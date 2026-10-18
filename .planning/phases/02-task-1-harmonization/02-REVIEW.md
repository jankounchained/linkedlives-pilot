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
  critical: 2
  warning: 5
  info: 3
  total: 10
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-18  **Depth:** standard  **Files Reviewed:** 5  **Status:** issues_found

## Summary

The pipeline is deterministic and the internal invariants hold. File A has 3,416 rows and no duplicate values. `n_total` equals the sum of the year counts. Each cluster has exactly one leader, which is its most frequent value. The lookup covers exactly the 300 review leaders. The data-governance guard works as long as the data root is trusted, and no census records are committed.

Two problems in the committed deliverable are substantive. First, fuzzy clustering merges values that differ in their digits, so `proposed_standard` states false numbers with high confidence (CR-01). Second, the README attributes the single-letter codes to 1801 when they come from 1901 (CR-02). The lookup validation also lets nulls through (WR-01). Details follow.

## Critical Issues

### CR-01: Clustering merges values that differ only in digits, so proposed_standard states a wrong number at high confidence

**File:** `task1_handicaps/harmonise.py:111-126, 223-243` (outputs in `task1_handicaps/outputs/handicaps_mapping.parquet`)

**Issue:** `fuzz.ratio` treats digits like any other character, so values with different onset ages and durations are merged. In the 300 review clusters, 1,023 values (1,883 records, 80 clusters) sit under a leader whose digit tokens differ. Examples from File A:

- "forstanden berøvet fra det 46 aar" and "...4 aar" get `proposed_standard` "forstanden berøvet fra det 20 aar", with confidence 0.94–0.98.
- "syg i 1 aar" maps to "syg i 2 aar" (0.91).
- "patient fra sit 27 ende aar" and "...51 ende aar" map to "...30 ende aar" (about 0.93).

File A's stated purpose is to be applied as the standardisation. Anyone who does that silently loses or falsifies the age at onset or the duration of illness, while the confidence column reports these rows as near-certain spelling variants. D-03 fixes the fuzzy method, but the README only warns in general terms that it "can also merge different terms". It never names this digit failure mode, and the confidence score actively hides it.

**Fix:** Add a cheap, parameter-free guard: make digit tokens part of the cluster key, so a value can only join a leader whose digit sequence is identical:
```python
import re
def digits(s): return tuple(re.findall(r"\d+", s))
# in leader_clusters: restrict candidates to leaders with the same digits
cands = [l for l in leaders if digits(l) == digits(v)]
match = process.extractOne(v, cands, scorer=fuzz.ratio, score_cutoff=threshold) if cands else None
```
If the current behaviour is kept instead, add a File A column such as `digits_differ` and document the failure mode in the README under Assumptions and Next steps. In either case, drop the word "unchanged" from the README's claim about the Phase 1 method.

### CR-02: The README attributes the single-letter codes to 1801 (a false finding in the deliverable)

**File:** `task1_handicaps/README.md:83` (compare lines 35 and 39)

**Issue:** Line 83 says "other/unclear" is large "mostly because of the 1801 single-letter codes ("s", "a", "d", "b")". File A shows otherwise:

- 1801 has only 86 filled records in total, and its only values are "k" (41) and "m" (45).
- "s", "a", "d" and "b" sit almost entirely in 1901: "s" 1,767, "a" 1,421, "d" 336 and "b" 282 records, against 0–4 in the other years.

The README also contradicts itself: line 35 says 1801 has only 2 distinct raw values, and line 39 names them as M and K. The interpretation matters too. The 1901 letters are plausibly abbreviations of sindssyg, åndssvag, døvstum and blind: "D [Døvstum]" appears as a raw spelling, yet the lookup files these letters under "other/unclear". The README presents a wrong finding as an insight, and the interview will be built on it.

**Fix:** Replace the sentence with: "mostly because of the 1901 single-letter codes ("s", "a", "d", "b": 1,767, 1,421, 336 and 282 records), which may be abbreviations; the 1801 values "M" and "K" are a separate case (86 records)." Also add the 1901 letter codes to the Questions for Bárbara and Olivia, which currently mention only "leading letter codes".

## Warnings

### WR-01: load_lookup and check_lookup validation lets null labels and conflicting duplicates through

**File:** `task1_handicaps/harmonise.py:303-309, 320, 458-461`

**Issue:** For null cells, `~is_in(...)` and `!= CATEGORY_SOURCE` evaluate to null, and `filter` drops those rows. A lookup with `suggested_category = None` and `category_source = None` was confirmed to report `bad = 0` and pass. `check_lookup` has the same hole, because `Series.is_in(...).all()` ignores nulls. Separately, `.unique(subset="leader")` (line 320) has no `keep` or ordering, so when the lookup has duplicate leaders with conflicting categories it silently picks one of them. The docstring promises that a bad lookup "leaves previous outputs untouched", and these checks do not enforce that.

**Fix:**
```python
if lookup["suggested_category"].null_count() or lookup["category_source"].null_count() or lookup["leader"].null_count():
    ...exit(2)
if lookup["leader"].is_duplicated().any():
    ...exit(2)
```
In `check_lookup`, use `fill_null(False)`, or keep `is_in(...).all()` with an explicit null check.

### WR-02: Merged members inherit the leader's category even when they name a different condition

**File:** `task1_handicaps/harmonise.py:323-337`, `task1_handicaps/category_suggestions.parquet`

**Issue:** Inheritance itself is deliberate (D-10), but these mismatches are not:

- "døvstum forstanden berøvet fra fødselen" (confidence 0.89) is merged into idiot cluster 6, so a deaf-mute value gets "uden forstandsevner/idiot".
- "forstanden berøvet fra fødselen vanvittig" joins the same cluster, although "vanvittig" means insane.
- The lookup treats near-synonyms differently. The leaders "aandsvag" and "åndssvag" map to "uden forstandsevner/idiot", but "sindssvag", "sindssvag fra det 22 aar" and "sindsvag fra 28 aar" map to "sindssyg".

File A has no marker for an inherited category, so "døvstum forstanden berøvet fra fødselen" looks as if it was classified directly.

**Fix:** Add a `category_inherited` boolean (`value != proposed_standard`) to File A and File B, so the historian can see which labels are inherited. Re-check the "svag"/"syg" leaders in the lookup for consistency. Optionally, make `confidence_min` and the lowest-confidence members more prominent in the review file.

### WR-03: CSV formula injection in the historian CSV files

**File:** `task1_handicaps/harmonise.py:422-431` (affects `merged_spellings`, and in the records CSV `handicaps` and every other free-text column)

**Issue:** The CSVs are meant to be opened in Excel, and raw values are written unescaped. Seven raw spellings in the review clusters start with "-", for example "- [ Døvstum ]", "- [ sindssvag ]" and "- [ FT-1870: ... ]", covering 3,256 records. `merged_spellings` begins with the top raw spelling, and the records CSV carries every census column (names, remarks and so on). Excel reads a leading `=`, `+`, `-` or `@` as formula or number syntax, so these cells display wrongly or as `#NAME?`. This is the OWASP CSV-injection class. The source is third-party transcribed data, not an attacker, but the display corruption is real.

**Fix:** In the CSV copy only, prefix any cell that begins with `=`, `+`, `-`, `@` or a tab with a single quote; leave the parquet unchanged:
```python
def csv_safe(df):
    return df.with_columns(pl.col(pl.String).map_elements(
        lambda s: "'" + s if s and s[0] in "=+-@\t\r" else s, return_dtype=pl.String))
```

### WR-04: assert_local_only only checks that the path is under DATA_ROOT, not that it is gitignored

**File:** `task1_handicaps/harmonise.py:159-170`, `scripts/project_paths.py:39-42`

**Issue:** The D-15 guard is `path.resolve().is_relative_to(DATA_ROOT)`, and `DATA_ROOT` is taken verbatim from `LINKING_LAB_DATA`. If that variable points at a tracked location (the repo root, `task1_handicaps/`, `.`), the guard passes and whole census records are written where they can be committed. `.gitignore` covers only `data/` and `*.csv`, so the records parquet would be exposed. This is the one-way risk D-15 itself names. The `file_b_inside_data_root` test in `--check` has the same weakness.

**Fix:** Also require the path to be git-ignored:
```python
def assert_local_only(path):
    ignored = subprocess.run(["git","check-ignore","-q",str(path)], cwd=pp.REPO_ROOT).returncode == 0
    if not (inside_data_root(path) and ignored): ...exit(2)
```
Alternatively, reject a `LINKING_LAB_DATA` that resolves inside `REPO_ROOT` unless it is under `REPO_ROOT/data`.

### WR-05: main_checkout_root assumes the common git dir is a `.git` directory directly under the checkout

**File:** `scripts/project_paths.py:22-42`

**Issue:** `Path(out).parent` is the main checkout only when the common git dir is a plain `.git` directory. For a submodule (`.git/modules/x`), a `--separate-git-dir` repository or a `GIT_DIR` environment override, the data root silently resolves to the wrong place. `RAW_DIR`, `PARQUET_DIR` and `OUTPUTS_DIR` all follow it, so the scripts would either report the census parquet files as missing or write File B somewhere unexpected. The subprocess also runs at import time as a side effect, with no timeout. Related: when git is unavailable, the `except` branch falls back to `REPO_ROOT`, which inside a worktree is the worktree itself, the very case this module exists to handle.

**Fix:** Trust the parent only when `Path(out).name == ".git"`; otherwise fall back to `REPO_ROOT` with a warning on stderr. Add a `timeout=` to the `subprocess.run` call.

## Info

### IN-01: Dead or misleading FACT lines and a stale lint suppression

**File:** `task1_handicaps/harmonise.py:31, 257, 318, 319`

**Issue:**

- `fact("lookup.missing", len(missing))` always prints 0, because the line above has already exited when `missing` is non-empty. The README's Key figures list it as if it were informative.
- The `# noqa: E402,F401` on the `_tmp_path`/`write_atomic` import is stale, since both names are used. The import also pulls the private `_tmp_path` from another script.
- The README says "Nothing is hard-coded" about coverage, but the tuples `(100, 200, 300, 360)` and `(80, 90, 95)` at lines 257 and 259 are literals.

**Fix:** Drop the always-zero FACT, or compute it before the exit. Remove `F401` from the noqa. Reword the README claim, or derive the k-list from `RECORDS_PER_HOUR_RANGE` and `HOURS_PER_DAY_RANGE`.

### IN-02: Example sampling reuses the same permutation for every cluster of equal size

**File:** `task1_handicaps/harmonise.py:364`

**Issue:** `shuffle(seed=SEED).over("cluster_id")` uses the same seed in every group. Two groups of 10 were confirmed to select identical positions. Because selection is positional within the `(year, pa_id)` sort order, clusters of equal size get identical selection patterns. Each record's marginal inclusion probability is still uniform, but the draws are correlated across clusters, which does not match the README's "drawn uniformly at random". The sample is reproducible and unbiased within each cluster, so the impact is low.

**Fix:** Seed per cluster, for example with a hash of `year` and `pa_id` (`pl.col("pa_id").hash(seed=SEED)`), and keep the 5 lowest keys per cluster. That is order-independent and gives each record its own key.

### IN-03: --check does not test the README or the lookup against the actual clustering

**File:** `task1_handicaps/harmonise.py:465-571`

**Issue:** `--check` validates the structure and invariants of the written files. It does not confirm that the lookup's leaders still equal the current review leaders: it catches review leaders missing from the lookup, but not unused lookup rows. A changed REF_THRESHOLD or leader order therefore passes `--check` until the next full run. The README figures are also copied by hand from the FACT output with no automated cross-check, and CR-02 shows that hand-written commentary can drift from the data.

**Fix:** Have `--check` also assert `set(lookup.leader) == set(review.proposed_standard)`, so the comparison runs in both directions. Add a note beside the FACT block that prose claims outside "Key figures" are not machine-checked.

---

_Reviewed: 2026-10-18_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
