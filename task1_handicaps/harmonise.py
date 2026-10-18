"""Harmonise the Link-Lives handicaps values: File A mapping and File B review subset.

Run: uv run python task1_handicaps/harmonise.py [--check]

Pools the `handicaps` column of the five census parquet files (1801, 1850, 1860,
1880, 1901), trivially normalises each value, clusters the content values by
fuzzy similarity (Phase 1 EDA method plus the D-17 digit guard) and writes:

- File A, task1_handicaps/outputs/handicaps_mapping.parquet (committed): one row
  per distinct trivially normalised value, value-level only, no records.
- File B, data/outputs/task1/handicaps_review.{parquet,csv} (local only, D-15):
  the highest-impact clusters for the historian, with empty decision/comment.

File B holds whole census records (D-15) and is only ever written inside the
gitignored data dir; the script refuses to write it anywhere else.

The script prints only paths, counts and FACT lines, never rows.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import polars as pl
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import project_paths as pp  # noqa: E402
from prepare_data import _tmp_path, write_atomic  # noqa: E402,F401

YEARS = pp.CENSUS_YEARS
REF_THRESHOLD = 85  # Phase 1 EDA value (D-03), unchanged by the D-17 digit guard

# Review capacity (D-12): one reviewer-day from the brief's 100-120 records/h x 2-3 h.
RECORDS_PER_HOUR = 120
HOURS_PER_DAY = 2.5
TOP_K = int(RECORDS_PER_HOUR * HOURS_PER_DAY)
RECORDS_PER_HOUR_RANGE = (100, 120)
HOURS_PER_DAY_RANGE = (2, 3)
EXAMPLES_PER_CLUSTER = 5  # D-14
SEED = 20261018  # D-14

TASK_DIR = Path(__file__).resolve().parent
MAPPING_PATH = TASK_DIR / "outputs" / "handicaps_mapping.parquet"
REVIEW_DIR = pp.OUTPUTS_DIR / "task1"
REVIEW_PATH = REVIEW_DIR / "handicaps_review.parquet"
REVIEW_CSV = REVIEW_DIR / "handicaps_review.csv"
RECORDS_PATH = REVIEW_DIR / "handicaps_review_records.parquet"
RECORDS_CSV = REVIEW_DIR / "handicaps_review_records.csv"
CSV_SEPARATOR = ";"  # Danish-locale Excel splits on semicolons; UTF-8 with BOM keeps æ, ø, å intact
CSV_BOM = b"\xef\xbb\xbf"
LOOKUP_PATH = TASK_DIR / "category_suggestions.parquet"
LEADERS_PATH = REVIEW_DIR / "review_leaders.parquet"

# Category vocabulary (D-09): the census's own historical terms plus explicit buckets.
CATEGORY_LABELS = [
    "døvstum/døv",
    "blind",
    "sindssyg",
    "uden forstandsevner/idiot",
    "krøbling/vanfør",
    "multiple conditions",
    "other/unclear",
    "not a condition (suspected misplaced)",
]
LOOKUP_COLUMNS = ["leader", "suggested_category", "category_source"]
CATEGORY_SOURCE = "llm_suggestion"

PREFIX = "task1.harmonise."

MAPPING_COLUMNS = [
    "value",
    "value_type",
    *[f"n_{y}" for y in YEARS],
    "n_total",
    "raw_variants_n",
    "raw_spellings",
    "cluster_id",
    "proposed_standard",
    "confidence",
    "in_review",
    "suggested_category",
    "category_source",
]


# --- helpers ported from the Phase 1 EDA (task1_handicaps/eda.ipynb) -------------


def filled(col: str) -> pl.Expr:
    return pl.col(col).is_not_null() & (pl.col(col).str.strip_chars() != "")


def trivial_norm(expr: pl.Expr) -> pl.Expr:
    return (
        expr.str.to_lowercase()
        .str.replace_all(r"[^\w\s]+", " ")
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
    )


def fact(key: str, value) -> None:
    if isinstance(value, float):
        value = round(value, 4)
    print(f"FACT {PREFIX}{key}={value}")


def digit_runs(s: str) -> tuple[str, ...]:
    """Maximal runs of the digits 0-9 in s, kept as strings (D-17)."""
    return tuple(re.findall(r"\d+", s))


def leader_clusters(
    values: list[str], threshold: int, digit_guard: bool = True
) -> tuple[dict[str, str], list[str]]:
    """Greedy leader clustering: each value joins the best leader at ratio >= threshold.

    D-17 digit guard: with digit_guard true, a value may only join a leader whose digit runs
    are identical to its own (candidates in leader-creation order); otherwise it becomes a
    new leader. fuzz.ratio treats digits like letters, so without the guard values stating a
    different age or duration merge. No parameter: exact equality of the digit runs.
    digit_guard=False is the unguarded Phase 1 method, kept for the counterfactual only.
    """
    leaders: list[str] = []
    by_digits: dict[tuple[str, ...], list[str]] = {}
    mapping: dict[str, str] = {}
    for v in values:
        candidates = by_digits.get(digit_runs(v), []) if digit_guard else leaders
        match = (
            process.extractOne(v, candidates, scorer=fuzz.ratio, score_cutoff=threshold)
            if candidates
            else None
        )
        if match is None:
            leaders.append(v)
            by_digits.setdefault(digit_runs(v), []).append(v)
            mapping[v] = v
        else:
            mapping[v] = match[0]
    return mapping, leaders


def cum_share(counts: list[int]) -> list[float]:
    s = pl.Series(counts, dtype=pl.Int64).sort(descending=True)
    return (s.cum_sum() / s.sum()).to_list() if s.len() else []


def coverage_at(curve: list[float], k: int) -> float:
    return curve[min(k, len(curve)) - 1] if curve else 0.0


def clusters_for(curve: list[float], target: float) -> int:
    for i, share in enumerate(curve, start=1):
        if share >= target:
            return i
    return len(curve)


# --- guards ----------------------------------------------------------------------


def require_inputs() -> None:
    """Exit with status 2, naming every missing census parquet."""
    missing = [pp.census_parquet(y) for y in YEARS if not pp.census_parquet(y).exists()]
    if not missing:
        return
    for p in missing:
        print(f"missing census parquet: {p}", file=sys.stderr)
    print("run: uv run python scripts/prepare_data.py", file=sys.stderr)
    sys.exit(2)


def inside_data_root(path: Path) -> bool:
    return path.resolve().is_relative_to(pp.DATA_ROOT.resolve())


def assert_local_only(path: Path) -> None:
    """Record-level outputs may only be written inside the gitignored data dir (D-15)."""
    if not inside_data_root(path):
        print(
            f"refusing to write record-level output outside the data dir: {path}",
            file=sys.stderr,
        )
        sys.exit(2)


# --- pipeline --------------------------------------------------------------------


def pooled_raw_counts() -> pl.DataFrame:
    """One row per (year, raw spelling) with its record count and trivial value."""
    frames = []
    for y in YEARS:
        frames.append(
            pl.scan_parquet(pp.census_parquet(y))
            .select(pl.col("handicaps").alias("raw"))
            .filter(filled("raw"))
            .group_by("raw")
            .len()
            .rename({"len": "n"})
            .with_columns(pl.col("n").cast(pl.Int64), pl.lit(y, dtype=pl.Int64).alias("year"))
            .collect()
        )
    return pl.concat(frames).with_columns(trivial_norm(pl.col("raw")).alias("value"))


def value_table(year_raw: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Per trivial value: per-year counts, raw spellings and value_type (D-01)."""
    raw_pooled = (
        year_raw.group_by("raw", "value")
        .agg(pl.col("n").sum())
        .sort(["n", "raw"], descending=[True, False])
    )
    spellings = raw_pooled.group_by("value", maintain_order=True).agg(
        pl.col("raw").alias("raw_spellings")
    )
    counts = year_raw.group_by("value").agg(
        *[
            pl.col("n").filter(pl.col("year") == y).sum().alias(f"n_{y}")
            for y in YEARS
        ],
        pl.col("n").sum().alias("n_total"),
    )
    values = (
        counts.join(spellings, on="value")
        .with_columns(
            pl.col("raw_spellings").list.len().cast(pl.Int64).alias("raw_variants_n"),
            pl.when(pl.col("value").str.contains(r"[^\W\d_]"))
            .then(pl.lit("content"))
            .otherwise(pl.lit("placeholder"))
            .alias("value_type"),
        )
    )
    return values, raw_pooled


def content_order(values: pl.DataFrame) -> list[str]:
    """Content values in the clustering visiting order: n_total descending, then value (D-03)."""
    content = values.filter(pl.col("value_type") == "content")
    return content.sort(["n_total", "value"], descending=[True, False])["value"].to_list()


def cluster_values(values: pl.DataFrame) -> pl.DataFrame:
    """Cluster content values (D-03..D-05, D-17); returns value, cluster_id, proposed_standard, confidence."""
    content = values.filter(pl.col("value_type") == "content")
    mapping, _ = leader_clusters(content_order(values), REF_THRESHOLD)
    assign = pl.DataFrame(
        {
            "value": list(mapping),
            "proposed_standard": list(mapping.values()),
            "confidence": [fuzz.ratio(v, ldr) / 100 for v, ldr in mapping.items()],
        }
    )
    ranks = (
        content.join(assign, on="value")
        .group_by("proposed_standard")
        .agg(pl.col("n_total").sum())
        .sort(["n_total", "proposed_standard"], descending=[True, False])
        .with_row_index("cluster_id", offset=1)
        .select(pl.col("cluster_id").cast(pl.Int64), "proposed_standard")
    )
    return assign.join(ranks, on="proposed_standard")


def report_coverage(values: pl.DataFrame, assigned: pl.DataFrame) -> pl.DataFrame:
    """Print the impact/size FACT lines (D-12); returns the cluster size table."""
    content = values.filter(pl.col("value_type") == "content")
    cluster_n = (
        content.join(assigned.select("value", "cluster_id"), on="value")
        .group_by("cluster_id")
        .agg(pl.col("n_total").sum())
        .sort("cluster_id")
    )
    curve = cum_share(cluster_n["n_total"].to_list())
    fact("clusters", cluster_n.height)
    for k in (100, 200, 300, 360):
        fact(f"coverage.top{k}", coverage_at(curve, k))
    for pct in (80, 90, 95):
        fact(f"clusters_for_coverage.{pct}", clusters_for(curve, pct / 100))
    fact("review.size", TOP_K)
    fact("review.size_low", RECORDS_PER_HOUR_RANGE[0] * HOURS_PER_DAY_RANGE[0])
    fact("review.size_high", RECORDS_PER_HOUR_RANGE[1] * HOURS_PER_DAY_RANGE[1])
    fact(
        "review.values",
        assigned.filter(pl.col("cluster_id") <= TOP_K).height,
    )
    return cluster_n


def report_digit_guard(values: pl.DataFrame) -> None:
    """Counterfactual FACT lines for the D-17 digit guard: what the unguarded method would do."""
    n_total = dict(zip(values["value"].to_list(), values["n_total"].to_list(), strict=True))
    mapping, leaders = leader_clusters(content_order(values), REF_THRESHOLD, digit_guard=False)
    moved = [v for v, ldr in mapping.items() if digit_runs(v) != digit_runs(ldr)]
    per_leader: dict[str, int] = {}
    for v, ldr in mapping.items():
        per_leader[ldr] = per_leader.get(ldr, 0) + n_total[v]
    curve = cum_share(list(per_leader.values()))
    fact("digit_guard.clusters_unguarded", len(leaders))
    fact("digit_guard.values_moved", len(moved))
    fact("digit_guard.records_moved", sum(n_total[v] for v in moved))
    fact(f"digit_guard.coverage.top{TOP_K}_unguarded", coverage_at(curve, TOP_K))


def review_leaders(values: pl.DataFrame, assigned: pl.DataFrame) -> pl.DataFrame:
    """Value-level worksheet, one row per review cluster: cluster_id, leader, n_total, merged_values."""
    return (
        values.join(assigned, on="value")
        .filter(pl.col("cluster_id") <= TOP_K)
        .sort(["cluster_id", "n_total", "value"], descending=[False, True, False])
        .group_by("cluster_id", maintain_order=True)
        .agg(
            pl.col("proposed_standard").first().alias("leader"),
            pl.col("n_total").sum(),
            pl.format("{} ({})", pl.col("value"), pl.col("n_total")).str.join(" | ").alias("merged_values"),
        )
        .select("cluster_id", "leader", "n_total", "merged_values")
        .sort("cluster_id")
    )


def load_lookup(path: Path, leaders: list[str]) -> pl.DataFrame:
    """Validate the category lookup and return it restricted to review leaders (HARM-03, D-08, D-10).

    Called before any output is written, so a bad lookup leaves previous outputs untouched.
    """
    if not path.exists():
        print(
            f"missing category lookup: {path} (run --write-leaders, see task1_handicaps/README.md)",
            file=sys.stderr,
        )
        sys.exit(2)
    lookup = pl.read_parquet(path)
    if lookup.columns != LOOKUP_COLUMNS:
        print(f"category lookup columns {lookup.columns} != {LOOKUP_COLUMNS}", file=sys.stderr)
        sys.exit(2)
    bad = lookup.filter(~pl.col("suggested_category").is_in(CATEGORY_LABELS)).height
    if bad:
        print(f"category lookup has {bad} rows with a label outside CATEGORY_LABELS", file=sys.stderr)
        sys.exit(2)
    if lookup.filter(pl.col("category_source") != CATEGORY_SOURCE).height:
        print(f"category lookup category_source must be {CATEGORY_SOURCE!r} in every row", file=sys.stderr)
        sys.exit(2)
    have = set(lookup["leader"].to_list())
    missing = [ldr for ldr in leaders if ldr not in have]
    if missing:
        print(
            f"missing category suggestions for {len(missing)} review leaders (run --write-leaders)",
            file=sys.stderr,
        )
        sys.exit(2)
    fact("lookup.missing", len(missing))
    fact("lookup.unused", len(have - set(leaders)))
    return lookup.filter(pl.col("leader").is_in(leaders)).unique(subset="leader")


def build_mapping(values: pl.DataFrame, assigned: pl.DataFrame, lookup: pl.DataFrame) -> pl.DataFrame:
    """File A (HARM-02, HARM-03): one row per trivial value, value-level only."""
    return (
        values.join(assigned, on="value", how="left")
        .join(lookup.rename({"leader": "proposed_standard"}), on="proposed_standard", how="left")
        .with_columns(
            (pl.col("cluster_id").is_not_null() & (pl.col("cluster_id") <= TOP_K)).alias("in_review"),
        )
        .select(MAPPING_COLUMNS)
        .sort(
            ["cluster_id", "n_total", "value"],
            descending=[False, True, False],
            nulls_last=True,
        )
    )


def sample_records(clusters: pl.DataFrame) -> pl.DataFrame:
    """File B example records (D-13, D-14): up to EXAMPLES_PER_CLUSTER whole records per review cluster.

    `clusters` holds value, cluster_id, proposed_standard for review-cluster content values.
    Records are drawn uniformly at random with the fixed SEED, with no judgement about which
    are typical. Whole census records: the output must stay inside the gitignored data dir.
    """
    parts = []
    for y in YEARS:
        parts.append(
            pl.scan_parquet(pp.census_parquet(y))
            .filter(filled("handicaps"))
            .with_columns(trivial_norm(pl.col("handicaps")).alias("_value"))
            .join(clusters.lazy(), left_on="_value", right_on="value", how="inner")
            .with_columns(pl.lit(y, dtype=pl.Int64).alias("year"))
            .drop("_value")
            .collect()
        )
    records = pl.concat(parts, how="diagonal_relaxed")
    lead = ["cluster_id", "proposed_standard", "year", "pa_id", "handicaps"]
    ordered = lead + [c for c in records.columns if c not in lead]
    return (
        records.select(ordered)
        .sort(["cluster_id", "year", "pa_id"])
        .filter(pl.int_range(pl.len()).shuffle(seed=SEED).over("cluster_id") < EXAMPLES_PER_CLUSTER)
        .sort(["cluster_id", "year", "pa_id"])
    )


def build_review(
    mapping: pl.DataFrame, raw_pooled: pl.DataFrame, records: pl.DataFrame
) -> pl.DataFrame:
    """File B review table (HARM-04, D-13): one row per review cluster."""
    examples = records.group_by("cluster_id").agg(pl.len().cast(pl.Int64).alias("examples_n"))
    in_review = mapping.filter(pl.col("in_review"))
    stats = in_review.group_by("cluster_id").agg(
        pl.col("proposed_standard").first(),
        pl.col("n_total").sum(),
        *[pl.col(f"n_{y}").sum() for y in YEARS],
        pl.len().cast(pl.Int64).alias("merged_values_n"),
        pl.col("confidence").mean().round(4).alias("confidence_mean"),
        pl.col("confidence").min().alias("confidence_min"),
        pl.col("suggested_category").first(),
        pl.col("category_source").first(),
    )
    spell = (
        raw_pooled.join(in_review.select("value", "cluster_id"), on="value")
        .sort(["cluster_id", "n", "raw"], descending=[False, True, False])
        .group_by("cluster_id", maintain_order=True)
        .agg(
            pl.len().cast(pl.Int64).alias("merged_spellings_n"),
            pl.format("{} ({})", pl.col("raw"), pl.col("n")).str.join(" | ").alias("merged_spellings"),
        )
    )
    return (
        stats.join(spell, on="cluster_id")
        .join(examples, on="cluster_id", how="left")
        .with_columns(pl.col("examples_n").fill_null(0))
        .with_columns(
            pl.lit("").alias("decision"),
            pl.lit("").alias("comment"),
        )
        .select(
            "cluster_id",
            "proposed_standard",
            "n_total",
            *[f"n_{y}" for y in YEARS],
            "merged_values_n",
            "merged_spellings_n",
            "merged_spellings",
            "confidence_mean",
            "confidence_min",
            "examples_n",
            "suggested_category",
            "category_source",
            "decision",
            "comment",
        )
        .sort("cluster_id")
    )


def write_csv_bom(frame: pl.DataFrame, target: Path) -> None:
    """Write a semicolon-separated UTF-8 CSV with BOM via temp file and rename (HARM-04)."""
    assert_local_only(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_path(target)
    try:
        tmp.write_bytes(CSV_BOM + frame.write_csv(separator=CSV_SEPARATOR).encode("utf-8"))
        tmp.replace(target)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def write_outputs(mapping: pl.DataFrame, review: pl.DataFrame, records: pl.DataFrame) -> None:
    write_atomic(mapping, MAPPING_PATH)
    print(f"wrote {MAPPING_PATH} rows={mapping.height}")
    for frame, parquet_path, csv_path in (
        (review, REVIEW_PATH, REVIEW_CSV),
        (records, RECORDS_PATH, RECORDS_CSV),
    ):
        assert_local_only(parquet_path)
        write_atomic(frame, parquet_path)
        print(f"wrote {parquet_path} rows={frame.height}")
        write_csv_bom(frame, csv_path)
        print(f"wrote {csv_path} rows={frame.height}")


# --- check -----------------------------------------------------------------------


def check_lookup(path: Path, report, review: pl.DataFrame) -> None:
    if not path.exists():
        report(False, "lookup_exists", str(path))
        return
    lk = pl.read_parquet(path)
    report(lk.columns == LOOKUP_COLUMNS, "lookup_columns", f"cols={lk.width}")
    report(lk["suggested_category"].is_in(CATEGORY_LABELS).all(), "lookup_labels_in_vocabulary")
    report(lk["category_source"].eq(CATEGORY_SOURCE).all(), "lookup_category_source")
    covered = set(lk["leader"].to_list())
    missing = [ldr for ldr in review["proposed_standard"].to_list() if ldr not in covered]
    report(not missing, "lookup_covers_review_leaders", f"missing={len(missing)}")


def check_outputs(lookup_path: Path) -> int:
    failed = 0

    def report(ok: bool, name: str, detail: str = "") -> None:
        nonlocal failed
        failed += 0 if ok else 1
        print(f"{'OK' if ok else 'FAIL'} {name} {detail}".rstrip())

    for p in (MAPPING_PATH, REVIEW_PATH, REVIEW_CSV, RECORDS_PATH, RECORDS_CSV):
        if not p.exists():
            report(False, p.name, "missing (run the script first)")
    if failed:
        return 1

    a = pl.read_parquet(MAPPING_PATH)
    report(a.columns == MAPPING_COLUMNS, "mapping_columns", f"cols={a.width}")
    report("pa_id" not in a.columns, "mapping_no_pa_id")
    report(
        set(a["value_type"].unique().to_list()) <= {"placeholder", "content"},
        "value_type_values",
    )
    ph = a.filter(pl.col("value_type") == "placeholder")
    report(
        ph["cluster_id"].null_count() == ph.height
        and ph["proposed_standard"].null_count() == ph.height
        and ph["confidence"].null_count() == ph.height
        and not ph["in_review"].any(),
        "placeholder_rows_unclustered",
        f"n={ph.height}",
    )
    ct = a.filter(pl.col("value_type") == "content")
    report(
        ct["confidence"].min() >= REF_THRESHOLD / 100 - 1e-9 and ct["confidence"].max() <= 1.0,
        "content_confidence_range",
    )
    report(
        ct.filter(pl.col("value") == pl.col("proposed_standard"))["confidence"].eq(1.0).all(),
        "leader_confidence_one",
    )
    report(
        a.select(
            (pl.col("n_total") == pl.sum_horizontal([f"n_{y}" for y in YEARS])).all()
        ).item(),
        "n_total_is_year_sum",
    )
    digit_violations = sum(
        digit_runs(v) != digit_runs(ldr)
        for v, ldr in zip(ct["value"].to_list(), ct["proposed_standard"].to_list(), strict=True)
    )
    report(digit_violations == 0, "digit_runs_match_leader", f"violations={digit_violations}")

    r = pl.read_parquet(REVIEW_PATH)
    n_clusters = ct["cluster_id"].n_unique()
    expected = min(TOP_K, n_clusters)
    report(r.height == expected, "review_rows", f"rows={r.height} expected={expected}")
    report(
        r["cluster_id"].to_list() == list(range(1, r.height + 1)),
        "review_cluster_ids_1_to_n",
    )
    report(
        r["decision"].eq("").all() and r["comment"].eq("").all(),
        "review_decision_comment_empty",
    )
    report(inside_data_root(REVIEW_PATH), "review_inside_data_root")

    report(
        a.select(
            (pl.col("suggested_category").is_not_null() == pl.col("in_review")).all()
        ).item(),
        "suggestion_iff_in_review",
    )
    report(
        a.filter(
            pl.col("category_source").is_not_null() & (pl.col("category_source") != CATEGORY_SOURCE)
        ).is_empty(),
        "category_source_llm_or_null",
    )
    report(r["suggested_category"].null_count() == 0, "review_suggestions_complete")
    check_lookup(lookup_path, report, r)

    rec = pl.read_parquet(RECORDS_PATH)
    report(
        rec.columns[:5] == ["cluster_id", "proposed_standard", "year", "pa_id", "handicaps"],
        "records_columns",
        f"cols={rec.width}",
    )
    # pa_id identifies a record within one census year; a pa_id string can recur across years.
    report(
        rec.select(["year", "pa_id"]).unique().height == rec.height,
        "records_year_pa_id_unique",
        f"rows={rec.height} pa_id_repeated_across_years={rec.height - rec['pa_id'].n_unique()}",
    )
    report(set(rec["cluster_id"].to_list()) <= set(r["cluster_id"].to_list()), "records_clusters_are_review")
    per_cluster = rec.group_by("cluster_id").agg(pl.len().cast(pl.Int64).alias("k"))
    cmp = r.select("cluster_id", "n_total", "examples_n").join(per_cluster, on="cluster_id", how="left")
    report(
        cmp.select(
            (pl.col("k").fill_null(0) == pl.min_horizontal(pl.col("n_total"), pl.lit(EXAMPLES_PER_CLUSTER)))
            & (pl.col("k").fill_null(0) == pl.col("examples_n"))
        )
        .to_series()
        .all(),
        "records_per_cluster_is_min_5_n_total",
    )
    for p in (REVIEW_CSV, RECORDS_CSV):
        with p.open("rb") as fh:
            report(fh.read(3) == CSV_BOM, f"{p.name}_bom")
    report(
        all(inside_data_root(p) for p in (RECORDS_PATH, REVIEW_CSV, RECORDS_CSV)),
        "file_b_inside_data_root",
    )
    return 1 if failed else 0


# --- main ------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate outputs, write nothing")
    parser.add_argument(
        "--write-leaders",
        action="store_true",
        help="write the review-leader worksheet (local only) used to author the category lookup",
    )
    parser.add_argument(
        "--lookup", type=Path, default=LOOKUP_PATH, help="category suggestion lookup parquet"
    )
    args = parser.parse_args()
    if args.check:
        return check_outputs(args.lookup)

    require_inputs()
    year_raw = pooled_raw_counts()
    fact("records.filled", int(year_raw["n"].sum()))
    fact("values.raw", year_raw["raw"].n_unique())
    values, raw_pooled = value_table(year_raw)
    placeholder = values.filter(pl.col("value_type") == "placeholder")
    fact("records.placeholder", int(placeholder["n_total"].sum()))
    fact("records.content", int(values.filter(pl.col("value_type") == "content")["n_total"].sum()))
    fact("values.trivial", values.height)
    fact("values.placeholder", placeholder.height)
    fact("values.content", values.height - placeholder.height)

    assigned = cluster_values(values)
    report_coverage(values, assigned)
    report_digit_guard(values)
    leaders = review_leaders(values, assigned)
    if args.write_leaders:
        assert_local_only(LEADERS_PATH)
        write_atomic(leaders, LEADERS_PATH)
        print(f"wrote {LEADERS_PATH} rows={leaders.height}")
        return 0

    lookup = load_lookup(args.lookup, leaders["leader"].to_list())
    mapping = build_mapping(values, assigned, lookup)
    content_records = int(values.filter(pl.col("value_type") == "content")["n_total"].sum())
    with_suggestion = mapping.filter(pl.col("suggested_category").is_not_null())
    fact("category.labels_used", with_suggestion["suggested_category"].n_unique())
    fact("category.values", with_suggestion.height)
    fact("category.record_share", int(with_suggestion["n_total"].sum()) / content_records)
    review_values = assigned.filter(pl.col("cluster_id") <= TOP_K).select(
        "value", "cluster_id", "proposed_standard"
    )
    records = sample_records(review_values)
    review = build_review(mapping, raw_pooled, records)
    fact("examples.records", records.height)
    fact("examples.clusters_lt5", review.filter(pl.col("n_total") < EXAMPLES_PER_CLUSTER).height)
    write_outputs(mapping, review, records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
