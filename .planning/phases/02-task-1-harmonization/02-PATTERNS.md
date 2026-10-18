# Phase 2: Task 1 - Harmonization - Pattern Map

**Mapped:** 2026-10-18
**Files analyzed:** 7
**Analogs found:** 5 / 7 (all analogs are git-tracked; verified with `git ls-files`)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `task1_handicaps/harmonise.py` | script (CLI) | batch / transform + file-I/O | `scripts/prepare_data.py` (layout) + `task1_handicaps/eda.ipynb` cells 1, 27, 34, 39 (logic) | role + logic match |
| `task1_handicaps/category_suggestions.parquet` | data lookup (committed) | file-I/O | none (written once by executor with polars; use `write_atomic` pattern) | none |
| `task1_handicaps/outputs/handicaps_mapping.parquet` (File A) | output | batch | `write_atomic` in `scripts/prepare_data.py` | partial |
| `data/outputs/task1/handicaps_review{,_records}.parquet` + `.csv` (File B) | output (local only) | batch | same as above; paths via `project_paths.DATA_ROOT` | partial |
| `task1_handicaps/README.md` | doc | n/a | root `README.md` (section style) | partial |
| `.planning/PROJECT.md` Key Decisions | doc | n/a | existing table in the file | exact |
| `scripts/project_paths.py` (optional: add `OUTPUTS_DIR`) | config | n/a | itself | exact |

## Pattern Assignments

### `task1_handicaps/harmonise.py` (script, batch)

**CLI layout analog:** `scripts/prepare_data.py`. Module docstring (first line used as the argparse description), `from __future__ import annotations`, stdlib imports, then `polars`, then `import project_paths`.

Note that `prepare_data.py` does `import project_paths` bare, which works because `scripts/` is `sys.path[0]` when it is run. A script in `task1_handicaps/` must add `scripts/` to the path, as the notebook does (cell 1):
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import project_paths as pp
```

**Main/exit-code pattern** (prepare_data.py 197-218):
```python
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate outputs, write nothing")
    args = parser.parse_args()
    if args.check:
        return check_outputs(args.only)
    ...
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Missing-input exit 2** (prepare_data.py 32-43):
```python
def require_sources(paths: list[Path]) -> None:
    missing = [p for p in paths if not p.exists()]
    if not missing:
        return
    for p in missing:
        print(f"missing source file: {p}", file=sys.stderr)
    print('see README.md, section "Data (not in git)", ...', file=sys.stderr)
    sys.exit(2)
```
Call it with `[pp.census_parquet(y) for y in pp.CENSUS_YEARS]`.

**Atomic write** (prepare_data.py 46-63): copy `_tmp_path` and `write_atomic` verbatim for every parquet output. It already does `mkdir(parents=True)`. For the CSV, write with a pid-tmp file and `replace` in the same way. Use `encoding="utf-8-sig"` for the BOM. Polars `write_csv` has no BOM option, so write the bytes by hand: `b"\xef\xbb\xbf" + df.write_csv().encode()`.

**Governance print rule** (prepare_data.py docstring): "prints only paths, counts and dtypes, never rows". Keep this. The script must not print raw handicaps values or records.

**Filled / trivial_norm / fact helpers** (eda.ipynb cell 1; port verbatim):
```python
def filled(col):
    return pl.col(col).is_not_null() & (pl.col(col).str.strip_chars() != "")

def trivial_norm(expr):
    return (
        expr.str.to_lowercase()
        .str.replace_all(r"[^\w\s]+", " ")
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
    )

def fact(key, value):
    if isinstance(value, float):
        value = round(value, 4)
    FACTS[key] = value
    print(f"FACT {key}={value}")

def safe_div(a, b):
    return a / b if b else 0.0
```

**Pooled counts per year** (cell 27; port, keep the per-year `n` for File A year columns):
```python
YEAR_RAW = pl.concat([
    LF[y].select(pl.col("handicaps").alias("raw")).filter(filled("raw"))
    .group_by("raw").len().rename({"len": "n"})
    .with_columns(pl.lit(y).alias("year")).collect()
    for y in YEARS
]).with_columns(trivial_norm(pl.col("raw")).alias("norm"))
NORM = (YEAR_RAW.group_by("norm")
    .agg(pl.col("n").sum().alias("n"), pl.col("year").n_unique().alias("years_n"),
         pl.col("raw").n_unique().alias("raw_variants_n"))
    .sort(["n", "norm"], descending=[True, False]))   # visit order = descending pooled count, ties by string
```
Phase 2 additions:
- Placeholder rule (D-01): `~pl.col("norm").str.contains(r"[^\W\d_]")`. Note that `\w` includes digits and `_`, so use a letters-only class. Check that the result matches the measured 33,210 real-content records.
- Pivot per-year counts: `YEAR_RAW.pivot(on="year", index="norm", values="n")`, or group_by + `pl.when(year==y)` sums.
- The "norm" for placeholders may be an empty string (for example `-` becomes ""). Group on it as is.

**Greedy leader clustering** (cell 27; verbatim, D-03). Run it on non-placeholder norms only:
```python
def leader_clusters(values, threshold):
    leaders, mapping = [], {}
    for v in values:
        match = process.extractOne(v, leaders, scorer=fuzz.ratio, score_cutoff=threshold) if leaders else None
        if match is None:
            leaders.append(v); mapping[v] = v
        else:
            mapping[v] = match[0]
    return mapping, leaders
```
Imports: `from rapidfuzz import fuzz, process`. `REF_THRESHOLD = 85`. Do not add new tuning constants beyond `TOP_K=300` and `SEED`.

**Cluster table** (cell 34):
```python
MAP85, LEADERS85 = CLUSTERS[REF_THRESHOLD]
NORM85 = NORM.with_columns(pl.col("norm").replace_strict(MAP85).alias("leader"))
CLUSTER85 = NORM85.group_by("leader").agg(pl.col("n").sum().alias("n")).sort(["n", "leader"], descending=[True, False])
```
Confidence (D-05): `fuzz.ratio(norm, leader)/100`, via `map_elements` or a Python list comprehension. About 3.3k values, so this is cheap.

**Coverage numbers** (cell 39; print them, do not hard-code them, D-12):
```python
def cum_share(counts):
    s = pl.Series(counts).sort(descending=True)
    return (s.cum_sum() / s.sum()).to_list() if s.len() else []

def coverage_at(curve, k):
    return curve[min(k, len(curve)) - 1] if curve else 0.0
```
Use `fact("task1.coverage.top300", ...)`. Also print the k at which 95% is reached.

**Example records for File B** (new; no analog). Pattern:
- Lazy-scan each census year.
- Compute `trivial_norm(handicaps)`, map to `cluster_id` with `replace_strict`, and filter to the top-300 clusters.
- Concat across years with `year` as a column. The schemas are probably not identical across years, so use `pl.concat(..., how="diagonal_relaxed")`. Verify this.
- Sample up to 5 per cluster with a fixed seed: add `pl.int_range(pl.len()).shuffle(seed=SEED).over("cluster_id")`, then keep rows where it is below 5, or use `group_by(...).map_groups(lambda g: g.sample(n=min(5, g.height), seed=SEED))`. Sorting first by `["year","pa_id"]` makes the result deterministic.
- Only collect the sampled rows. Use `pa_id` as the join key if a two-pass approach (select `pa_id` first, then fetch full rows) is wanted.
- All columns stay as String (Phase 1 D-06). Cast explicitly if numbers are needed.

**Category lookup join** (D-08, D-10): `pl.read_parquet("task1_handicaps/category_suggestions.parquet")` on `leader`. Columns: `leader`, `suggested_category`, `category_source="llm_suggestion"`. The join is left, so non-top-300 clusters stay null. Make the script fail with exit 2 if a top-300 leader is missing from the lookup. A `--check` flag in the style of `prepare_data.py` can report this.

**Existing-FACT pattern for docs:** every number quoted in the README should be a `FACT task1.harmonise.*` line printed by the script.

---

### `task1_handicaps/category_suggestions.parquet`
No code analog. Generate the top-300 leader list by running the script (a `--dump-leaders` mode that writes the leaders to the scratchpad, or prints them for the executor). The executor then writes the lookup with polars `write_parquet`. Columns: `leader`, `suggested_category`, `category_source`. Verify that it is tracked (see Gitignore below).

### `task1_handicaps/outputs/handicaps_mapping.parquet` (File A)
Value-level only: one row per trivial value. Suggested columns: `value`, `value_type`, `n_1801..n_1901` (or `n_<year>`), `n_total`, `cluster_id`, `proposed_standard`, `confidence`, `suggested_category`, `suggestion_note`. Write it via `write_atomic`. Do not include raw spellings that look like names. The values are handicap terms, but still apply the Phase 1 rule that committed outputs hold aggregates only.

### `data/outputs/task1/*` (File B)
Add `OUTPUTS_DIR = DATA_ROOT / "outputs"` to `scripts/project_paths.py`, next to `PARQUET_DIR = DATA_ROOT / "parquet"` (line 51). Optionally add `"outputs"` to `_CLI_DIRS`. This keeps the path resolution worktree-safe (the main checkout's `data/`).

### `.planning/PROJECT.md`
Append rows to the existing Key Decisions table, following its format (read the file when editing).

---

## Shared Patterns

### Atomic parquet write
**Source:** `scripts/prepare_data.py` lines 46-63. Apply to all five output files.

### Data governance
- Never print rows.
- Record-level outputs only under `data/` (D-15).
- Committed outputs hold value-level counts only.

### Gitignore and pre-commit: exact current rules
`.gitignore`:
```
data/
*.xlsx
*.zip
*.csv
*.pdf
.claude/*
!.claude/CLAUDE.md
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
```
`.githooks/pre-commit` blocks staged paths matching `data/*|*.xlsx|*.zip|*.pdf`. It also scans staged `.ipynb` files with `check_notebook_outputs.py`.

**Finding:** `*.parquet` is NOT blocked, either by `.gitignore` or by the hook. Only `data/` blocks the parquet files, so `task1_handicaps/category_suggestions.parquet` and `task1_handicaps/outputs/handicaps_mapping.parquet` can be committed with no new allow rule. `*.csv` IS ignored globally. That is harmless here, because the CSVs belong under `data/outputs/` anyway. Do not commit a CSV of File A. If one is wanted, it needs `git add -f` or a `!task1_handicaps/outputs/*.csv` rule. Recommendation: skip it, since parquet is the project format.

**Risk to flag:** the hook does not look at parquet content. Nothing prevents someone from placing a record-level parquet under `task1_handicaps/`. Keep File B strictly under `data/outputs/`. Optionally add a script assertion that the File B path is inside `pp.DATA_ROOT`.

## No Analog Found

| File | Reason |
|---|---|
| `task1_handicaps/category_suggestions.parquet` | Hand/LLM-authored lookup; no existing lookup files |
| Example-record sampling (File B records) | No existing per-group sampling; use the polars pattern above |
| CSV writer with BOM | New |

## Metadata
**Analog search scope:** `scripts/`, `task1_handicaps/`, `.githooks/`, `.gitignore`, `README.md`.
**Files scanned:** 8 (tracked files listed by `git ls-files`; notebook cells 1, 3, 7, 21, 23, 27, 34, 39, 43 read).
**Pattern extraction date:** 2026-10-18
