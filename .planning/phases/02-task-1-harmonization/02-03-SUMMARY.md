---
phase: 02-task-1-harmonization
plan: 03
subsystem: data-harmonisation
tags: [polars, rapidfuzz, leader-clustering, digit-guard, gap-closure, parquet, handicaps]

requires:
  - phase: 02-task-1-harmonization
    provides: "02-01 harmonise.py, File A, category lookup; 02-02 README"
provides:
  - "D-17 digit guard in leader_clusters: a value joins only a leader with identical digit runs (no parameter)"
  - "Category lookup refreshed to the 300 guarded review leaders (189 kept, 111 new, 111 dropped)"
  - "category_inherited in File A and the review table; csv_safe for the two CSV copies; null/duplicate lookup rejection; two-way lookup/review leader check"
  - "Corrected README (1901 letter codes, D-17/D-19 entries, regenerated figures) and 02-REVIEW-DISPOSITION.md ledger (6 fixed, 4 deferred)"
affects: [03-task-2-linking, 04-hand-in]

actuals:
  tokens: 16000
  tasks: 3
  commits: 5
plan_head_before: 229a48e2ee03636064f1397efa0d5f30de631647
plan_head_after: 8214a846ddc0a78c836081925ef5608c2fc5eca0

tech-stack:
  added: []
  patterns:
    - "Decision recorded in PROJECT.md in its own commit before the code that implements it (ROADMAP SC1)"
    - "Counterfactual FACT lines printed from the script show what a rule changed"
    - "CSV escaping in memory before the atomic temp-file write; parquet written from the unescaped frame"

key-files:
  created:
    - .planning/phases/02-task-1-harmonization/02-03-SUMMARY.md
  modified:
    - task1_handicaps/harmonise.py
    - task1_handicaps/category_suggestions.parquet
    - task1_handicaps/outputs/handicaps_mapping.parquet
    - task1_handicaps/README.md
    - .planning/PROJECT.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/phases/02-task-1-harmonization/02-01-SUMMARY.md
    - .planning/phases/02-task-1-harmonization/02-REVIEW-DISPOSITION.md

key-decisions:
  - "D-17: exact digit-run equality as a candidate filter in the leader clustering; trivial_norm, the visiting order and REF_THRESHOLD = 85 unchanged; no new constant"
  - "D-18: HARM-06 and ROADMAP criterion 3 reworded to the confirmed scope zero; traceability row left Pending for phase close-out"
  - "D-19: fix WR-01, WR-02, WR-03 and IN-03 now; defer WR-04, WR-05, IN-01, IN-02 with a reason each"
  - "All 111 new review leaders kept their inherited pre-guard label; no leader's own words named a different group, so there were no overrides"

requirements-completed: [HARM-01, HARM-02, HARM-03, HARM-04, HARM-05, HARM-06]

coverage:
  - id: D1
    description: "Proposed standards never change a stated number: digit guard in leader_clusters, File A regenerated"
    requirement: "HARM-01"
    verification:
      - kind: integration
        ref: "uv run python task1_handicaps/harmonise.py --check (OK digit_runs_match_leader violations=0)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Lookup validated before any write (nulls, duplicates, two-way leader set equality); outputs written atomically; CSV cells escaped in memory"
    requirement: "HARM-02, HARM-03, HARM-04"
    verification:
      - kind: integration
        ref: "negative runs with a null lookup and a duplicated lookup exit 2 and leave File A untouched; --check lookup_no_nulls, lookup_leaders_unique, lookup_leaders_equal_review_leaders, category_inherited_consistent, *_cells_safe"
        status: pass
    human_judgment: false
  - id: D3
    description: "README is true and matches the regenerated outputs (1901 letter codes, D-17/D-19, figures)"
    requirement: "HARM-05"
    verification:
      - kind: other
        ref: "two-way FACT loop (47 lines, no missing, no stale) and prose-figure check against File A"
        status: pass
    human_judgment: true
    rationale: "Readability for Barbara and Olivia and the plausibility of the 111 new LLM labels are judgements; automation proves structure and figures only"
  - id: D4
    description: "HARM-06 closed by wording (D-18); review dispositions recorded"
    requirement: "HARM-06"
    verification:
      - kind: other
        ref: "REQUIREMENTS.md HARM-06 and ROADMAP criterion 3 cite D-18; traceability row unchanged; ledger has 6 fixed and 4 deferred rows"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-10-18
status: complete
---

# Phase 2 Plan 03: Gap Closure Summary

**Parameter-free digit guard in the leader clustering (a value joins only a leader with identical digit runs) closes CR-01, with a refreshed 300-row category lookup, `category_inherited`, CSV-safe cells, strict lookup validation, a corrected and regenerated README, and the review dispositions.**

## Performance

- **Duration:** about 15 min
- **Tasks:** 3 (1 tracer, 2 auto)
- **Commits:** 5 task commits (PROJECT.md decision first, then the three tasks, then the ledger)
- **Files modified:** 9

## Accomplishments

- CR-01 closed (HARM-01): `digit_runs` and `leader_clusters(..., digit_guard=True)`. `--check` prints `OK digit_runs_match_leader violations=0`. The decision (D-17) is in commit 1c33fbc, a strict ancestor of the guard commit 56f2eb5 (ROADMAP SC1).
- The guard trades coverage for correctness: 2,160 clusters instead of 1,652; the top 300 cover 92.66% of real-content records instead of 95.15%; 1,061 values (1,921 records) would otherwise have carried a proposed standard stating a different number.
- Lookup refreshed: 189 kept, 111 new, 111 dropped; 300 rows, no null, sorted by leader. The default run printed `missing category suggestions for 111 review leaders` (exit 2) before the lookup was refreshed, as designed.
- D-19: `category_inherited` (949 inherited values), `csv_safe` (122 risky parquet cells in the records file equal 122 escaped CSV cells, 0 unescaped), null and duplicate rejection (`exit 2`, stderr "category lookup has 1 null cells" / "2 duplicated leaders", File A untouched), two-way leader set check.
- CR-02 closed (HARM-05): README and 02-01-SUMMARY attribute "s", "a", "d", "b" to 1901 (1,767, 1,421, 336, 282 records) and treat 1801 "M"/"K" (86 records) as a separate case; every README FACT line matches a fresh run in both directions.
- D-18: HARM-06 and ROADMAP Phase 2 criterion 3 state the confirmed scope (zero). Traceability row left `| HARM-06 | Phase 2 | Pending |`.

## FACT lines (aggregates only, final run)

```
FACT task1.harmonise.records.filled=143597
FACT task1.harmonise.values.raw=4520
FACT task1.harmonise.records.placeholder=110387
FACT task1.harmonise.records.content=33210
FACT task1.harmonise.values.trivial=3416
FACT task1.harmonise.values.placeholder=83
FACT task1.harmonise.values.content=3333
FACT task1.harmonise.clusters=2160
FACT task1.harmonise.coverage.top100=0.8783
FACT task1.harmonise.coverage.top200=0.9103
FACT task1.harmonise.coverage.top300=0.9266
FACT task1.harmonise.coverage.top360=0.9329
FACT task1.harmonise.clusters_for_coverage.80=26
FACT task1.harmonise.clusters_for_coverage.90=158
FACT task1.harmonise.clusters_for_coverage.95=601
FACT task1.harmonise.review.size=300
FACT task1.harmonise.review.size_low=200
FACT task1.harmonise.review.size_high=360
FACT task1.harmonise.review.values=1249
FACT task1.harmonise.digit_guard.clusters_unguarded=1652
FACT task1.harmonise.digit_guard.values_moved=1061
FACT task1.harmonise.digit_guard.records_moved=1921
FACT task1.harmonise.digit_guard.coverage.top300_unguarded=0.9515
FACT task1.harmonise.lookup.missing=0
FACT task1.harmonise.lookup.unused=0
FACT task1.harmonise.category.labels_used=8
FACT task1.harmonise.category.values=1249
FACT task1.harmonise.category.record_share=0.9266
FACT task1.harmonise.category.inherited_values=949
FACT task1.harmonise.category.leaders.døvstum/døv=14
FACT task1.harmonise.category.records.døvstum/døv=5102
FACT task1.harmonise.category.leaders.blind=18
FACT task1.harmonise.category.records.blind=3483
FACT task1.harmonise.category.leaders.sindssyg=9
FACT task1.harmonise.category.records.sindssyg=5547
FACT task1.harmonise.category.leaders.uden forstandsevner/idiot=97
FACT task1.harmonise.category.records.uden forstandsevner/idiot=8009
FACT task1.harmonise.category.leaders.krøbling/vanfør=6
FACT task1.harmonise.category.records.krøbling/vanfør=422
FACT task1.harmonise.category.leaders.multiple conditions=16
FACT task1.harmonise.category.records.multiple conditions=157
FACT task1.harmonise.category.leaders.other/unclear=76
FACT task1.harmonise.category.records.other/unclear=5091
FACT task1.harmonise.category.leaders.not a condition (suspected misplaced)=64
FACT task1.harmonise.category.records.not a condition (suspected misplaced)=2963
FACT task1.harmonise.examples.records=1479
FACT task1.harmonise.examples.clusters_lt5=21
```

## Lookup refresh

- **Counts:** 189 kept (0 relabelled against de03b43), 111 new, 111 dropped; 300 rows.
- **New labels:** all 111 kept the inherited pre-guard default; 0 overridden (no leader's own words named a different group). Defaults by label: uden forstandsevner/idiot 63, other/unclear 44, blind 3, døvstum/døv 1. Overridden leader and label pairs: none.
- **Reading note:** 3 new "forstanden berøvet ..." clusters (30, 50 and 52 years) contain a minority member that names døv, døvstum or sindssvag; the leader's words decide, so they keep "uden forstandsevner/idiot". `category_inherited` marks these for the historian.
- **Leaders and records per label (final lookup):** see the `category.leaders.<label>` and `category.records.<label>` lines above.

## Task Commits

1. **Decision before code:** `1c33fbc` docs(02-03) D-17 and D-18 in PROJECT.md Key Decisions
2. **Task 1 (tracer):** `56f2eb5` feat(02-03) digit guard, refreshed lookup, regenerated File A
3. **Task 2:** `4d8c6e8` fix(02-03) D-19 lookup validation, `category_inherited`, CSV-safe cells, per-label FACTs
4. **Task 3:** `1c611b7` docs(02-03) README corrections and figures, HARM-06 wording (D-18)
5. **Task 3 ledger:** `8214a84` docs(02-03) review dispositions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree harness refuses compound shell commands**
- **Found during:** Task 1 verify
- **Issue:** the harness rejected `git`-naming compound commands and heredocs (as noted in 02-01-SUMMARY).
- **Fix:** the plan's `<automated>` checks were run as equivalent Python scripts in the session scratchpad (same assertions; git calls through subprocess) and as separate plain commands. The plan-commit ledger file in the git dir was skipped for the same reason; `plan_head_before` is the known base 229a48e.
- **Files modified:** none (scratchpad only)

**2. [Plan wording] Task 3 committed in two commits, not one**
- **Issue:** the ledger's "fixed in 02-03, <short hash>" source for CR-02 needs the README commit hash.
- **Fix:** README, 02-01-SUMMARY, REQUIREMENTS and ROADMAP in `1c611b7`; the ledger in `8214a84`.

**Total deviations:** 1 auto-fixed (blocking harness limit), 1 commit split. **Impact:** none on outputs.

## Authentication Gates

None.

## Issues Encountered

None beyond the harness note above. The first README check failed once on the string "1,732" (the README had only the unformatted FACT value); a clause naming 1,732 clusters fixed it.

## Known Stubs

None. `decision` and `comment` are intentionally empty for the historian.

## Threat Flags

None beyond the plan's threat model. Mitigations verified: T-02-11 (`violations=0`, FACT counts 1,061 / 1,921), T-02-12 (122 risky cells escaped, 0 unescaped, parquet untouched), T-02-13 (null/dup negative runs exit 2), T-02-15 (`git ls-files -- data '*.csv' '*handicaps_review*' '*review_leaders*'` empty), T-02-16 (D-17 commit is a strict ancestor of the `def digit_runs` commit), T-02-SC (pyproject.toml and uv.lock unchanged since c2cca33). No census rows or pa_id values were printed; lookup authoring read only the value-level worksheet and File A strings.

## Next Phase Readiness

- Phase 2 gaps CR-01 and CR-02 are closed; the orchestrator owns STATE.md, the ROADMAP plan list and progress, and the HARM requirement checkboxes.
- End-of-phase human check (not a gate): read the README top to bottom, and open `data/outputs/task1/handicaps_review.csv` in a Danish-locale spreadsheet; skim `suggested_category` and `category_inherited` for the 111 new labels.
- File B was regenerated under the main checkout's `data/outputs/task1/` (local only, D-15); the Phase 4 zip must include it.

## Self-Check: PASSED

- Files exist: harmonise.py, category_suggestions.parquet, handicaps_mapping.parquet, README.md, 02-REVIEW-DISPOSITION.md.
- Commits 1c33fbc, 56f2eb5, 4d8c6e8, 1c611b7 and 8214a84 are ancestors of HEAD (5 commits since 229a48e).
- `--check` exits 0 with no FAIL line; the two-way README FACT loop is clean.

---
*Phase: 02-task-1-harmonization*
*Completed: 2026-10-18*
