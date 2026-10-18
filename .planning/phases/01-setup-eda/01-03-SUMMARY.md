---
phase: 01-setup-eda
plan: 03
subsystem: eda
tags: [polars, jupyter, nbconvert, matplotlib, dwi-census, record-linkage, data-governance]

requires:
  - phase: 01-setup-eda (plan 01)
    provides: "scripts/project_paths.py, dwi_1846_1850.parquet, check_notebook_outputs.py scanner and pre-commit hook"
provides:
  - "task2_linking/eda.ipynb: output-free Task 2 EDA notebook source (42 cells, 5 sections plus Facts for open decisions)"
  - "Executed copy and HTML review copy in the gitignored rendered dir (data/rendered/task2_eda.ipynb, task2_eda.html)"
  - "Computed FACT lines for blocking window width, feature-weight hints and household-pass potential (copied below)"
affects: [01-04, phase-03]

actuals:
  tokens: 9200   # chars/4 over task2_linking/eda.ipynb (36849 chars), the only changed file
  tasks: 3
  commits: 3     # measured: git rev-list --count e69003d..HEAD (production commits; the SUMMARY docs commit follows)
plan_head_before: e69003d2e11ffd8b49f87fef02caa62d477fc591
plan_head_after: 40408947c67909a40c3d4d0c0c6c4b60105d4776

tech-stack:
  added: []
  patterns:
    - "Notebook source committed output-free; executed copy rendered into the gitignored main-checkout rendered dir and scanned with check_notebook_outputs.py"
    - "FACT lines: every figure that feeds an open decision is printed from computed values through fact()"
    - "Window cost by aggregation: per (sex, birth year) counts joined and filtered, record pairs never materialised"
    - "Name-valued columns only as frequency examples with n >= 5; identifiers and owner names masked via MASK_EXAMPLE_COLUMNS"

key-files:
  created:
    - task2_linking/eda.ipynb
  modified: []

key-decisions:
  - "Island derived from inp_EVENT_PLACE (filled for every record) with substring rules croix / thomas / john-or-jan; zero unmapped"
  - "Blocking birth year is census_year - age, because inp_PR_BIR_YEAR_EST equals it for 100% of 83,076 checked records"
  - "Agreement with no comparable pairs (owner) is reported as NA with both_filled=0 instead of NaN"

requirements-completed: [EDA-03, EDA-04]

coverage:
  - id: D1
    description: "DWI column overview per census (type profile, int-parse share, % missing, cardinality, examples with n>=5, identifier and owner columns masked) plus explicit casts with parse-failure facts"
    requirement: EDA-03
    verification:
      - kind: other
        ref: "nbconvert --execute of task2_linking/eda.ipynb; grep FACT task2.rows.1846=43891, task2.rows.1850=39523, task2.biryear_is_derived_share=; scanner prints OK"
        status: pass
    human_judgment: false
  - id: D2
    description: "Stability 1846 to 1850 (marginals per census and island, anchor agreement, status crosstab), unique-name anchors with age-noise plot and lower-bound caveat, window-cost table, household profile"
    requirement: EDA-03
    verification:
      - kind: other
        ref: "nbconvert --execute; grep FACT task2.anchors=, task2.window.5.anchor_share=, task2.pairs.sex_only=, task2.agree.owner=, task2.household.singleton_share.1850=; image/png present; scanner prints OK"
        status: pass
    human_judgment: true
    rationale: "Bias caveats sit next to the numbers they qualify and no output may show an individual record; the scanner is a header heuristic, so a human reads the rendered HTML (plan 01-04 gate)"
  - id: D3
    description: "Closing Facts for open decisions section printing computed FACT lines for window width, feature-weight hints and household-pass potential, stating Phase 1 makes none of these decisions"
    requirement: EDA-04
    verification:
      - kind: other
        ref: "grep 'Phase 1 makes none of these decisions' and FACT lines in the rendered notebook"
        status: pass
    human_judgment: true
    rationale: "Whether the facts suffice to pick a blocking window width is a judgement (EDA-04, ROADMAP criterion 5)"

duration: 7min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 03: Task 2 EDA Notebook Summary

**Output-free `task2_linking/eda.ipynb` that profiles the DWI 1846/1850 census (casts, masked column overview, island rules), measures stability and age noise on 1,381 unique-name anchors, puts the sex-plus-birth-year blocking window cost on one table (38M to 140M pairs vs 854M sex-only), profiles households, and ends with computed Facts for open decisions that decide nothing.**

## Performance

- **Duration:** about 7 min (start time was not recorded at launch; estimated from the wave-1 completion time 15:49Z to 15:57Z)
- **Completed:** 2026-10-18T15:57:14Z
- **Tasks:** 3 (Task 1 tracer, Tasks 2 and 3 auto)
- **Files modified:** 1 tracked file created

## Accomplishments

- Tracer: DWI parquet to casts, masked column overview and island to rendered copy to scanner to output-free commit, verified end-to-end before expansion (`end-of-phase` mode, automated-only verify).
- Anchors (sex + normalised given name + normalised surname, unique in both censuses), age-difference plot with the lower-bound bias caveat directly after it, and the window-cost table computed by aggregation.
- Stability marginals, anchor agreement rates, status crosstab, household profile and the closing Facts section.
- Executed copy at `data/rendered/task2_eda.ipynb` plus `task2_eda.html` in the main checkout's gitignored rendered dir. The scanner prints `OK 1 notebook(s), 26 table output(s) scanned` on it, and `--require-empty` passes on the committed source.

## FACT lines (aggregates only, copied from the rendered notebook)

Data quality
```
FACT task2.rows.1846=43891
FACT task2.rows.1850=39523
FACT task2.age_parse_fail.1846=0
FACT task2.age_parse_fail.1850=0
FACT task2.age_missing.1846=243
FACT task2.age_missing.1850=95
FACT task2.bir_year_missing.1846=243
FACT task2.bir_year_missing.1850=95
FACT task2.census_year_parse_fail.1846=0
FACT task2.census_year_parse_fail.1850=0
FACT task2.biryear_is_derived_share=1.0
FACT task2.biryear_checked_n=83076
FACT task2.sex_blank.1846=742
FACT task2.sex_blank.1850=233
FACT task2.island_unmapped=0
```
(a) Blocking window width and anchors
```
FACT task2.anchors=1381
FACT task2.anchor_free_share_1846=0.8798
FACT task2.anchors_with_both_ages=1380
FACT task2.agediff.median=4.0
FACT task2.agediff.iqr=3.0
FACT task2.agediff.within1=0.4754
FACT task2.agediff.within2=0.5935
FACT task2.agediff.within3=0.6493
FACT task2.agediff.within5=0.7058
FACT task2.blocking_excluded.1846=949
FACT task2.blocking_excluded.1850=310
FACT task2.pairs.sex_only=853817263
FACT task2.window.1.pairs=38388149     (4.5% of sex-only; anchor_share 0.4754)
FACT task2.window.2.pairs=63557989     (7.4% of sex-only; anchor_share 0.5935)
FACT task2.window.3.pairs=88685994     (10.4% of sex-only; anchor_share 0.6493)
FACT task2.window.5.pairs=140001297    (16.4% of sex-only; anchor_share 0.7058)
```
The age-difference plot clips at -10..20; 157 anchors fall below -10 and 74 above 20. The spread is a lower bound on age noise for enslaved people (anchors are 88% free in 1846).

(b) Feature-weight hints
```
FACT task2.agree.island=0.8907          both_filled 1381
FACT task2.agree.birthplace=0.5676      both_filled 1339
FACT task2.agree.owner=NA               both_filled 0
FACT task2.agree.surname_raw=0.9957     both_filled 1381
FACT task2.surname_share.1846.free=0.913
FACT task2.surname_share.1846.enslaved=0.045
FACT task2.surname_share.1846.blank=0.424
FACT task2.surname_share.1850.blank=0.527
```
(c) Household-pass potential
```
FACT task2.household.singleton_share.1846=0.1113
FACT task2.household.singleton_share.1850=0.0261
FACT task2.household.median_size.1846=6.0
FACT task2.household.median_size.1850=10.0
FACT task2.household.no_id.1846=0
FACT task2.household.no_id.1850=0
```

## Observations worth the user's attention (facts, not decisions)

- The free/enslaved flag is blank for every 1850 record (the 1846 column has Free 16,686, Enslaved 24,844, blank 2,361). The owner fields are also empty in 1850 (owner fill share 0.0 on every island), so owner agreement has nothing to compare (NA). Consistent with the July 1848 emancipation, but it means status and owner cannot be linking features across the two censuses.
- `inp_PR_BIR_YEAR_EST` equals `census_year - age` in 100% of the 83,076 records where all three parse, so it is no independent evidence of age. Age is missing for 243 (1846) and 95 (1850) records.
- Only 1,381 anchors exist, 88% free. Their age difference is centred on the expected 4 (median 4.0, IQR 3.0), yet only 59% fall within +-2 and 71% within +-5; this is a lower bound for enslaved people.
- Raw surname agreement on anchors is 99.6%, birthplace (normalised) 56.8%, island 89.1%. Surname share is 4.5% for enslaved vs 91.3% for free in 1846.
- Households: 1850 households are larger (median 10 vs 6) and rarely singletons (2.6% vs 11.1%).

## Task Commits

1. **Task 1: Tracer, casts, column overview and island** - `fd10268` (feat)
2. **Task 2: Unique-name anchors, age-noise plot and window-cost table** - `746519d` (feat)
3. **Task 3: Stability marginals, anchor agreement, household profile and decision facts** - `4040894` (feat)

**Plan metadata:** docs commit for this SUMMARY follows (STATE.md and ROADMAP.md left to the orchestrator).

## Files Created/Modified

- `task2_linking/eda.ipynb` - Task 2 EDA notebook source, output-free. Symbols: `DWI`, `CENSUSES`, `WINDOWS`, `MIN_EXAMPLE_COUNT`, `FACTS`, `MASK_EXAMPLE_COLUMNS`, `filled()`, `fact()`, `print_facts()`, `normalise_name()`, `column_overview()`; derived columns `age`, `census_year`, `bir_year_est`, `sex`, `status`, `island`, `gn_norm`, `sn_norm`, `name_key`, `age_diff`, `birth_year`.

## Decisions Made

- `island` comes from `inp_EVENT_PLACE`, which is filled for every record (the `_SUP` column has 21 blanks). Rules: contains `croix`, `thomas`, or the word `john`/`jan`. No record is unmapped.
- Blocking uses `census_year - age` as birth year because the estimate column is fully derived.
- A field with no comparable anchors reports `NA` and `both_filled=0` rather than NaN.
- The notebook source was generated with a throwaway builder kept outside the repo (scratchpad); only the notebook is committed.

## Deviations from Plan

None - plan executed exactly as written. Small additions inside the plan's intent: `print_facts()` helper for the Facts section, a surname-share-by-status table (feeds feature-weight hints), `task2.anchors_with_both_ages`, `task2.household.no_id.<census>`, and the NA handling for empty fields.

**Total deviations:** 0 auto-fixed.

## Issues Encountered

- The worktree tooling refuses compound shell commands with variable substitution, so the plan's one-line render-and-check chain was run as equivalent separate commands with the literal rendered path `/data/repositories/linking_lab/data/rendered`. Same assertions, same results.
- The 1850 flag and owner fields are entirely empty, so the owner agreement and the 1846 x 1850 status crosstab carry little information (crosstab has a single `n_1850_blank` column). The notebook states this next to the tables.

## Human review still open

Task 3's `<human-check>` (read the rendered `data/rendered/task2_eda.html`, confirm no individual record, owner name or household id is visible, and that the Facts section suffices to pick a window width) is deferred to the plan 01-04 D-02 gate per `HUMAN_VERIFY_MODE=end-of-phase`. Only automated checks ran here: scanner on the rendered copy, `--require-empty` on the source, and construction (owner and id columns masked, anchors and households shown only as aggregates). The column overview does show full-name example values that occur at least 5 times in `inp_PR_NAME*` columns, as the plan allows; the reviewer should confirm this is acceptable.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. No new network, auth or file-access surface; the notebook reads the local parquet and writes only to the gitignored rendered dir.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-04 can run the human D-02 gate on `data/rendered/task2_eda.html` and commit outputs.
- Phase 3 can read the window-cost table and the FACT lines above to record the blocking window width.
- No blockers.

## Self-Check: PASSED

- `task2_linking/eda.ipynb` exists and is tracked; `--require-empty` passes.
- Commits `fd10268`, `746519d`, `4040894` are ancestors of HEAD.
- Rendered notebook contains all FACT keys required by the acceptance criteria, an `image/png` output, the phrase `lower bound`, and the sentence "Phase 1 makes none of these decisions; they are the user's after this EDA."; the scanner prints `OK` on it.

---
*Phase: 01-setup-eda*
*Completed: 2026-10-18*
