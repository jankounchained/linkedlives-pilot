---
phase: 02-task-1-harmonization
verified: 2026-10-18T21:45:00Z
status: human_needed
score: 13/13 must-haves verified
covered_files:
  - ".planning/phases/02-task-1-harmonization/02-01-PLAN.md"
  - ".planning/phases/02-task-1-harmonization/02-01-SUMMARY.md"
  - ".planning/phases/02-task-1-harmonization/02-02-PLAN.md"
  - ".planning/phases/02-task-1-harmonization/02-02-SUMMARY.md"
  - ".planning/phases/02-task-1-harmonization/02-03-PLAN.md"
  - ".planning/phases/02-task-1-harmonization/02-03-SUMMARY.md"
  - "scripts/project_paths.py"
  - "task1_handicaps/README.md"
  - "task1_handicaps/category_suggestions.parquet"
  - "task1_handicaps/harmonise.py"
  - "task1_handicaps/outputs/handicaps_mapping.parquet"
covered_digest: "v3:sha256:203f187e42a22f370b2ff0b411626524dfefa225a1bfbde366b30eb178c6f678"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 9/11
  gaps_closed:
    - "HARM-01 / CR-01 (digit-blind clustering): D-17 digit guard in leader_clusters; 0 content rows in File A whose digit runs differ from their proposed_standard (independent re-check)"
    - "HARM-05 / CR-02 (README misattributed single letters to 1801): README now attributes s/a/d/b to 1901 with counts matching File A; 1801 M/K treated separately; 1901 letters added to the questions list"
    - "HARM-06 acceptance: REQUIREMENTS.md HARM-06 and ROADMAP criterion 3 reworded to the confirmed scope (zero, D-07/D-18), so requirement text and delivered scope now agree"
  gaps_remaining: []
  regressions: []
gaps: []
deferred: []
advisory: []
human_verification:
  - test: "Decide whether the committed File A (task1_handicaps/outputs/handicaps_mapping.parquet, columns value and raw_spellings) may stay as it is. 2,813 of 3,333 content values occur in at most 2 records and are verbatim transcribed free text (up to 50 characters here, source-truncated); the code review (CR-01) found strings naming a person and describing a household."
    expected: "Either (a) accept the recorded user decision (02-REVIEW-DISPOSITION.md: deferred 2026-10-18, repo goes only to Rigsarkivet who holds the source data, disclosed in README Outputs) as an explicit exception to the project rule that committed outputs are pa_id + aggregates only, or (b) mask rare values in the committed File A and purge earlier versions from git history before hand-in"
    why_human: "A one-way governance decision against a stated project constraint (CLAUDE.md Data governance). It was consciously deferred and disclosed, so it is not a code gap, but the verifier cannot grant the exception. The same rare strings are already in history (56f2eb5, 4d8c6e8 and earlier)"
  - test: "Read task1_handicaps/README.md top to bottom without opening the code, then open data/outputs/task1/handicaps_review.csv in a Danish-locale spreadsheet and skim suggested_category and category_inherited, especially the 111 labels written in 02-03"
    expected: "README can be followed from EDA findings to next steps; CSV opens with ae/oe/aa intact, 300 rows, empty decision and comment; suggestions are historically plausible, inherited ones recognisable"
    why_human: "Readability for Barbara and Olivia and historical plausibility of LLM labels are judgements. Plan 02-02 Task 2 and plan 02-03 Task 3 both defer this to an end-of-phase human check that has not been done"
---

# Phase 2: Task 1 - Harmonization Verification Report

**Phase Goal:** The historians get a first-iteration harmonisation of `handicaps`: a complete mapping from raw values to proposed standard values, and a bounded, impact-ranked review file Asbjorn can work through.
**Verified:** 2026-10-18T21:45:00Z
**Status:** human_needed
**Re-verification:** Yes - after gap closure (plan 02-03). Previous status gaps_found, 9/11.

## Verdict in one paragraph

The goal is achieved in the codebase and both previous gaps are closed on independent evidence, not on the SUMMARY. A fresh `uv run python task1_handicaps/harmonise.py` exits 0, rewrites File A (3,416 rows, 17 columns) byte-for-byte as committed (`git status` shows no change under `task1_handicaps/`) and a 300-row File B; `--check` prints 33 OK lines and no FAIL. My own re-derivation of the digit guard over File A (regex `\d+` runs of `value` against `proposed_standard`, all 3,333 content rows) finds 0 mismatches, against 1,061 values before. All 47 FACT lines printed by the run are identical to the 47 FACT lines in the README Key figures (sorted diff empty). The single-letter finding is now correct against File A. One thing needs a human, not a code change: the committed File A still carries verbatim rare free-text values, which the review flagged (CR-01) and the user consciously deferred with a README disclosure. That sits against the project's data-governance constraint, so the status is `human_needed`, not `passed`.

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| 1  | SC1: decisions recorded in PROJECT.md before the scripts (and D-17 before the guard code) | VERIFIED | `git merge-base --is-ancestor c2cca33 0dfb17d` exit 0; `1c33fbc` (D-17/D-18 in PROJECT.md) is a strict ancestor of `56f2eb5`, the commit that first added `def digit_runs`. PROJECT.md lines 89-91 hold the rows |
| 2  | SC2 / HARM-02: script regenerates File A, one row per normalised value, per-year freq, proposed standard, confidence, category marked as suggestion | VERIFIED | Fresh run exit 0, only `wrote ...` and FACT lines on stdout. File A: 3,416 rows, 3,416 distinct `value`, columns n_1801..n_1901, n_total, raw_variants_n, raw_spellings, cluster_id, proposed_standard, confidence, in_review, suggested_category, category_source, category_inherited. Year column sums 86 / 13,144 / 21,575 / 48,011 / 60,781. `category_source` only `llm_suggestion` or null; 1,249 rows with a category = 1,249 `in_review` rows |
| 3  | HARM-01: spelling normalisation proposes variant spellings only, never a different number | VERIFIED | Independent check: 0 of 3,333 content rows have digit runs different from `proposed_standard`; content confidence in [0.85, 1.0]; `--check` `OK digit_runs_match_leader violations=0`. Guard is `leader_clusters` restricting candidates to `by_digits[digit_runs(v)]` (harmonise.py), exact equality, no new constant (diff since 229a48e adds only `REF_THRESHOLD` comment and `RISKY_START`). Residual: numbers written as words can still merge (disclosed, deferred IN-02) |
| 4  | D-01 placeholder rule: no-letter values placeholders, null cluster/standard/confidence, excluded from coverage | VERIFIED | 83 placeholder rows, all with null proposed_standard, confidence and cluster_id; `FACT values.placeholder=83`, `records.content=33210`; `--check` `placeholder_rows_unclustered n=83` |
| 5  | SC3 / HARM-06: wording-level grouping | VERIFIED (scope zero) | Requirement and roadmap criterion are now worded to the confirmed scope (REQUIREMENTS.md line 30, ROADMAP.md line 59, both cite D-07/D-18). README Next steps documents embedding grouping as a next step and Caveat carries the modern-meaning bias. No embedding code or dependency: `git diff --quiet c2cca33 -- pyproject.toml uv.lock` exit 0 |
| 6  | SC4 / HARM-04: File B review table (parquet + CSV) by impact, sized from 100-120 rec/h x 2-3 h, arithmetic shown, empty decision/comment | VERIFIED | `handicaps_review.parquet`: 300 rows, `n_total` sorted descending (5,004, 3,351, 3,181 ...), sums to 30,774 = 92.66% of 33,210 content records; `decision` and `comment` non-empty count 0 in both; CSV has the same 19 columns, 300 rows, BOM and `csv_cells_safe unsafe=0`. `FACT review.size=300, size_low=200, size_high=360`; README shows both arithmetic lines (D-12) |
| 7  | Example records: <= 5 per cluster, whole records, all clusters present | VERIFIED (counts only) | Records parquet: 1,479 rows, max 5 per cluster, 300 distinct clusters; 21 clusters have < 5 (README reading guide: 1,479 not 1,500). `--check` `records_year_pa_id_unique`, `records_per_cluster_is_min_5_n_total`. File not opened per governance |
| 8  | D-15 governance: record-level outputs never committed | VERIFIED | `git ls-files -- data '*.csv' '*handicaps_review*' '*review_leaders*'` prints nothing; `git check-ignore -v` confirms `.gitignore:2:data/` for review parquet, review CSV and records parquet; `--check` `file_b_inside_data_root`. Tracked under task1_handicaps: README, lookup, eda.ipynb, harmonise.py, File A only |
| 9  | HARM-03: committed auditable lookup, 300 rows, `llm_suggestion`, no runtime API, census vocabulary | VERIFIED | Lookup: 300 rows, 300 distinct leaders, 8 labels all in the fixed vocabulary; `--check` `lookup_no_nulls`, `lookup_leaders_unique`, `lookup_leaders_equal_review_leaders missing=0 unused=0`. Label totals per category match the README FACT lines exactly (e.g. uden forstandsevner/idiot 97 leaders / 8,009 records). Plausibility of labels is a human judgement (item 2) |
| 10 | `category_inherited` (WR-02) | VERIFIED | File A: 949 inherited values, 0 nulls = `FACT category.inherited_values=949`; review table: 210 of 300 clusters flagged; `--check` `category_inherited_consistent inherited_values=949` |
| 11 | CSV safety (WR-03): escaping only in CSV copies, parquet intact | VERIFIED | Review CSV: 0 cells with a risky first character; review parquet also 0 such cells in the columns I scanned; `--check` `*_csv_cells_safe unsafe=0` for both CSVs (the records file is where risky parquet cells occur; the check compares them to escaped CSV cells). Not opened by me |
| 12 | SC5 / HARM-05: README takes a reviewer EDA -> assumptions -> decisions -> conclusions -> next steps, figures traced to FACT lines | VERIFIED (readability: human item) | Sections present: How to run, Outputs, EDA findings, Assumptions, Decisions (D-01..D-17, D-19), Conclusions, Next steps, Caveat, Key figures. Sorted diff of run FACT lines vs README FACT lines is empty (47 = 47, both directions). Prose figures re-derived from File A: 3,806 = 1,767 + 1,421 + 336 + 282 (1901 letters); in 1901 s 1,767, a 1,421, d 336, b 282, and 1801 holds only k 41 / m 45 = 86 records; 2,813 values with <= 2 records; 2,494 singletons; tail 1,860 clusters / 2,436 records / 2,084 values; s/a/d/b all labelled other/unclear. The Phase 1 preview mismatch (1,732 vs 2,160 clusters) is explained in Conclusions |
| 13 | Prohibitions: no "no handicap" reading of empties; no record content in README; no HARM-06 implementation claim; eda.ipynb untouched | VERIFIED | README states empty must not be read as "no handicap"; README holds only value strings and aggregates (no pa_id); `git diff --quiet 6c53637 -- task1_handicaps/eda.ipynb` exit 0 |

**Score:** 13/13 truths verified, 0 behavior-unverified. The `human_needed` status comes from the two human items below, not from any failed truth.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `task1_handicaps/harmonise.py` | Script with File A, File B, `--check`, `--write-leaders`, `--lookup`, `def digit_runs` | VERIFIED | 759 lines; `digit_runs`, `leader_clusters(..., digit_guard=True)`, `REF_THRESHOLD = 85` present and used; run and check both exit 0 |
| `task1_handicaps/outputs/handicaps_mapping.parquet` | File A, committed | VERIFIED | tracked, 3,416 x 17, reproduced exactly by a fresh run |
| `task1_handicaps/category_suggestions.parquet` | lookup, committed | VERIFIED | tracked, 300 rows, validated |
| `task1_handicaps/README.md` | Nine sections incl. D-17 | VERIFIED | 162 lines, content checked against File A and FACT output |
| `.planning/PROJECT.md` | D-17 / D-18 decision rows before the code | VERIFIED | recorded in `1c33fbc`, ancestor of `56f2eb5` |
| `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` | HARM-06 / criterion 3 reworded citing D-18 | VERIFIED | lines 30 and 59 respectively; traceability row still `Pending` (orchestrator closes it) |
| `02-REVIEW-DISPOSITION.md` | 10 findings, all with disposition, `open: 0` | VERIFIED | 1 fixed (CR-02), 9 deferred with a reason each, including CR-01 (user decision); see anti-patterns |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `leader_clusters` | `digit_runs` | candidates restricted to identical digit runs | WIRED | `by_digits.get(digit_runs(v), [])`; 0 violations in File A |
| `write_csv_bom` | `csv_safe` | CSV escaped in memory, parquet from unescaped frame | WIRED | `--check` `csv_cells_safe unsafe=0` x2 |
| `check_lookup` | review leaders | two-way set equality | WIRED | `lookup_leaders_equal_review_leaders missing=0 unused=0` |
| README Key figures | harmonise.py FACT output | verbatim lines both directions | WIRED | sorted diff empty, 47 lines |
| harmonise.py | project_paths / prepare_data.write_atomic | imports | WIRED | run writes all five outputs atomically |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| File A / File B | counts, clusters, confidence | polars scan of the five census parquet files (`FACT records.filled=143597`) | yes | FLOWING |
| `suggested_category` | label | committed lookup joined on leader | yes, review clusters only (1,249 rows = 1,249 `in_review`) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Script regenerates outputs | `uv run python task1_handicaps/harmonise.py` | exit 0; five `wrote` lines + 47 FACT lines | PASS |
| File A reproducible | `git status --short` after run | no change under `task1_handicaps/` | PASS |
| Output validation | `... --check` | exit 0; 33 OK, 0 FAIL | PASS |
| README carries every FACT line, no stale ones | sort + diff of run FACT vs README FACT | identical | PASS |
| Digit guard (own regex over File A) | polars + `re.findall(r"\d+")` | 0 mismatches / 3,333 content rows | PASS |
| Letter-code finding | File A per-year counts for s, a, d, b, k, m | s/a/d/b are 1901; 1801 only k 41, m 45 | PASS |
| Governance | `git ls-files` / `git check-ignore` | no record-level file tracked; File B ignored | PASS |
| Dependencies unchanged | `git diff --quiet c2cca33 -- pyproject.toml uv.lock` | unchanged | PASS |

### Probe Execution

SKIPPED: no `probe-*.sh` declared or present.

### Requirements Coverage

Plan frontmatter `requirements:` across 02-01 (HARM-01..04), 02-02 (HARM-05, HARM-06) and 02-03 (HARM-01..06) account for all six IDs. REQUIREMENTS.md maps exactly HARM-01..HARM-06 to Phase 2; no orphans.

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| HARM-01 | 02-01, 02-03 | Automatic spelling normalisation | SATISFIED | Truth 3; 0 digit mismatches; method documented (D-03/D-17) |
| HARM-02 | 02-01, 02-03 | File A: one row per normalised value, per-year freq, standard, confidence | SATISFIED | Truth 2 |
| HARM-03 | 02-01, 02-03 | Suggested category marked as suggestion | SATISFIED | Truths 9, 10; label plausibility is human item 2 |
| HARM-04 | 02-01, 02-03 | File B subset by impact, sized from brief, empty decision/comment, CSV | SATISFIED | Truth 6 |
| HARM-05 | 02-02, 02-03 | Task 1 README | SATISFIED | Truth 12; readability is human item 2 |
| HARM-06 | 02-02, 02-03 | Wording variants: confirmed scope zero, next step documented | SATISFIED | Truth 5, against the reworded requirement. If the user does not accept the rewording (D-18), this reverts to unmet |

REQUIREMENTS.md traceability still shows all six as `Pending` and the checkboxes are unticked; the 02-03 plan leaves that to the orchestrator at phase close.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `task1_handicaps/outputs/handicaps_mapping.parquet` | columns `value`, `raw_spellings` | Verbatim rare free-text values committed (review CR-01) | Warning (human decision, not a code gap) | Conflicts with the project rule "committed outputs: pa_id + aggregates only"; user deferred it with a disclosure in README Outputs and in `02-REVIEW-DISPOSITION.md`. Human item 1 |
| `task1_handicaps/harmonise.py` | `assert_local_only` / `scripts/project_paths.py` | Guard checks location, not gitignore status; empty `LINKING_LAB_DATA` defeats it (WR-02/WR-04) | Warning, deferred | Only under a mis-set environment variable |
| `scripts/project_paths.py` | `main_checkout_root` | Can resolve the data root to an unrelated parent repo after unzip (WR-03/WR-05) | Warning, deferred | Delivery-path risk for the Phase 4 zip |
| `task1_handicaps/README.md` | line 46 | "Values whose numbers differ are never merged" is true for digit runs only (IN-02) | Info, deferred | Number words can still merge |

No TBD/FIXME/XXX marker found in harmonise.py, README.md or project_paths.py (grep empty).

### Prohibition checks (must_haves.prohibitions of 02-03)

| Prohibition | Tier | Result |
| ----------- | ---- | ------ |
| No record-level output staged or committed | test | VERIFIED (git ls-files empty, check-ignore) |
| No new dependency / embedding code | test | VERIFIED (pyproject.toml, uv.lock unchanged since c2cca33) |
| CSV escaping must not alter parquet copies | test | VERIFIED (0 risky cells in review parquet, `--check` compares the records file) |
| eda.ipynb not edited | test | VERIFIED (unchanged since 6c53637) |
| No new tuning constant | judgment | VERIFIED by diff: the only added module constants are a comment change on `REF_THRESHOLD = 85` and the `RISKY_START` regex (not a tuning parameter). Non-authoritative LLM-judge verdict |
| Do not print/open census records or pa_id rows | judgment | NOT independently verifiable after the fact. The summary says compliance; my own run never opened `handicaps_review_records.*` (counts via `--check` and group sizes only). Flagged: unverified-prohibition, human review recommended (cannot be proven from artifacts) |

### Human Verification Required

#### 1. Committed File A with verbatim rare free text

**Test:** Decide whether `task1_handicaps/outputs/handicaps_mapping.parquet` may stay as committed.
**Expected:** Either accept the recorded user decision (deferred 2026-10-18; repo goes only to Rigsarkivet, who hold the source data) as an explicit exception to the project governance rule, or mask rare values and purge history before hand-in.
**Why human:** One-way governance decision against a stated project constraint; it was a conscious, documented deferral so I did not mark it a gap. If accepted, record it as an override, for example:

```yaml
overrides:
  - must_have: "Committed outputs are pa_id + aggregates only (CLAUDE.md data governance)"
    reason: "File A ships rare verbatim values; repo goes only to Rigsarkivet who hold the source data; disclosed in README Outputs (review CR-01 deferred)"
    accepted_by: "user"
    accepted_at: "2026-10-18"
```

#### 2. README and review CSV read-through

**Test:** Read the README top to bottom without the code; open `data/outputs/task1/handicaps_review.csv` in a Danish-locale spreadsheet and skim `suggested_category` and `category_inherited`, including the 111 labels written in 02-03.
**Expected:** Readable end to end; ae/oe/aa intact; empty decision/comment; labels plausible and inherited ones recognisable.
**Why human:** Readability and historical plausibility are judgements; this check was deferred by plans 02-02 and 02-03 and has not been performed.

### Gaps Summary

No gaps. The two gaps of the previous verification (CR-01 digit-blind clustering, CR-02 false 1801 letter-code finding) are closed and re-verified against the data, the README now matches the regenerated outputs exactly, and the HARM-06 requirement text matches the delivered scope. The remaining items are human decisions: the governance exception for the committed rare free-text values, and the read-through of README and review CSV. Housekeeping for the orchestrator: tick the HARM-01..HARM-06 checkboxes and traceability rows once the user closes the phase. One small inconsistency: `02-REVIEW-DISPOSITION.md` and the 02-03 SUMMARY describe the ledger as "6 fixed, 4 deferred", while the disposition table (written after the later re-review) records 1 fixed and 9 deferred; the table is the current truth.

---

_Verified: 2026-10-18T21:45:00Z_
_Verifier: Claude (gsd-verifier)_
