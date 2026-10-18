---
phase: 02-task-1-harmonization
verified: 2026-10-18T20:15:00Z
status: gaps_found
score: 9/11 must-haves verified
covered_files:
  - ".planning/phases/02-task-1-harmonization/02-01-PLAN.md"
  - ".planning/phases/02-task-1-harmonization/02-01-SUMMARY.md"
  - ".planning/phases/02-task-1-harmonization/02-02-PLAN.md"
  - ".planning/phases/02-task-1-harmonization/02-02-SUMMARY.md"
  - "scripts/project_paths.py"
  - "task1_handicaps/README.md"
  - "task1_handicaps/category_suggestions.parquet"
  - "task1_handicaps/harmonise.py"
  - "task1_handicaps/outputs/handicaps_mapping.parquet"
covered_digest: "v3:sha256:ede950e891160d007f6af0b121a6e82e1eb1e91830bfc4778ef10e8b4d638af8"
behavior_unverified: 0
overrides_applied: 0
re_verification: false
gaps:
  - truth: "HARM-01 / D-03: variant spellings are normalised automatically; proposed_standard and confidence are trustworthy enough to apply (ROADMAP SC2)"
    status: partial
    reason: "fuzz.ratio >= 85 clustering treats digits as ordinary characters, so values that differ in onset age or duration are merged and the proposed_standard states a different number at high confidence. Independently confirmed against File A: 1,023 of the review-cluster values (1,883 records, 80 of 300 clusters) sit under a leader whose digit tokens differ; across all content, 1,061 values / 1,921 records. Example: 'syg i 1 aar' -> 'syg i 2 aar', confidence 0.909. That is about 6% of the records in the review clusters. The method is Phase 1's, locked unchanged by D-03, so this is not an execution deviation; but the README only warns generically ('can also merge different terms') and never names the digit failure mode, and the confidence column hides it."
    artifacts:
      - path: "task1_handicaps/harmonise.py"
        issue: "leader_clusters (lines 111-126) matches on fuzz.ratio only, with no digit-identity guard"
      - path: "task1_handicaps/outputs/handicaps_mapping.parquet"
        issue: "1,061 content rows carry a proposed_standard whose digits differ from the row's own value"
    missing:
      - "Either restrict leader candidates to identical digit sequences (parameter-free guard; changes cluster counts, so FACT lines, lookup and README figures must be regenerated), or keep D-03 and document the failure mode explicitly in README Assumptions and Next steps, optionally with a digits_differ column in File A and the review table"
      - "Drop 'unchanged' from the README D-03 wording if a guard is added"
  - truth: "HARM-05 / ROADMAP SC5: the Task 1 README gives correct EDA findings, assumptions, conclusions the interview can rest on"
    status: partial
    reason: "README line 83 says 'other/unclear' is large 'mostly because of the 1801 single-letter codes (\"s\", \"a\", \"d\", \"b\")'. File A shows 1801 holds only 86 filled records with only the values 'k' (41) and 'm' (45). The letters s/a/d/b are 1901 values: s 1,767, a 1,421, d 336, b 282 records, against 0-4 in other years. The README contradicts itself (line 35 says 1801 has 2 distinct raw values; line 39 names them M and K). It is a wrong finding presented as an insight. 02-01-SUMMARY.md makes the same mistake. The questions list (lines 90-94) also does not ask about the 1901 letter codes specifically."
    artifacts:
      - path: "task1_handicaps/README.md"
        issue: "line 83 misattributes single-letter codes to 1801"
    missing:
      - "Reword to: mostly the 1901 single-letter codes ('s' 1,767, 'a' 1,421, 'd' 336, 'b' 282 records), which may be abbreviations; 1801 'M'/'K' (86 records) are a separate case"
      - "Add the 1901 letter codes to the candidate questions for Barbara and Olivia"
human_verification:
  - test: "Decide whether the deliberate HARM-06 descoping (embedding-based wording grouping not implemented) is acceptable as a requirement outcome"
    expected: "Either (a) accept D-07 as the user-confirmed 'scope confirmed after EDA' (REQUIREMENTS.md says 'Scope confirmed after EDA' and CONTEXT.md D-07 records the confirmed scope as zero), and edit REQUIREMENTS.md HARM-06 wording / ROADMAP SC3 to match, or (b) treat it as unmet and plan an embedding pass"
    why_human: "REQUIREMENTS.md HARM-06 and ROADMAP SC3 still read as implementation requirements; the code implements none of it. The deviation is documented (README Next steps, Caveat, PROJECT.md row, CONTEXT D-07, pyproject.toml/uv.lock unchanged since c2cca33) but only the user can decide it counts as satisfying the requirement"
  - test: "Read task1_handicaps/README.md top to bottom without opening the code; open data/outputs/task1/handicaps_review.csv in a Danish-locale spreadsheet and skim suggested_category"
    expected: "README can be followed from EDA to next steps; CSV opens with ae/oe/aa intact, 300 rows, empty decision/comment; suggestions look plausible"
    why_human: "Readability for Barbara and Olivia and historical plausibility of LLM category suggestions are judgements; this was Plan 02-02 Task 2's human-check and the executor did not perform it"
  - test: "Spot-judge the merged-category inheritance (review WR-02) and CSV leading-dash cells (WR-03)"
    expected: "Asbjorn can tell which suggested_category values are inherited from the leader, and cells such as '- [ Doevstum ]' display as text in Excel"
    why_human: "Advisory quality issues from the code review; not must-have failures"
deferred: []
---

# Phase 2: Task 1 - Harmonization Verification Report

**Phase Goal:** The historians get a first-iteration harmonisation of `handicaps`: a complete mapping from raw values to proposed standard values, and a bounded, impact-ranked review file Asbjorn can work through.
**Verified:** 2026-10-18T20:15:00Z
**Status:** gaps_found (two cheap-to-fix defects in the deliverable; the structural goal itself is met)
**Re-verification:** No - initial verification

## Verdict in one paragraph

The structural goal is achieved and independently confirmed: a fresh `uv run python task1_handicaps/harmonise.py` exits 0, regenerates a complete File A (3,416 rows, byte-identical to the committed file, `git status` clean) and a 300-row impact-ranked File B with empty `decision`/`comment`; `--check` passes with 27 OK lines and no FAIL; all 26 FACT lines appear verbatim in the README; governance holds (git tracks exactly two value-level parquet files, nothing under `data/`, no CSV, File B gitignored, dependencies unchanged since c2cca33). Two substantive defects remain in what the historians would receive: CR-01 (digit-blind clustering gives wrong proposed standards at high confidence for about 6% of review-cluster records) and CR-02 (a false finding in the README). Both were confirmed from the data, not just taken from the review. Neither stops Asbjorn from working through the file, but both undermine "proposed standard values" and the README that the interview rests on. HARM-06 is a user-judgement item.

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| 1  | ROADMAP SC1: decisions recorded in PROJECT.md before the scripts | VERIFIED | `git merge-base --is-ancestor c2cca33 0dfb17d` exits 0 (0dfb17d first added harmonise.py). PROJECT.md lines 86-89 hold the Phase 2 rows; footer updated |
| 2  | ROADMAP SC2 / HARM-01..03: script regenerates File A, one row per normalised value, per-year freq, proposed standard, confidence, category marked as suggestion | VERIFIED structurally (see gap 1 for quality) | Fresh run exit 0; File A 16 columns, 3,416 rows; `--check` OK for columns, no pa_id, n_total = year sum, leader confidence 1.0, content confidence in [0.85,1.0], `suggestion_iff_in_review`, `category_source_llm_or_null`; File A unchanged in git after run |
| 3  | HARM-01 spelling normalisation is correct: variant spellings only | FAILED (partial) | 1,023 review-cluster values (1,883 records, 80 clusters) merged under a leader with different digit tokens; "syg i 1 aar" -> "syg i 2 aar" at 0.909. See gaps |
| 4  | Placeholder rule (D-01): no-letter values are placeholders, null cluster/standard/confidence, excluded from coverage; content=33,210 | VERIFIED | `FACT ...records.content=33210`, `values.placeholder=83`; `--check` `placeholder_rows_unclustered n=83`; regex `[^\W\d_]` present |
| 5  | ROADMAP SC3 / HARM-06: wording grouping via embeddings | DEFERRED BY DECISION - human item | Not implemented, by D-07. Documented in README Next steps (line 87), Decisions D-07, Caveat, PROJECT.md. No torch/model dependency (`git diff c2cca33 -- pyproject.toml uv.lock` empty). See human verification |
| 6  | ROADMAP SC4 / HARM-04: File B review table (parquet + CSV) by user's impact definition, sized from 100-120 rec/h x 2-3 h, arithmetic shown, empty decision/comment | VERIFIED | `handicaps_review.parquet`: 300 rows, columns match plan, `decision`/`comment` empty in all 300 rows (counted 0 non-empty); CSV present with BOM (`--check`). TOP_K = int(120*2.5) = 300; `review.size_low=200`, `size_high=360` printed; README shows both arithmetic lines. Impact = pooled content-record count; `review_cluster_ids_1_to_n` OK |
| 7  | Seeded example records, <=5 per cluster, deterministic, whole records | VERIFIED (not opened) | `--check`: `records_per_cluster_is_min_5_n_total`, `records_year_pa_id_unique rows=1363`; shuffle(seed=SEED) present at harmonise.py:364. Records file deliberately not opened (governance). Determinism by two consecutive runs: records file regenerated twice (executor + this run) without check failure; not independently diffed. Minor: IN-02 correlated sampling across equal-size clusters |
| 8  | D-15 governance: record-level outputs never committed | VERIFIED | `git ls-files -- data '*.csv' '*handicaps_review*' '*review_leaders*'` lists only the two parquet files (value-level); `git check-ignore -v` shows `.gitignore:2:data/` for the records parquet and review CSV; `assert_local_only` at harmonise.py:163, `--check` `file_b_inside_data_root` OK. (WR-04: guard checks DATA_ROOT, not gitignore status - risk only if LINKING_LAB_DATA is mis-set) |
| 9  | HARM-03 lookup: committed, auditable, 300 rows, `llm_suggestion`, no runtime API, in census vocabulary | VERIFIED | `--check` `lookup_*` OK, `lookup_covers_review_leaders missing=0`; File A label totals over review clusters match summary (idiot 8,354; sindssyg 5,566; other 5,237; ...). Plausibility of the labels is a human judgement. WR-01: null/duplicate hole in load_lookup validation (hardening, not a current failure) |
| 10 | ROADMAP SC5 / HARM-05: README takes a reviewer EDA -> assumptions -> decisions -> conclusions -> next steps, figures traced to FACT lines | PARTIAL | All nine headings present, D-01..D-16 each cited, review arithmetic present, every one of the 26 FACT lines verbatim in README (my loop printed no "README lacks"). But line 83 is factually wrong (CR-02). Readability not performed (human item) |
| 11 | HARM-05 prohibitions: no "no handicap" reading of empties; no record content in README; no claim that HARM-06 was implemented | VERIFIED | README line 36 explicit; README contains only value strings and aggregates (no pa_id); line 87 states HARM-06 not built |

**Score:** 9/11 truths fully verified (truth 3 failed/partial, truth 10 partial; truth 5 is routed to human judgement and counted neither way).

### Review findings: effect on goal achievement

| Finding | Independently confirmed | Effect |
| ------- | ----------------------- | ------ |
| CR-01 digit-blind clustering | Yes: 1,023 values / 1,883 records / 80 of 300 review clusters under a leader with different digits (about 6% of the 31,598 records in review clusters); 1,061 / 1,921 across all content. "syg i 1 aar" -> "syg i 2 aar", conf 0.9091 | Does not break the bounded review file or its ranking (merged_spellings and confidence_min are visible to Asbjorn). It does weaken the "proposed standard" deliverable: applying File A as-is falsifies onset age / duration for these rows, and confidence reads as near-certain. It is the main substantive quality defect. Listed as a gap, not a goal failure, because the method is the user-locked D-03 and the fix is either a one-line guard or an explicit README caveat |
| CR-02 README misattributes single letters to 1801 | Yes: 1801 total 86 filled records, only "k" 41 and "m" 45; "s" 1,767 / "a" 1,421 / "d" 336 / "b" 282 are 1901 | Directly hits HARM-05 correctness. A reviewer would carry a false finding into the interview. Cheap sentence-level fix |
| WR-01..WR-05, IN-01..IN-03 | Not individually re-derived (WR-03 leading-dash raw spellings and IN-01 "Nothing is hard-coded" vs literal k-lists are consistent with what I read) | Hardening and polish; none is a must-have failure. Recommend triage after CR fixes. WR-02 (inherited category not marked) is worth a `category_inherited` column since Asbjorn cannot see which labels were inherited |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `task1_handicaps/harmonise.py` | Script with File A, File B, --check, --write-leaders, --lookup, `REF_THRESHOLD = 85` | VERIFIED | 546 lines; constants and functions present (lines 34, 39, 117, 163, 358, 364) |
| `task1_handicaps/outputs/handicaps_mapping.parquet` | File A, committed | VERIFIED | tracked, 3,416 x 16, reproduced exactly by a fresh run |
| `task1_handicaps/category_suggestions.parquet` | lookup | VERIFIED | tracked; validated by `--check` |
| `scripts/project_paths.py` | OUTPUTS_DIR | VERIFIED | File B resolves under `data/outputs/task1/` |
| `task1_handicaps/README.md` | Nine sections, Key figures | VERIFIED present, content defect CR-02 | 134 lines |
| `.planning/PROJECT.md` | Two rows "Implemented (Phase 2)" | VERIFIED | lines 86, 87; footer line 120 |

### Key Link Verification

| From | To | Status | Details |
| ---- | -- | ------ | ------- |
| harmonise.py | project_paths | WIRED | `import project_paths as pp` |
| harmonise.py | prepare_data.write_atomic | WIRED | atomic writes in use (run produced all files) |
| harmonise.py | category_suggestions.parquet | WIRED | `lookup_covers_review_leaders missing=0` |
| harmonise.py | census parquet | WIRED | run reads five years, FACT counts match plan probe (143,597 filled; 33,210 content) |
| README | harmonise.py FACT output | WIRED | all 26 FACT lines verbatim |
| README | eda.ipynb | WIRED | link on line 33 |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
| -------- | ---- | ------ | --------- | ------ |
| File A / File B | counts, clusters | polars scan of census parquet | yes | FLOWING |
| suggested_category | label | committed lookup joined on leader | yes, review clusters only (D-10) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Script regenerates outputs | `uv run python task1_handicaps/harmonise.py` | exit 0; 26 FACT lines; only `wrote` and FACT lines on stdout | PASS |
| Output validation | `... --check` | exit 0; 27 OK, 0 FAIL | PASS |
| README carries every FACT line | grep -qxF loop | no misses | PASS |
| File A reproducible | `git status --short task1_handicaps` after run | clean | PASS |
| Governance | `git ls-files` / `git check-ignore` | only 2 value-level parquets tracked; File B ignored | PASS |
| Dependencies unchanged | `git diff --quiet c2cca33 -- pyproject.toml uv.lock` | unchanged | PASS |
| Digit-guard probe (CR-01) | polars aggregate over File A (value strings and counts only) | 1,023 / 1,883 / 80 | FAIL (defect confirmed) |
| Letter-code year probe (CR-02) | File A per-year counts for s,a,d,b,k,m | s/a/d/b in 1901; 1801 only k,m (86 records) | FAIL (README wrong) |

### Probe Execution

SKIPPED: no `probe-*.sh` declared or present.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| HARM-01 | 02-01 | Automatic spelling normalisation | PARTIAL | Pipeline works; digit-blind merges (CR-01) include non-spelling variants |
| HARM-02 | 02-01 | File A: one row per normalised value, per-year freq, standard, confidence | SATISFIED | 3,416 rows; `--check` OK; reproducible |
| HARM-03 | 02-01 | Suggested category, marked as suggestion | SATISFIED | `category_source = llm_suggestion`; null outside review clusters. Label plausibility is human judgement |
| HARM-04 | 02-01 | File B review subset by impact, sized from brief, empty decision/comment, CSV | SATISFIED | 300 rows, arithmetic printed and in README, CSV with BOM |
| HARM-05 | 02-02 | Task 1 README | PARTIAL | Complete structure; one false finding (CR-02); readability unchecked |
| HARM-06 | 02-02 | Embedding grouping of wording variants | NEEDS HUMAN | Deliberately not implemented (D-07); documented deviation; REQUIREMENTS.md wording unchanged |

No orphaned requirements: REQUIREMENTS.md maps HARM-01..HARM-06 to Phase 2 and every ID is claimed by a plan (02-01: HARM-01..04; 02-02: HARM-05, 06). Note REQUIREMENTS.md traceability table still shows all as "Pending"; update when the user closes the phase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| task1_handicaps/harmonise.py | 111-126 | Fuzzy match with digits treated as letters | Blocker for proposed_standard quality (CR-01) | Wrong numbers at high confidence |
| task1_handicaps/README.md | 83 | Factually incorrect statement | Blocker for HARM-05 correctness (CR-02) | False finding |
| task1_handicaps/harmonise.py | 303-320 | Null/duplicate lookup rows pass validation | Warning (WR-01) | Hardening |
| task1_handicaps/harmonise.py | 422-431 | CSV cells beginning with "-" unescaped | Warning (WR-03) | Display corruption in Excel for 3,256 records' top spelling cells |
| task1_handicaps/harmonise.py | 159-170 | Guard checks DATA_ROOT not gitignore | Warning (WR-04) | One-way-door risk only under mis-set env |

No TBD/FIXME/XXX markers inspected beyond review; none surfaced in what I read.

### Human Verification Required

1. **HARM-06 acceptance.** Decide whether D-07's descoping satisfies the requirement ("Scope confirmed after EDA", confirmed scope = zero) and, if so, edit REQUIREMENTS.md HARM-06 and ROADMAP SC3 to say so; otherwise schedule an embedding pass. I have not silently passed or failed it.
2. **README + review CSV read-through** (Plan 02-02 Task 2 human check, not performed): README readable without code; CSV opens correctly with æ/ø/å; category suggestions plausible.
3. **Inherited-category and leading-dash cells** (WR-02, WR-03): judge whether to add `category_inherited` and CSV escaping before handing File B to Asbjorn.

### Gaps Summary

1. **CR-01 (partial, HARM-01/proposed standard).** Digit-blind clustering. Confirmed. Smallest fix that respects the "minimise degrees of freedom" preference: require equal digit sequences for a value to join a leader (no new tunable). This changes cluster counts, so rerun, regenerate the lookup via `--write-leaders` if leaders change, and refresh README figures. Alternative: keep D-03 and document the failure mode plus add a `digits_differ` column.
2. **CR-02 (partial, HARM-05).** One-sentence README correction plus a question about the 1901 letter codes. Also correct the same sentence in 02-01-SUMMARY.md.

The phase goal's two deliverables exist and function, are bounded and governance-safe. After these two fixes and the user's HARM-06 call, the phase can be closed.

---

_Verified: 2026-10-18T20:15:00Z_
_Verifier: Claude (gsd-verifier)_
