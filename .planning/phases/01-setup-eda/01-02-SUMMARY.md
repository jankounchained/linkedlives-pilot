---
phase: 01-setup-eda
plan: 02
subsystem: eda
tags: [polars, rapidfuzz, matplotlib, jupyter, handicaps, data-governance]

requires:
  - phase: 01-setup-eda
    provides: "project_paths, census parquet files, check_notebook_outputs.py scanner (plan 01-01)"
provides:
  - "task1_handicaps/eda.ipynb: output-free Task 1 EDA notebook source (6 sections plus Facts for open decisions)"
  - "Gitignored executed copies data/rendered/task1_eda.ipynb and task1_eda.html (scanner clean)"
  - "Computed FACT lines for the Task 1 method, LLM-for-categories, embedding scope (HARM-06) and File B impact decisions, copied below"
affects: [01-04, phase-02]

actuals:
  tokens: 7700   # chars/4 over the one changed source file (30660 chars)
  tasks: 3
  commits: 3     # measured: git rev-list --count e69003d..ef0415e (production commits; the SUMMARY docs commit follows)
plan_head_before: e69003d2e11ffd8b49f87fef02caa62d477fc591
plan_head_after: ef0415e33bc981d7593a8eeb2421a116d567daa2

tech-stack:
  added: []
  patterns:
    - "Notebook source committed output-free; executed copy only in the gitignored rendered dir; scanner run on both (--require-empty on the source)"
    - "Every number in the Facts section comes from a computed variable through fact(), printed as a FACT line"
    - "Greedy leader clustering with rapidfuzz fuzz.ratio over trivially normalised values"

key-files:
  created:
    - task1_handicaps/eda.ipynb
  modified: []

key-decisions:
  - "Name columns (navn, ejernavn, ejendom_navn) are masked in the column-overview examples in addition to the plan's MASK_EXAMPLE_COLUMNS"
  - "alder_tal is stored in float format (e.g. '34.0'), so the explicit cast goes through Float64 and then checks for a whole number"
  - "The three cluster thresholds are alternatives, so drop_vs_previous_share compares each with the trivial level"

requirements-completed: [EDA-01, EDA-02, EDA-04]

coverage:
  - id: D1
    description: "Per-year handicaps rows, filled count, fill rate and raw distinct count (EDA-01)"
    requirement: EDA-01
    verification:
      - kind: other
        ref: "nbconvert --execute of task1_handicaps/eda.ipynb; grep FACT task1.fill_rate.<year> in rendered copy; scanner OK"
        status: pass
    human_judgment: false
  - id: D2
    description: "Column overview per year with parse profile, masked examples and no official definitions (EDA-02)"
    requirement: EDA-02
    verification:
      - kind: other
        ref: "rendered copy contains type_profile tables for all five years, 'not shown' masks, scanner OK"
        status: pass
    human_judgment: true
    rationale: "Whether masking is sufficient and the overview reads as description rather than definition is a reader judgement (plan 01-04 human gate)"
  - id: D3
    description: "Missingness by year and geography with the not-asked / not-transcribed caveat"
    requirement: EDA-01
    verification:
      - kind: other
        ref: "FACT task1.empty_parish_share.<year> in rendered copy; scanner OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Three-level normalisation preview, messy-value tables and coverage curve with review-capacity lines"
    requirement: EDA-01
    verification:
      - kind: other
        ref: "FACT task1.distinct.*, task1.clusters.ratio*, task1.coverage.*; image/png present in rendered copy; scanner OK"
        status: pass
    human_judgment: true
    rationale: "Value-frequency tables show raw handicaps strings at any count; a human must confirm no output reads as a person's record (D-02, plan 01-04)"
  - id: D5
    description: "Facts for open decisions section computed from the data, with no decision made (EDA-04)"
    requirement: EDA-04
    verification:
      - kind: other
        ref: "rendered copy has FACT lines per decision and the closing sentence; scanner OK"
        status: pass
    human_judgment: true
    rationale: "Whether the facts suffice to decide is a judgement (EDA-04, ROADMAP criterion 5)"

duration: 20min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 02: Task 1 EDA Notebook Summary

**An output-free `task1_handicaps/eda.ipynb` that profiles `handicaps` across the five censuses (fill rate, parish emptiness, a raw/trivial/rapidfuzz-cluster normalisation preview, a coverage curve against review capacity) and closes with computed FACT lines for the four open Task 1 decisions, none of which it makes.**

## Performance

- **Duration:** about 20 min
- **Tasks:** 3 (tracer plus two auto), all committed separately
- **Files modified:** 1 tracked file (`task1_handicaps/eda.ipynb`); executed copies in the gitignored rendered dir

## Accomplishments

- Section 1 to 6 plus "Facts for open decisions" render end to end in about 7 seconds (lazy polars scans, a few thousand pooled values for clustering).
- Rendered copy passes `check_notebook_outputs.py` (34 table outputs scanned, OK); the committed source passes `--require-empty`.
- The notebook states the caveats next to the numbers: empty may mean not asked or not transcribed (not "no handicap"); column descriptions describe the data, not official definitions; clustering is a preview with scorer `fuzz.ratio` and thresholds 80/85/90.
- Rendered review copies (local only): `/data/repositories/linking_lab/data/rendered/task1_eda.ipynb` and `task1_eda.html`.

## FACT lines (aggregates, copied from the rendered notebook)

Per year (1801 / 1850 / 1860 / 1880 / 1901):

```
rows_n:                 937944 / 1405217 / 1748226 / 1979455 / 2468040
fill_rate (handicaps):  0.0001 / 0.0094 / 0.0123 / 0.0243 / 0.0246
raw_distinct_n:         2 / 1832 / 1300 / 855 / 880
empty_parish_share:     0.9994 / 0.4304 / 0.3 / 0.3011 / 0.3103
alder_tal_parse_fail:   0 / 0 / 0 / 0 / 0
alder_tal_fractional:   18 / 592 / 257 / 40074 / 1
```

(a) Task 1 method, normalisation levels:

```
FACT task1.distinct.raw=4520
FACT task1.distinct.trivial=3416
FACT task1.drop.trivial_vs_raw=0.2442
FACT task1.clusters.ratio80=1472
FACT task1.clusters.ratio85=1732
FACT task1.clusters.ratio90=2049
FACT task1.drop.ratio80_vs_trivial=0.5691
FACT task1.drop.ratio85_vs_trivial=0.493
FACT task1.drop.ratio90_vs_trivial=0.4002
```

(b) LLM-for-categories (values a categoriser would face, singleton tail):

```
FACT task1.level2_values=3416
FACT task1.clusters.ratio85=1732
FACT task1.multi_year_values=307
FACT task1.singleton_values=2494
FACT task1.singleton_record_share=0.0174
```

(c) Embedding scope (HARM-06), cluster-85 leaders by pooled count:

```
FACT task1.leaders85.frequent=249
FACT task1.leaders85.rare=1483
```

(d) File B impact, coverage of filled records by the top k values (k = 200 / 300 / 360):

```
FACT task1.coverage.trivial.200=0.9667
FACT task1.coverage.trivial.300=0.971
FACT task1.coverage.trivial.360=0.973
FACT task1.coverage.cluster85.200=0.9843
FACT task1.coverage.cluster85.300=0.9875
FACT task1.coverage.cluster85.360=0.9888
```

Reading aid (no decision): filled `handicaps` is under 2.5 percent of rows in every year, and 1801 has 86 filled values in 937,944 rows, so most records have nothing to normalise. About 3,400 trivial-level values cover 97 percent of the filled records within the top 200; the long tail is 2,494 values seen once, 1.7 percent of filled records.

## Task Commits

1. **Task 1 (tracer): census parquet to per-year table to rendered copy to scanner to output-free commit** - `60281cc` (feat)
2. **Task 2: column overview per year and missingness by geography** - `01f6b2c` (feat)
3. **Task 3: normalisation preview, messy values, coverage curve, Facts for open decisions** - `ef0415e` (feat)

**Plan metadata:** docs commit for this SUMMARY follows (STATE.md and ROADMAP.md left to the orchestrator).

Tracer gate: interactive, automated-only `<verify>`, so the tracer verify chain was run end to end (it passed) before expansion; expansion tasks then re-ran the full chain each time.

## Files Created/Modified

- `task1_handicaps/eda.ipynb` - Task 1 EDA notebook source, committed without outputs. Symbols: `YEARS`, `LF`, `MIN_EXAMPLE_COUNT`, `CAPACITY_LINES`, `CLUSTER_THRESHOLDS`, `REF_THRESHOLD`, `FACTS`, `MASK_EXAMPLE_COLUMNS`, `filled()`, `trivial_norm()`, `fact()`, `column_overview()`, `leader_clusters()`.

## Decisions Made

- Masked name columns (`navn`, `ejernavn`, `ejendom_navn`) in the overview examples as well, so no name is shown even as a frequent value.
- `drop_vs_previous_share` for the three cluster settings is measured against the trivial level, because they are alternatives, not a sequence. The notebook says so.
- Coverage is computed over filled records only; the notebook says empty records are outside the curve.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `alder_tal` integer cast rejected nearly every value**
- **Found during:** Task 2
- **Issue:** `alder_tal` is stored as float-formatted text (for example "34.0"), so the plan's integer cast reported about 99.9 percent parse failures, a misleading finding.
- **Fix:** The explicit cast now goes through Float64 and checks for a whole number. `int_parse_share` and `task1.alder_tal_parse_fail.<year>` use this; a new `task1.alder_tal_fractional.<year>` fact counts numeric values with a fractional part (for example 40,074 in 1880). The notebook explains the format.
- **Files modified:** task1_handicaps/eda.ipynb
- **Verification:** rendered facts show 0 non-numeric values in every year; scanner OK.
- **Committed in:** `01f6b2c`

**2. [Rule 2 - Missing critical] Name columns masked in overview examples**
- **Found during:** Task 2
- **Issue:** The plan's `MASK_EXAMPLE_COLUMNS` leaves `navn`, `ejernavn` and `ejendom_navn` unmasked, so frequent full names could appear in the examples column (CLAUDE.md data-governance rule, D-02).
- **Fix:** Added the three name columns to the mask set.
- **Committed in:** `01f6b2c`

**3. [Rule 3 - Blocking] Verify chain split into plain commands**
- **Found during:** Task 1
- **Issue:** The worktree tooling refused the single compound command that uses `R="$(uv run ...)"`. The same steps were run as separate commands with the literal rendered path (`/data/repositories/linking_lab/data/rendered`, as printed by `project_paths.py rendered`). Same assertions, same results.

---

**Total deviations:** 3 (1 bug, 1 missing critical, 1 blocking/process)
**Impact on plan:** No scope change. The `alder_tal` fix prevents a misleading D-06 finding.

## Issues Encountered

- Added a small extra column `no_geo_rows_n` to the parish table (records with no geography at all), because the parish unit counts otherwise silently skip them.
- Debug probes were limited to aggregates (value counts of `alder_tal`, string-length statistics of distinct `handicaps` values: longest value is 52 characters, 246 distinct values exceed 40 characters, covering 359 records). No record-level rows were printed.

## Known Stubs

None.

## Threat Flags

None. No new network, auth or file surface; no new dependencies (pyproject.toml and uv.lock untouched).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-04 can run the D-02 human gate on `/data/repositories/linking_lab/data/rendered/task1_eda.html`. One point for that review: sections 5a and 5b show raw `handicaps` strings at any count (as the plan specifies), so the rare variants in 5b deserve a look for anything person-specific before outputs are committed.
- The user decisions on Task 1 method, LLM-for-categories, embedding scope and File B impact are open and can be taken from the FACT lines above; Phase 1 makes none of these decisions.

## Self-Check: PASSED

- `task1_handicaps/eda.ipynb` exists; commits `60281cc`, `01f6b2c`, `ef0415e` are ancestors of HEAD.
- Plan-level verification re-run on the final source: nbconvert execute OK, html written, scanner on the rendered copy prints OK (34 tables), `--require-empty` on the source exits 0, all listed FACT keys and one `image/png` present, closing sentence present, section order 1, 2, 3, 4, 5, 6, Facts.

---
*Phase: 01-setup-eda*
*Completed: 2026-10-18*
