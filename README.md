# Linking Lab pre-interview tasks

Task 1: explore and prepare the `handicaps` census variable for standardisation.
Task 2: design and implement a simple method to link the 1846 and 1850 Danish West Indies censuses.

## Findings in brief

**Task 1: `handicaps` (implemented)**

- Of 143,597 filled `handicaps` cells across 1801, 1850, 1860, 1880 and 1901, 77% are placeholders (`-`, `?`, bare numbers). Empty or a placeholder says nothing about a condition, and 1801 is practically empty.
- Trivial normalisation turns 4,520 raw values into 3,416. Fuzzy clustering groups the 3,333 content values into 2,160 clusters, each with a proposed standard (its most frequent spelling) and a confidence.
- One reviewer-day for Asbjørn standardises 92.7% of real-content records. That's 300 clusters, sized from the brief's 100–120 records an hour and 2–3 hours a day. 80% needs only 26 clusters.
- Numbers matter: a digit guard stops "syg i 1 aar" being merged into "syg i 2 aar". It costs 2.5 points of coverage, which I think is worth it.
- Categories are LLM suggestions in the census's own vocabulary (døvstum, sindssyg, uden forstandsevner, ...), so modern meanings don't creep in. The historian decides.
- The review table for the team is `data/outputs/task1/handicaps_review.csv` (File B, details below).

**Task 2: linking (designed, not implemented)**

- Age noise was measured on 1,381 people whose name occurs once in each census. Their age gap centres on the expected 4 years, but the tails are wide. A ±5-year birth-year window keeps 70.6% of them at 16% of the sex-only candidate pairs.
- The free/enslaved flag and both owner fields are empty for every 1850 record. So the change across emancipation (July 1848) can't be observed in this file, and owner can't be a linking feature.
- Plan: block on sex and birth year ±5, then score with an explainable additive score (name, surname, age gap, island, birthplace). Assign links greedily one-to-one with a margin and a confidence band, then run a household second pass. Evaluate plausibility without ground truth. Details are in [`task2_linking/README.md`](task2_linking/README.md).

My questions about the sources are in [`QUESTIONS.md`](QUESTIONS.md).

## Time spent and AI use

I spent about 3.5 hours on this. In that time I explored both datasets and made the decisions: what counts as a placeholder, how to cluster, how big a reviewer-day is, and the Task 2 design. Task 1 got done, and Task 2 got as far as the exploration and the design.

I used Claude Code to write and check the code and documentation from those decisions. Some of that ran while I wasn't at the keyboard.

## Start here

- [`task1_handicaps/README.md`](task1_handicaps/README.md): Task 1, from the EDA findings to the outputs, decisions, conclusions and next steps.
- [`task2_linking/README.md`](task2_linking/README.md): Task 2, the linking design.
- [`task1_handicaps/eda.ipynb`](task1_handicaps/eda.ipynb) and [`task2_linking/eda.ipynb`](task2_linking/eda.ipynb): the exploration behind each task, saved with their outputs.
- `data/outputs/task1/handicaps_review.csv`: the Task 1 review table for the historians ("File B"). It has one row per cluster of `handicaps` spellings, the 300 with the most records first. Each row gives the proposed standard, the merged spellings with counts, a suggested category, and empty `decision` and `comment` columns to fill in. It opens in Excel with a Danish locale. Next to it:
  - `handicaps_review_records.csv`: up to 5 whole census records per cluster as examples, linked by `cluster_id`.
  - `.parquet` copies of both files.
  - `review_leaders.parquet`: a helper list used to refresh the category lookup.

  The records file holds whole census records, so this folder is never committed and travels only inside the hand-in zip.
- `task1_handicaps/outputs/handicaps_mapping.parquet`: the full mapping ("File A"). It has one row per distinct `handicaps` value (after trivial normalisation), with its counts per census, proposed standard, confidence and category.

Delivery: this repository as a zip of its working tree, with the git history and `data/outputs/`, but without `data/raw/` and `data/parquet/`.

Nothing has to run just to read the results: the zip already holds File A, File B and both notebooks with their outputs. To rebuild everything, put the source files in place (see "Data (not in git)") and run:

```bash
uv sync
uv run python scripts/prepare_data.py
uv run python scripts/prepare_data.py --check
uv run python task1_handicaps/harmonise.py
uv run python task1_handicaps/harmonise.py --check
```

## What is where

```text
README.md                  this file
QUESTIONS.md               questions about the sources
pyproject.toml, uv.lock    pinned environment, with .python-version
scripts/                   prepare_data.py (source files to parquet), project_paths.py
                           (where the data lives), check_notebook_outputs.py (output scanner)
task1_handicaps/           Task 1: README.md, eda.ipynb, harmonise.py and
                           category_suggestions.parquet (the LLM category lookup)
task1_handicaps/outputs/   File A, handicaps_mapping.parquet (value-level, committed)
task2_linking/             Task 2: README.md (design note) and eda.ipynb
.githooks/                 pre-commit data guard (see "Data governance")
data/                      gitignored, never committed
  outputs/task1/           File B, whole census records (in the zip only)
  raw/, parquet/           source files and converted data (not in the zip)
```

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

The unzipped hand-in carries its `.git`, so `scripts/project_paths.py` resolves the data
directory to the `data/` folder next to this README (`LINKING_LAB_DATA` still overrides
it). In the zip that folder holds `data/outputs/` but not `data/raw/` or `data/parquet/`.
Create the raw-data folders and copy the source files in as listed in the table above:

```bash
mkdir -p data/raw/digidata_14001 data/raw/linking_lab
```

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

## Reproduce Task 1

The zip already holds both Task 1 outputs, so no run is needed just to see them. To
reproduce them, convert the census files (`uv run python scripts/prepare_data.py --only census`
is enough for Task 1) and run:

```bash
uv run python task1_handicaps/harmonise.py          # write File A and File B
uv run python task1_handicaps/harmonise.py --check  # validate both, write nothing
```

- File A, `task1_handicaps/outputs/handicaps_mapping.parquet`, is committed. The run
  rewrites it in place, so `git status --short task1_handicaps/outputs/` prints nothing
  if the run reproduced the committed file.
- File B is `handicaps_review` and `handicaps_review_records` under `data/outputs/task1/`,
  each as parquet and as a CSV copy for the historians. It holds whole census records,
  so it is never committed and reaches you only inside the zip. The run writes it again
  in the same place and replaces the copy from the zip, so copy the review files
  elsewhere before anyone fills in `decision` and `comment`.
- The script exits with status 2 if a census parquet file is missing. `--check` reads
  only File A, File B and the category lookup, so it also runs straight after unzipping,
  before any data is prepared.
- The other options (`--write-leaders`, `--lookup`), every column and the findings are in
  [`task1_handicaps/README.md`](task1_handicaps/README.md).

Task 2 has no script to run. Its EDA notebook re-renders as described in "EDA notebooks".

## Data governance

Never enters git: raw source files, the converted parquet files, and any record-level
output (rows with names, ages, owners, households or `pa_id` values). Committed
outputs are aggregates only (value-frequency tables, summary statistics, plots), or
`pa_id` plus aggregates. One known exception: the rare free-text values in File A,
described under "Outputs" in `task1_handicaps/README.md`.

Notebooks are committed with outputs, so their outputs must show aggregates only.
Two guards back this up:

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

Both are committed with their outputs, so they can be read without re-running them. The
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
