---
phase: 02-task-1-harmonization
reviewed: 2026-10-18T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - scripts/project_paths.py
  - task1_handicaps/README.md
  - task1_handicaps/category_suggestions.parquet
  - task1_handicaps/harmonise.py
  - task1_handicaps/outputs/handicaps_mapping.parquet
findings:
  critical: 1
  warning: 3
  info: 3
  total: 7
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-18
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Re-review of the Phase 2 harmonisation deliverable after the 02-03 gap-closure plan. The pipeline logic holds up: I recomputed the headline README figures from the committed File A (2,160 clusters, coverage at 100/200/300/360 of 0.8783/0.9103/0.9266/0.9329, 26/158/601 clusters for 80/90/95%, 1,249 review values, 949 inherited, 2,494 singletons at 1.74%, the s/a/d/b = 3,806 and M/K = 86 counts, the 1,860-cluster tail of 2,436 records). All of them match. `harmonise.py --check` reports OK on every check, and the lookup parquet has 300 unique leaders, no nulls, valid labels, and every leader exists in File A.

The one serious problem is a data-governance defect in the committed File A, not in the code. Two findings (WR-02 and IN-03 below) re-raise items already deferred in `02-REVIEW-DISPOSITION.md` (WR-04, WR-05, IN-01) only where the new evidence changes the picture.

Fallow structural findings: none were provided.

## Critical Issues

### CR-01: Committed File A ships verbatim free-text census strings, including personal narrative and a surname

**File:** `task1_handicaps/outputs/handicaps_mapping.parquet` (column `raw_spellings`), produced at `task1_handicaps/harmonise.py:219-221`
**Issue:** The project rule is "raw data and named record-level outputs never enter git — Committed outputs: `pa_id` + aggregates only", and D-15 itself argues that committing record-level data is one-way. File A is committed and contains, for every one of the 3,416 values, the full list of raw spellings (4,520 verbatim strings, up to about 52 characters, the source's own truncation). The `handicaps` column is free text. 2,813 content values occur in at most 2 records, and many of these are one-of-a-kind sentences about a single person. Reading the longest singletons (value-level table, so allowed) shows entries such as an "enke efter liuentenant ... assistent <Surname>." string that contains a personal surname and a household description, and "Sidst han skrev til Hjemmet opholdt han sig i Mexi..." (a personal narrative). A singleton raw string is, in effect, one person's transcribed record text, so this is verbatim FamilySearch partner data in git history (commits 56f2eb5, 4d8c6e8 and earlier). The File A column list in the README presents the file as "value-level only, no records", which is not true for the rare tail. Because the zip in Phase 4 also ships the working tree, this reaches recipients and any remote.
**Fix:** Keep spelling text only where it cannot identify a person, and keep counts everywhere. For example, in `value_table` (and in the `MAPPING_COLUMNS` write path) blank `raw_spellings` for values below a disclosure threshold, and keep `raw_variants_n`:
```python
MIN_SPELLING_COUNT = 5  # publish verbatim text only for values seen in >= 5 records
...
pl.when(pl.col("n_total") >= MIN_SPELLING_COUNT)
  .then(pl.col("raw_spellings"))
  .otherwise(pl.lit(None, dtype=pl.List(pl.String)))
  .alias("raw_spellings")
```
The full `raw_spellings` can stay in the local-only File B (`merged_spellings`, which is already under `data/`). Because the strings are already in history, decide whether a history rewrite is needed before the repo leaves the machine, and update the README File A description either way. Note that the same text is inside `value` itself (a trivially normalised form of the string), so the threshold should apply to `value` for singletons that contain names as well, or the rare tail should be aggregated into a `rare_content` bucket in the committed file and kept in full only in the local-only table.

## Warnings

### WR-01: `load_lookup` silently drops stale leaders that `--check` later rejects

**File:** `task1_handicaps/harmonise.py:365-367` (and `:544-551`)
**Issue:** `load_lookup` fails on missing review leaders but only prints `lookup.unused=N` for lookup rows that are no longer review leaders, then discards them with the final `filter`. `check_lookup` treats the same condition as a failure (`lookup_leaders_equal_review_leaders` requires `unused == 0`). So after any clustering change, a normal run succeeds and writes File A and File B from a lookup that is partly stale, and only a later `--check` goes red, which is the reverse order from what D-19 intends ("rejected before anything is written"). The README (line 16) lists only the missing-row case as an exit-2 condition, so the asymmetry is undocumented too.
**Fix:** Make the main run enforce the same invariant as `--check`:
```python
unused = have - set(leaders)
if unused:
    print(f"category lookup has {len(unused)} rows that are not review leaders (run --write-leaders)", file=sys.stderr)
    sys.exit(2)
```

### WR-02: Record-level output guard can be defeated by an empty or repo-level `LINKING_LAB_DATA` (re-raise of deferred WR-04, with reproduction)

**File:** `scripts/project_paths.py:39-40`, `task1_handicaps/harmonise.py:178-189`
**Issue:** `02-REVIEW-DISPOSITION.md` deferred WR-04 as "only a mis-set `LINKING_LAB_DATA` defeats it". I reproduced a concrete, easy mis-set: `"LINKING_LAB_DATA" in os.environ` is true for an empty value, so `LINKING_LAB_DATA= python ...` (or `LINKING_LAB_DATA=$UNSET_VAR`) yields `DATA_ROOT == Path('.')`, `OUTPUTS_DIR == outputs`, and `inside_data_root` then accepts any path under the current directory. From the repo root this writes `outputs/task1/handicaps_review_records.parquet` (whole census records) into a location that `.gitignore` does not cover (only `data/` and `*.csv` are ignored, so the parquet copy is committable). The guard's stated purpose is to prevent exactly this, and the cost of failure is the one-way leak that D-15 warns about. The fix is two lines, so deferral is not justified by effort.
**Fix:** Ignore empty values and make the guard check ignore status instead of location:
```python
_env = os.environ.get("LINKING_LAB_DATA")
DATA_ROOT = Path(_env).resolve() if _env else main_checkout_root() / "data"
```
and in `assert_local_only`, additionally require `git check-ignore -q <path>` to succeed (exit 0) when the data root is inside a git work tree.

### WR-03: `main_checkout_root` can resolve the data root to an unrelated parent repository (re-raise of deferred WR-05, delivery path)

**File:** `scripts/project_paths.py:22-36`
**Issue:** The function runs `git rev-parse --git-common-dir` with `cwd=REPO_ROOT` and trusts the result. Phase 4 delivers a zip built from the working tree; unzipped without `.git` inside any directory that is itself in a git repository (a recipient's home dir or notes repo is common), git walks upward, returns that unrelated repo's `.git`, and `DATA_ROOT` becomes `<that repo>/data`. Combined with WR-02, the script would then create and write record-level files in the recipient's other repository. Also, a git older than 2.31 (no `--path-format=absolute`) raises `CalledProcessError`, which is swallowed and silently returns `REPO_ROOT`, which is wrong inside a worktree and reintroduces the missing-`data/` problem the module exists to avoid.
**Fix:** Only call git when this tree is itself a checkout:
```python
if not (REPO_ROOT / ".git").exists():   # file in a worktree, dir in a normal checkout
    return REPO_ROOT
```
and print a one-line stderr notice when the git call fails instead of failing silently.

## Info

### IN-01: Main run writes the committed File A before the File B guard runs

**File:** `task1_handicaps/harmonise.py:509-520`
**Issue:** `write_outputs` writes the mapping first and only then calls `assert_local_only` for the File B paths. If the data root is wrong, the script exits 2 after already replacing the committed File A, and File B and File A can be out of sync. The four File B files are also written one after another, so an interrupted run leaves a new review table next to old example records.
**Fix:** Call `assert_local_only` for all four File B paths at the top of `write_outputs` (or in `main` before any write), then write.

### IN-02: README overstates the digit guard ("numbers ... never merged")

**File:** `task1_handicaps/README.md:46`
**Issue:** "Values whose numbers differ are never merged (D-17)" is true only for digit runs. Numbers written as words ("tre aar" versus "to aar") can still merge at ratio >= 85, and "18de" and "18" compare equal. D-17 itself (line 77) states the digit rule correctly, so the assumption bullet contradicts it.
**Fix:** Reword to "Values whose digit runs differ are never merged (D-17); numbers written as words are not covered."

### IN-03: Private cross-module import and stale suppression

**File:** `task1_handicaps/harmonise.py:32`
**Issue:** `from prepare_data import _tmp_path, write_atomic  # noqa: E402,F401` imports an underscore-private helper from another script, and the `F401` suppression is stale (both names are used). Deferred earlier as IN-01 (cosmetic); listed again only because the private import couples two scripts to an implementation detail (the pid-suffixed temp name).
**Fix:** Rename `_tmp_path` to a public name in `scripts/prepare_data.py` (or move both helpers to `project_paths.py`/a small `io_utils.py`), and drop `F401`.

---

_Reviewed: 2026-10-18_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
