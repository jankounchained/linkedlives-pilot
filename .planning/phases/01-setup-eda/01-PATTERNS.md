# Phase 1: Setup & EDA - Pattern Map

**Mapped:** 2026-10-18
**Files analyzed:** 8
**Analogs found:** 0 / 8 (greenfield; `git ls-files` shows only `.planning/`, `.gitignore`, `.claude/CLAUDE.md`)

`.claude/` GSD tooling is JavaScript and not a valid analog. No data files were read.

## File Classification

| New File | Role | Data Flow | Analog |
|---|---|---|---|
| `pyproject.toml` (+ `uv.lock`, `.python-version` if pinned) | config | n/a | none, greenfield |
| `scripts/prepare_data.py` (root level, name free) | utility / batch | file-I/O, batch | none, greenfield |
| `task1_handicaps/eda.ipynb` | notebook | transform, aggregate | none, greenfield |
| `task2_linking/eda.ipynb` | notebook | transform, aggregate | none, greenfield |
| `README.md` (root: data sources, how to run) | docs | n/a | none |
| `.gitignore` | config | n/a | existing; already covers `data/`, `*.xlsx`, `*.zip`, `*.csv`, `*.pdf`, `.venv/`, `.ipynb_checkpoints/`. Likely no change. |
| `task1_handicaps/README.md`, `task2_linking/README.md` | docs | n/a | none (stubs; filled in later phases) |

## Conventions to apply (fixed by CONTEXT.md and CLAUDE.md, not by code)

### Environment
- `uv` project: `uv init`, `uv add polars pyarrow rapidfuzz fastexcel ipykernel nbconvert matplotlib` (plus `jupyter` or `nbclient` for executing the notebooks). Run scripts with `uv run`.
- System Python is 3.14. Check wheels for each dep, and if one is missing, set `requires-python` or a uv-managed Python (CONTEXT code_context).

### Paths (later phases depend on these)
- Raw input: `data/raw/linking_lab/{MF_census_1850_1846_cl.xlsx, Linking_Lab_opgave.zip, *.pdf}` and `data/raw/digidata_14001/14001.zip` (D-04, D-05).
- Output: `data/parquet/census_<year>.parquet` for 1801, 1850, 1860, 1880, 1901, plus one DWI parquet, e.g. `data/parquet/dwi_1846_1850.parquet`.

### prepare_data.py skeleton (D-04, D-06, D-07)
- Use `pathlib` constants for the paths above.
- Missing-file check first, exit with a clear message that names the file and points to the README.
- Extract only the 5 `Data/CSV/main_datasets/census_{year}__v1__cl.csv` members plus the Guide PDF (`Dokumenter/`) with `zipfile` into a temp dir. Never unpack the full ~10.6 GB.
- Convert each CSV with `pl.scan_csv(path, infer_schema=False)` then `.sink_parquet(out)`. `infer_schema=False` gives all-Utf8 columns, so nothing is coerced.
- Read the xlsx with `pl.read_excel(path, sheet_name="MF_census_1850_1846_cl", infer_schema_length=0)` (fastexcel engine) and cast to Utf8 if needed. Keep the leftover `Column1` as is.
- Idempotent: skip or overwrite existing parquet, delete the temp dir after the run.
- Never print rows.

### Notebooks (D-01, D-02)
- First cell: `import polars as pl`, then `pl.scan_parquet("../data/parquet/...")`. Use lazy scans for the census files.
- Cast explicitly (`pl.col("age").cast(pl.Int32, strict=False)`) and report null counts after the cast as a finding (D-06).
- Only allowed outputs are frequency tables (`group_by().len().sort().head(n)`), summary stats and plots. No `.head()` of raw frames, no `pa_id` rows, no name/age/owner rows.
- State the chosen rapidfuzz scorer and threshold (for example `rapidfuzz.process.cdist` or `fuzz.token_sort_ratio`) in a markdown cell.
- End each notebook with a "Facts for open decisions" section.
- Execute with `uv run jupyter nbconvert --to notebook --execute --inplace <nb>`, then scan the cell outputs for record-level content before `git add` (the one-way door in D-02).

### Task 1 notebook (D-12..D-14)
- Three-level distinct counts: raw, then `str.to_lowercase().str.replace_all(r"[^\w]+", "")`, then rapidfuzz clusters.
- Fill rate per year, and per geographic unit (pick the column from the Guide).
- Coverage curve: sort normalised values by frequency, `cum_sum() / total`, with vlines at 200, 300 and 360. Print the coverage at each.

### Task 2 notebook (D-08..D-11)
- Name normalisation: lowercase, `unicodedata` NFKD accent stripping, drop punctuation, collapse whitespace. Anchor key is sex + given + surname, unique in both censuses.
- Plot the `age_1850 - age_1846` distribution on the anchors. Print the lower-bound caveat next to it.
- Window table: for each of ±1, ±2, ±3, ±5, the candidate-pair count (join on sex + birth-year window, counted via aggregation, not materialised) and the share of anchors kept.
- Household profile: group by `FS_HOUSEHOLD_ID`, with size distribution per census and island, and the singleton share.

## No Analog Found

All files above. The planner should rely on the conventions listed here and in `01-CONTEXT.md`. There is no RESEARCH.md for this phase, so the polars API calls (`infer_schema=False`, `sink_parquet`, `read_excel`) should be verified against the installed polars version when the executor runs.

## Metadata

**Analog search scope:** `git ls-files` (the whole tracked repo)
**Files scanned:** 9 tracked files, plus `01-CONTEXT.md` read in full
