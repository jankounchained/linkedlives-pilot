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

Writes are atomic (temp file renamed into place), so an interrupted run never leaves
a partial parquet at a final path.
