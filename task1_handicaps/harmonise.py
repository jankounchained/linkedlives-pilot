"""Harmonise the Link-Lives handicaps values: File A mapping and File B review subset.

Run: uv run python task1_handicaps/harmonise.py [--check]

Pools the `handicaps` column of the five census parquet files (1801, 1850, 1860,
1880, 1901), trivially normalises each value, clusters the content values by
fuzzy similarity (Phase 1 EDA method, unchanged) and writes:

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
import sys
from pathlib import Path

import polars as pl
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import project_paths as pp  # noqa: E402
from prepare_data import _tmp_path, write_atomic  # noqa: E402,F401

YEARS = pp.CENSUS_YEARS
REF_THRESHOLD = 85  # Phase 1 EDA value (D-03)

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


def leader_clusters(values: list[str], threshold: int) -> tuple[dict[str, str], list[str]]:
    """Greedy leader clustering: each value joins the best leader at ratio >= threshold."""
    leaders: list[str] = []
    mapping: dict[str, str] = {}
    for v in values:
        match = (
            process.extractOne(v, leaders, scorer=fuzz.ratio, score_cutoff=threshold)
            if leaders
            else None
        )
        if match is None:
            leaders.append(v)
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


def cluster_values(values: pl.DataFrame) -> pl.DataFrame:
    """Cluster content values (D-03..D-05); returns value, cluster_id, proposed_standard, confidence."""
    content = values.filter(pl.col("value_type") == "content")
    order = content.sort(["n_total", "value"], descending=[True, False])["value"].to_list()
    mapping, _ = leader_clusters(order, REF_THRESHOLD)
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


def build_mapping(values: pl.DataFrame, assigned: pl.DataFrame) -> pl.DataFrame:
    """File A (HARM-02): one row per trivial value, value-level only."""
    return (
        values.join(assigned, on="value", how="left")
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


def build_review(mapping: pl.DataFrame, raw_pooled: pl.DataFrame) -> pl.DataFrame:
    """File B review table (HARM-04, D-13): one row per review cluster."""
    in_review = mapping.filter(pl.col("in_review"))
    stats = in_review.group_by("cluster_id").agg(
        pl.col("proposed_standard").first(),
        pl.col("n_total").sum(),
        *[pl.col(f"n_{y}").sum() for y in YEARS],
        pl.len().cast(pl.Int64).alias("merged_values_n"),
        pl.col("confidence").mean().round(4).alias("confidence_mean"),
        pl.col("confidence").min().alias("confidence_min"),
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
            "decision",
            "comment",
        )
        .sort("cluster_id")
    )


def write_outputs(mapping: pl.DataFrame, review: pl.DataFrame) -> None:
    write_atomic(mapping, MAPPING_PATH)
    print(f"wrote {MAPPING_PATH} rows={mapping.height}")
    assert_local_only(REVIEW_PATH)
    write_atomic(review, REVIEW_PATH)
    print(f"wrote {REVIEW_PATH} rows={review.height}")


# --- check -----------------------------------------------------------------------


def check_outputs() -> int:
    failed = 0

    def report(ok: bool, name: str, detail: str = "") -> None:
        nonlocal failed
        failed += 0 if ok else 1
        print(f"{'OK' if ok else 'FAIL'} {name} {detail}".rstrip())

    for p in (MAPPING_PATH, REVIEW_PATH):
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
    return 1 if failed else 0


# --- main ------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate outputs, write nothing")
    args = parser.parse_args()
    if args.check:
        return check_outputs()

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
    mapping = build_mapping(values, assigned)
    review = build_review(mapping, raw_pooled)
    write_outputs(mapping, review)
    return 0


if __name__ == "__main__":
    sys.exit(main())
