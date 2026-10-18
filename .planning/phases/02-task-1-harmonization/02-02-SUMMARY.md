---
phase: 02-task-1-harmonization
plan: 02
subsystem: documentation
tags: [readme, close-out, governance-audit, harm-06-deviation]

requires:
  - phase: 02-task-1-harmonization
    provides: "plan 02-01: harmonise.py, File A, category lookup, local File B, authoritative FACT lines"
provides:
  - "task1_handicaps/README.md: reviewer overview from EDA findings to next steps (HARM-05)"
  - "Documented HARM-06 deviation (embeddings descoped, D-07) in Next steps and the modern-meaning-bias caveat"
  - "PROJECT.md Key Decisions: the two pending Task 1 rows read Implemented (Phase 2)"
  - "Close-out audit: decisions predate the script, File A reproducible, no record-level file tracked"
affects: [04 root README and delivery zip, QUESTIONS.md]

actuals:
  tokens: 5000
  tasks: 2
  commits: 2
plan_head_before: 8f2cfeb9827ef54bef34a99b58f3085551fce48d
plan_head_after: 973b80557c62d31b2937d6821101210719fd7b5c

tech-stack:
  added: []
  patterns:
    - "Key figures block in the README is the verbatim FACT output of the script"

key-files:
  created:
    - task1_handicaps/README.md
  modified:
    - .planning/PROJECT.md

key-decisions:
  - "README quotes the script's FACT values (1,652 clusters; 95% at 284; 80% at 21), not the discussion-time figures in CONTEXT.md"
  - "HARM-06 is covered as a documented, reasoned descoping (D-07), not an implementation; REQUIREMENTS.md wording not edited"

patterns-established:
  - "Docs quote only value-level strings and FACT aggregates, never record content"

requirements-completed: [HARM-05, HARM-06]

coverage:
  - id: D1
    description: "task1_handicaps/README.md with the nine required headings, D-01..D-16, review arithmetic, HARM-06 deviation note, caveat and a Key figures block holding every FACT line of a fresh run"
    requirement: "HARM-05"
    verification:
      - kind: integration
        ref: "loop over fresh-run FACT task1.harmonise.* lines with grep -qxF against the README (separate commands, all found); heading, required-string and D-01..D-16 greps"
        status: pass
    human_judgment: false
  - id: D2
    description: "Reader-facing quality of the README (can Barbara and Olivia follow EDA to next steps without the code) and plausibility of LLM category suggestions"
    requirement: "HARM-05"
    verification: []
    human_judgment: true
    rationale: "Readability and historical plausibility are judgements; the plan's human-check (README top to bottom, open the review CSV in a spreadsheet) was not performed by the executor and is left for the end-of-phase review"
  - id: D3
    description: "HARM-06 embedding grouping documented as deliberately not implemented (D-07)"
    requirement: "HARM-06"
    verification:
      - kind: other
        ref: "grep for HARM-06, D-07 in README; PROJECT.md row 'HARM-06 embeddings descoped' present; pyproject.toml and uv.lock unchanged since c2cca33"
        status: pass
    human_judgment: true
    rationale: "Requirement wording says embedding grouping; the user must accept the deliberate deviation recorded in D-07"
  - id: D4
    description: "Close-out audit: c2cca33 ancestor of harmonise.py's first commit, File A reproduces, --check passes, only two parquet files tracked, nothing under data/, no CSV or File B tracked"
    verification:
      - kind: integration
        ref: "git merge-base --is-ancestor c2cca33 0dfb17d; fresh run leaves git status clean; harmonise.py --check; git ls-files listings; git diff c2cca33 HEAD -- pyproject.toml uv.lock empty"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-10-18
status: complete
---

# Phase 2 Plan 02: Task 1 README and Close-out Summary

**A 134-line Task 1 README takes a reviewer from EDA findings through decisions D-01..D-16 to next steps, with the HARM-06 embedding deviation and the modern-meaning-bias caveat stated, and a Key figures block that is the verbatim FACT output of harmonise.py; PROJECT.md records the Phase 2 outcomes and the governance audit passes.**

## Performance

- **Duration:** about 20 min
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- `task1_handicaps/README.md` with the nine required headings (How to run, Outputs, EDA findings, Assumptions, Decisions, Conclusions, Next steps, Caveat: modern-meaning bias, Key figures).
- All 26 `FACT task1.harmonise.*` lines of a fresh run appear verbatim in the Key figures block; prose figures come from them (1,652 clusters, 95.15% coverage at 300, 95% at 284 clusters, 80% at 21) and from the committed Phase 1 notebook (fill rates, parishes with nothing filled, 4,520 raw to 3,416 trivial values).
- Review-size arithmetic shown as `120 records/hour x 2.5 hours = 300` and `100-120 records/hour x 2-3 hours = 200-360`; the impact definition is quoted (D-11).
- HARM-06 stated as deliberately not implemented (D-07: modern-meaning bias, large torch/model dependency, extra cosine threshold), listed in Next steps and tied to the caveat.
- File B location and delivery stated: `data/outputs/task1/`, never committed, travels in the Phase 4 zip that includes `data/outputs/` and excludes `data/raw/` and `data/parquet/` (D-15, D-16).
- `pa_id` repeating across census years noted (identify records by `year` and `pa_id`).
- PROJECT.md: the two pending Task 1 rows now read "Implemented (Phase 2)"; footer updated; the "HARM-06 embeddings descoped" row is untouched.

## Task Commits

1. **Task 1: Task 1 README** - `e9e6369` (docs)
2. **Task 2: PROJECT.md outcomes and close-out audit** - `973b805` (docs)

**Plan metadata:** committed separately (docs: complete plan)

## Files Created/Modified

- `task1_handicaps/README.md` - Task 1 overview for reviewers
- `.planning/PROJECT.md` - two Key Decisions outcomes and the footer

## Decisions Made

- Quoted the script's FACT values, not CONTEXT.md's discussion-time ones, as the wave 1 summary instructed.
- Derived figures that have no FACT line (1,352 tail clusters = 1,652 - 300; 1,456 tail values = 3,333 - 1,877; about 4.9% tail record share = 1 - 0.9515; 76.9% placeholder share) are computed from FACT lines and labelled as reading-guide arithmetic, not new measurements. The category record counts (e.g. 3,065 records for "not a condition") were read from the committed value-level File A.

## Deviations from Plan

None - plan executed exactly as written. Two notes:

- The README is 134 lines, below the plan's 150-220 line guide. All required content is present; I kept it lean rather than padding.
- Compound shell verify commands (the plan's `<automated>` chains) were refused by the worktree harness. I ran their parts as separate commands with the same assertions: the FACT-line loop, heading greps, required-string greps, the D-01..D-16 loop, `git merge-base --is-ancestor c2cca33 0dfb17d`, `git ls-files` listings, `git diff c2cca33 HEAD -- pyproject.toml uv.lock` (empty) and `--check` (all OK). File A reproducibility was proven by a stronger test than frame equality: after a fresh run the committed `handicaps_mapping.parquet` showed no change in `git status` (byte-identical).

## Issues Encountered

None.

## Known Stubs

None.

## Threat Flags

None. The README quotes only value-level handicaps strings and aggregate FACT figures. The executor never opened `handicaps_review_records.*`, and no record rows or `pa_id` values were printed.

## Next Phase Readiness

- The human check from Task 2 is still open: read the README top to bottom and skim `data/outputs/task1/handicaps_review.csv` in a spreadsheet (æ, ø, å intact, 300 rows, empty decision and comment, plausible suggestions).
- The user decides whether the HARM-06 deviation needs a wording edit in REQUIREMENTS.md (not done here, per plan).
- Phase 4: link `task1_handicaps/README.md` from the root README and build the zip with `data/outputs/` included (D-16).
- The user writes QUESTIONS.md; the candidate questions are listed in the README's Next steps.

## Self-Check: PASSED

- `task1_handicaps/README.md` exists; commits `e9e6369` and `973b805` are on this branch.
- Fresh run leaves the committed File A unchanged; `--check` has no FAIL line; `git ls-files` shows exactly the two value-level parquet files and nothing under `data/`.

---
*Phase: 02-task-1-harmonization*
*Completed: 2026-10-18*
