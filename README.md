# Linking Lab pre-interview tasks

Task 1: explore and prepare the `handicaps` census variable for standardisation.
Task 2: design and implement a simple method to link the 1846 and 1850 Danish West Indies censuses.

(Phase 4 completes this README. Currently: setup, data sources and the prepare step.)

## Setup

```bash
uv sync
```

The project pins Python 3.14 (`.python-version`) and exact dependency versions
(`pyproject.toml` + `uv.lock`). If the machine has no Python 3.14, uv downloads a
uv-managed one. Run everything with `uv run`.

## Data (not in git)

Raw data and converted data never enter git, not even this private repo (the licence
may not allow it). Everything lives under `data/`, which is gitignored.

| What | Where it comes from | Where it goes |
|---|---|---|
| Link-Lives Release 2 (census files 1801 to 1901 and the Release 2 Guide) | Rigsarkivet Digidata dataset 14001, saved as `14001.zip` | `data/raw/digidata_14001/14001.zip` |
| `MF_census_1850_1846_cl.xlsx` (Danish West Indies 1846 and 1850) | Emailed by Linking Lab. FamilySearch partner data, must not be redistributed | `data/raw/linking_lab/MF_census_1850_1846_cl.xlsx` |
| `Linking_Lab_opgave.zip`, `Linking_Lab_brief.pdf`, `Pre_interview_tasks_for_data_scientists_datamanagers_2026.pdf` | Emailed by Linking Lab | `data/raw/linking_lab/` |

The prepare script does not download anything. If a file is missing it exits with
status 2, names the missing path and points back to this section.

By default the data directory is the one in the main git checkout (so git worktrees
share it). Set `LINKING_LAB_DATA=/absolute/path/to/data` to override. The resolved
paths are defined once in `scripts/project_paths.py`
(`uv run python scripts/project_paths.py parquet` prints the parquet directory).

## Prepare data

```bash
uv run python scripts/prepare_data.py            # convert everything
uv run python scripts/prepare_data.py --only dwi # convert one source
uv run python scripts/prepare_data.py --check    # validate outputs, write nothing
```

Outputs are all-String parquet files (nothing is coerced; later scripts cast
explicitly and report parse failures) under `data/parquet/`:

- `dwi_1846_1850.parquet` (83,414 rows, 22 columns, from the xlsx sheet `MF_census_1850_1846_cl`)
- `census_1801.parquet`, `census_1850.parquet`, `census_1860.parquet`, `census_1880.parquet`,
  `census_1901.parquet` (all columns of `census_<year>__v1__cl.csv` from the Digidata zip)

The census files are streamed from `14001.zip` one at a time: only the five census
CSVs and the Release 2 Guide are read, the rest of the ~10.6 GB release is never
unpacked, and at most one CSV (up to 675 MB) is on disk at a time. The Guide is
extracted to `data/raw/digidata_14001/Link_Lives Release 2 Guide (2025).pdf`.

Writes are atomic (temp file renamed into place), so an interrupted run never leaves
a partial parquet at a final path.

## Data governance

Never enters git: raw source files, the converted parquet files, and any record-level
output (rows with names, ages, owners, households or `pa_id` values). Committed
outputs are aggregates only (value-frequency tables, summary statistics, plots), or
`pa_id` plus aggregates.

Notebooks are committed with outputs (D-02), so their outputs must show aggregates
only. Two guards back this up:

- `.gitignore` covers `data/`, `*.xlsx`, `*.zip`, `*.csv` and `*.pdf`.
- A tracked pre-commit hook (`.githooks/pre-commit`) rejects staged paths under
  `data/` or ending in `.xlsx`, `.zip` or `.pdf`, and scans every staged `.ipynb`
  with `scripts/check_notebook_outputs.py`. Enable it once per clone (the setting is
  shared by all worktrees of that clone):

  ```bash
  git config core.hooksPath .githooks
  ```

The notebook scanner is a heuristic on table headers; the final check is a human
read of the rendered outputs. Run it by hand with:

```bash
python3 -I scripts/check_notebook_outputs.py path/to/notebook.ipynb
python3 -I scripts/check_notebook_outputs.py --require-empty path/to/notebook.ipynb  # source must carry no outputs
python3 -I scripts/check_notebook_outputs.py --self-test
```

## EDA notebooks

- `task1_handicaps/eda.ipynb`: Task 1, exploration of the `handicaps` variable across the census years.
- `task2_linking/eda.ipynb`: Task 2, exploration of the 1846 and 1850 Danish West Indies censuses ahead of linking.

Both are committed with their outputs (D-02), so GitHub renders them inline. The
outputs were reviewed by hand under the no-record-level rule (no name next to an age,
owner, birthplace or household; no `pa_id` or record-number columns; no owner names;
no name shown with a count below 5; no identifying free text) and pass
`scripts/check_notebook_outputs.py`; the pre-commit hook re-scans them on every commit.

Re-rendering needs the local data under `data/` (see "Data (not in git)" and "Prepare data"):

```bash
uv run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 task1_handicaps/eda.ipynb
uv run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 task2_linking/eda.ipynb
uv run python scripts/check_notebook_outputs.py task1_handicaps/eda.ipynb task2_linking/eda.ipynb
```

Check the outputs again before committing a re-render.
