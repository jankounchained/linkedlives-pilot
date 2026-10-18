---
phase: 01-setup-eda
reviewed: 2026-10-18T19:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - .githooks/pre-commit
  - README.md
  - pyproject.toml
  - scripts/check_notebook_outputs.py
  - scripts/prepare_data.py
  - scripts/project_paths.py
  - task1_handicaps/eda.ipynb
  - task2_linking/eda.ipynb
  - uv.lock
findings:
  critical: 0
  warning: 7
  info: 7
  total: 14
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-18
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Reviewed the data guard (pre-commit hook and notebook output scanner), the two data scripts, both EDA notebooks (code cells and the structure of their committed outputs) and the dependency pins.

The analysis code in both notebooks is sound. I traced the casts, joins, window arithmetic, anchor logic and clustering and found no incorrect result. The pair counts and anchor shares are mutually consistent, and the facts printed in the outputs agree with the code. `prepare_data.py` is careful: fixed member names, no extract helpers, atomic writes. `uv.lock` has only expected packages, all from PyPI.

The weak point is the mechanical data guard, which the project treats as the top concern. The scanner and hook work for the common case but have several provable false negatives. I confirmed these by running the scanner's functions on synthetic frames.

- The scanner only inspects table headers, by exact, case-sensitive match against fixed lists.
- The hook's path rules are case-sensitive and top-level-only.
- `project_paths.py` can redirect data writes to a location that is neither gitignored nor hook-blocked.

I found no leaked record-level content in the committed outputs. Every scanned table is an aggregate or value-frequency table. No `pa_id`, record number, absolute path or owner name appears in any output. I checked this structurally, not by quoting values.

No finding is a confirmed leak today. All are gaps that would let a future mistake through.

## Warnings

### WR-01: Scanner does not look at Series reprs, glimpse() or any non-table text, so an identifier column passes

**File:** `scripts/check_notebook_outputs.py:163-174` (`text_tables`), `185-198` (`_output_tables`)
**Issue:** `text_tables` only recognises a polars box table (a `┌` line followed by a `│` line). A displayed `pl.Series` (last expression `df["pa_id"]`) is not a table. Its repr is `shape: (n,)` / `Series: 'pa_id' [str]` / `[ "…" ]`, so nothing is collected. The same holds for `df.glimpse()`, `print(df.row(0))`, and list or dict reprs. I ran `text_tables(repr(pl.Series("pa_id", ["a", "b"])))` and it returned `[]`, so the notebook is reported OK. The docstring admits free text and values are invisible, but a Series of an identifier or name column is detectable from the repr header, and this is the easiest accidental leak (`df["navn"].head(20)` as a last line).
**Fix:** Also parse Series headers and glimpse rows, and feed the names into the same rule engine. For example:
```python
_SERIES = re.compile(r"^Series:\s*'([^']*)'", re.M)
_GLIMPSE = re.compile(r"^\$\s+(\S+)\s+<", re.M)

def text_tables(text):
    ...
    for name in _SERIES.findall(clean) + _GLIMPSE.findall(clean):
        tables.append([name])
    return tables
```
Add self-test fixtures for a Series of `pa_id` and a glimpse output.

### WR-02: Column lists are exact-match, case-sensitive, incomplete, and have drifted from the notebooks' own masks

**File:** `scripts/check_notebook_outputs.py:35-64` (lists), `201-212` (`violations_for_headers`)
**Issue:** `violations_for_headers` uses set membership on the literal header. Several consequences:
- The notebooks create renamed or suffixed columns that are not in the lists. In task 2 these are `surname_raw_1846`, `owner_gn_1846`, `owner_sn_1850`, `birthplace_1846`, `bp_46` and `ow_46`, built in cells 15 and 25. `violations_for_headers(["surname_raw_1846","age_1846"])` and `(["owner_gn_1846","age_1846"])` both return `[]`. A name beside an age would pass, which is exactly what rule B is meant to catch.
- The notebooks mask `source_id`, `Adresse`, `gadenr`, `Matrikel`, `Kommentarer` and `kildekommentar` as sensitive (task 1 cell 7), but none of these are in `IDENTIFIER_COLUMNS`. `skema_lbnr` and `KIPNr` are not listed either. `source_id` is not masked in task 2 at all (see IN-01).
- Matching is case-sensitive: `["PA_ID"]` and `["Navn"]` pass.

**Fix:** Normalise before matching (`h.strip().lower()`), and match name and identifier columns by pattern as well as exact name. For example:
```python
_NAME_RX = re.compile(r"(^|_)(navn|name|gn|sn|surn|surname|owner|ow)(_|\d|$)", re.I)
_ID_RX   = re.compile(r"(^|_)(pa_id|id|nbr|nr|lbnr|record|household)(_|\d|$)", re.I)
```
Then generate the exact lists from one shared source (a small module imported by the notebooks' `MASK_EXAMPLE_COLUMNS` and the scanner) so they cannot drift.

### WR-03: Text tables truncate headers, so exact header matching fails for `print(df)` / stream outputs

**File:** `scripts/check_notebook_outputs.py:163-174`, `194-195`
**Issue:** With more than a few columns, polars truncates header names to about 10 characters in the text repr. I checked a 9-column frame: `inp_FS_HOUSEHOLD_ID` became `inp_FS_HOU`, `Husstands_familienr` became `Husstands_`, and `løbenr_i_indtastning` became `løbenr_i_i`. The scanner's HTML branch sees full names, but a `stream` output (`print(df)`) or an `error` traceback has only the truncated text. Those headers never equal an entry in `IDENTIFIER_COLUMNS`, so rule A cannot fire. The self-test only uses short, untruncated header names.
**Fix:** For text-table headers, do prefix matching. Treat a header as a hit if it is a prefix of a listed column and at least 6 characters long, or ends in `…`. Add a self-test with a wide frame in a `stream` output.

### WR-04: Any count-like header disables rule C and exempts a column from rule B; the "name with count below 5" policy is not enforced

**File:** `scripts/check_notebook_outputs.py:96-110`, `201-212`
**Issue:** `is_count_like` accepts `n`, `len`, `count`, `rank`, `rate`, `n_*`, `cum_*` and several suffixes. Once any header matches, rule C is off for the whole table. In rule B the count-like header is also ignored when looking for a "non-name partner". A table `[navn, n]` is accepted no matter what `n` holds. A name with `n = 1` is exactly what the README rule "no name shown with a count below 5" forbids, but the scanner cannot see values. `rank`/`len` are ordinary names for non-aggregate columns, for example the character length of a name. This weakens the guarantee the README makes ("pass `scripts/check_notebook_outputs.py`").
**Fix:** In the table parsers, also capture the body of the count-like column. For a table that has a name column and a count column, flag the table if any count in it is below `MIN_EXAMPLE_COUNT` (5). Failing that, state in the README and the docstring that the min-count rule is review-only. Narrow `is_count_like` by dropping `rank`, `len` and `rate`, which are not counts of records.

### WR-05: Hook path rules are case-sensitive and top-level-only; parquet and csv are not blocked outside `data/`; the hook fails open if `git diff` fails

**File:** `.githooks/pre-commit:14-20, 32`; also `.gitignore` (no `*.parquet`)
**Issue:**
- `case "$path" in data/*|*.xlsx|*.zip|*.pdf)` is case-sensitive. `MF_census.XLSX`, `Release.ZIP` and `guide.Pdf` pass. `.gitignore` is case-sensitive too, so nothing else stops them.
- `data/*` anchors at the repo root. `task2_linking/data/x.xlsx` is caught by the extension rule, but `task1_handicaps/data/census_1850.parquet` or `out/dwi.csv` is not blocked by the hook. The converted parquet files are full raw data. `.gitignore` has `*.csv` but no `*.parquet`. Anything written outside `data/` (see WR-06) is therefore unprotected, and `git add -f` bypasses the ignore.
- The loop reads from `< <(git diff --cached ...)`. Under `set -e`, a failing `git diff` inside process substitution does not abort the script, so the loop sees no input and the hook exits 0.

**Fix:**
```bash
shopt -s nocasematch
case "$path" in
  data/*|*/data/*|*.xlsx|*.zip|*.pdf|*.csv|*.tsv|*.xls|*.sav|*.dta) ... ;;
esac
shopt -u nocasematch
```
Also add `census_*.parquet` and `dwi_*.parquet` (the raw-data conversions) to the blocked patterns and to `.gitignore`; later committed `pa_id` plus aggregate parquets must keep working. For the fail-open case, collect the list first with `mapfile -d '' -t paths < <(git diff … )` after checking `git diff --cached --quiet` exit codes, or use `git diff-index` into a temp file and test its status.

### WR-06: Empty or relative `LINKING_LAB_DATA` redirects raw-data writes into an unignored, unblocked location

**File:** `scripts/project_paths.py:39-42`
**Issue:** The check is `"LINKING_LAB_DATA" in os.environ`, so `LINKING_LAB_DATA=""` (a common shell slip, such as `export LINKING_LAB_DATA=$UNSET_VAR`) gives `DATA_ROOT = Path("")`, which is `.`. `prepare_data.py` would then write `./parquet/census_*.parquet` and extract the Release Guide into `./raw/...`, relative to the current directory. For a repo-root run that is untracked, not gitignored (see WR-05) and not blocked by the hook, so a plain `git add .` stages the full census conversion. A relative value gives the same cwd-dependent behaviour. The docstring says "absolute path" but nothing enforces it.
**Fix:**
```python
_env = os.environ.get("LINKING_LAB_DATA", "").strip()
if _env:
    DATA_ROOT = Path(_env).expanduser()
    if not DATA_ROOT.is_absolute():
        raise SystemExit("LINKING_LAB_DATA must be an absolute path")
else:
    DATA_ROOT = main_checkout_root() / "data"
```

### WR-07: Task 2 notebook states "The committed notebook carries no outputs", which is false

**File:** `task2_linking/eda.ipynb` cell 0 (markdown), "Data governance" paragraph
**Issue:** The notebook is committed with outputs under the D-02 decision. It has 60-odd output blocks, and the README says so. The cell 0 sentence ("The committed notebook carries no outputs; the executed copy is reviewed locally first") is a leftover from the earlier plan to commit it cleaned. A reader, or a later maintainer relying on it, would conclude the outputs are not in git and could skip the per-commit review the README requires. The task 1 notebook has no such claim, so the two also disagree.
**Fix:** Replace it with: "The notebook is committed with its outputs (aggregates only, reviewed by hand and scanned by `scripts/check_notebook_outputs.py`)."

## Info

### IN-01: Masking lists differ between the two notebooks

**File:** `task1_handicaps/eda.ipynb` cell 7 vs `task2_linking/eda.ipynb` cell 1 (`MASK_EXAMPLE_COLUMNS`)
**Issue:** Task 1 masks `source_id` (and `Kommentarer`, addresses). Task 2 does not mask `source_id`, and the DWI frame has that column. Task 2's committed overview shows an example for it (a 2-character code with a count of at least 5), so nothing identifying is shown today. The policy is applied inconsistently, and only the count threshold prevents a leak.
**Fix:** Mask `source_id` in task 2, or define one shared mask set in `scripts/` (see WR-02).

### IN-02: Raw free-text `handicaps` strings are shown below the min-count threshold

**File:** `task1_handicaps/eda.ipynb` cells 32 and 34 (5a/5b)
**Issue:** The markdown in cell 30 says the strings "are shown at any count". In the committed output of cell 34, 14 of 76 rows have a count under 5, 7 with a count of 1. All are short, name-free-looking condition words, but the free-text field can in principle contain names, and the scanner cannot inspect these cells. The README/notebook statement of "no identifying free text" is therefore only a human check.
**Fix:** Apply `MIN_EXAMPLE_COUNT` in 5b (show variants with n >= 5, or show a "(n < 5)" bucket count), consistent with the rule used in the column-overview tables.

### IN-03: Punctuation-only values become an empty "normalised value" and are counted

**File:** `task1_handicaps/eda.ipynb` cell 27 (`trivial_norm`, `YEAR_RAW`)
**Issue:** `filled("raw")` tests the raw string. A value like `-` or `?` passes it, and `trivial_norm` turns it into `""`. That empty string counts as one distinct normalised value, becomes a cluster leader, and takes part in the coverage curves and the "values a reviewer must look at" figures that feed the File B decision.
**Fix:** After normalising, filter `pl.col("norm") != ""` out of `YEAR_RAW`, and report their number as a separate fact (`task1.punctuation_only_n`).

### IN-04: Parish key can collide when a level is missing

**File:** `task1_handicaps/eda.ipynb` cell 21 (`geo_key`)
**Issue:** `concat_str(..., ignore_nulls=True)` drops missing levels, so a record with only `Sogn="X"` and one with only `Amt="X"` get the same key `X`. This can merge unrelated units in `units_n` and `empty_unit_share`.
**Fix:** Keep the separators, for example `pl.concat_str([pl.col(c).str.strip_chars().fill_null("") for c in GEO], separator="|")`, then treat `"||"` as "no geography".

### IN-05: Inconsistent whitespace handling between `filled()` and grouping

**File:** `task2_linking/eda.ipynb` cell 8 (examples `group_by("v")`) and cell 29 (`group_by(... "inp_FS_HOUSEHOLD_ID")`)
**Issue:** `filled()` strips, but the grouping uses the unstripped value. `" 123"` and `"123"` count as different example values and different households. Task 1 strips before grouping, so the two notebooks differ.
**Fix:** Strip once into a column and group on it (`pl.col(col).str.strip_chars().alias("v")`), as in task 1 cell 7.

### IN-06: Planning jargon in deliverables meant for the interviewers

**File:** `task1_handicaps/eda.ipynb` cells 0, 6, 26, 40, 48, 54; `task2_linking/eda.ipynb` cells 0, 5, 24, 28, 30; `README.md:6`
**Issue:** The notebooks go to Linking Lab staff but cite internal identifiers that mean nothing to them: D-02, D-06, D-08/D-09, D-12, HARM-06, LINK-04, "PROJECT.md suspects", "the user's decisions", "Phase 1/2/3". README line 6 says "(Phase 4 completes this README...)". This reads as unfinished and makes the reasoning harder to follow in the interview.
**Fix:** Replace the ids with plain statements ("decided before the EDA", "the main project notes") and drop the README Phase 4 note before the final delivery.

### IN-07: Small quality items

**Files and details:**
- `scripts/check_notebook_outputs.py:222`: `nb.get("cells", [])` silently reports OK (0 tables) for an nbformat < 4 notebook (`worksheets`) or a malformed file. Fail with an error if `cells` is missing or if outputs exist but no table was parsed.
- `.githooks/pre-commit`: protection exists only after `git config core.hooksPath .githooks`. A fresh clone without that step, or `--no-verify`, has no guard. A one-line `uv run`/`make` setup check, or a CI scan, would help. This is documented in the README, so only a note.
- `scripts/prepare_data.py:167-168`: `83414` and `22` are hard-coded, and also appear in the README. Move them to `project_paths.py`.
- `scripts/prepare_data.py:89-91`: `_require_member` rebuilds `set(zf.namelist())` on every call (about 6 times). Build it once.
- `task1_handicaps/eda.ipynb` cell 7: `column_overview(lf, year)` never uses `year`. Cell 34: `LEADERS85` is assigned and never used.
- Both notebooks: `sys.path.insert(0, Path.cwd().resolve().parent / "scripts")` assumes the kernel's working directory is the notebook directory. This holds for nbconvert and JupyterLab, but not for editors that start in the repo root. Prefer locating `scripts/` by searching upward for `project_paths.py`.
- Task 2 cell 19: `B_` is a poor name, and `10**9` in `HH_BINS` is a magic number (use `float("inf")` or a named constant).

---

_Reviewed: 2026-10-18_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
