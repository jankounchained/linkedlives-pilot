---
phase: 01-setup-eda
verified: 2026-10-18T19:00:00Z
status: human_needed
score: 5/5 roadmap success criteria verified (automated); 0 gaps
covered_files:
  - .githooks/pre-commit
  - .planning/phases/01-setup-eda/01-01-PLAN.md
  - .planning/phases/01-setup-eda/01-01-SUMMARY.md
  - .planning/phases/01-setup-eda/01-02-PLAN.md
  - .planning/phases/01-setup-eda/01-02-SUMMARY.md
  - .planning/phases/01-setup-eda/01-03-PLAN.md
  - .planning/phases/01-setup-eda/01-03-SUMMARY.md
  - .planning/phases/01-setup-eda/01-04-PLAN.md
  - .planning/phases/01-setup-eda/01-04-SUMMARY.md
  - README.md
  - pyproject.toml
  - scripts/check_notebook_outputs.py
  - scripts/prepare_data.py
  - scripts/project_paths.py
  - task1_handicaps/eda.ipynb
  - task2_linking/eda.ipynb
  - uv.lock
covered_digest: "v3:sha256:d7ceb83147a5de92f6ea98b754cbf6363918b8c472fb156a8dc20c661b876d49"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Skim the two committed notebooks for the three judgment-tier prohibitions (no Phase 1 decision stated or implied; empty handicaps never presented as 'no handicap'; column descriptions never presented as official; anchor figures always next to the lower-bound/bias caveat)"
    expected: "Every caveat sits next to the numbers it qualifies and no section reads as a decision"
    why_human: "Judgment-tier prohibitions (ADR-550 D3/D4). The verifier's read of the markdown cells found compliance, but that verdict is a non-authoritative LLM-judge result: unverified-prohibition, human review recommended."
  - test: "On a genuinely fresh clone (or a clean directory) run `uv sync --locked`, `git config core.hooksPath .githooks`, then `uv run python scripts/prepare_data.py --check` after placing the raw files"
    expected: "Environment builds from uv.lock; hook is active; --check prints OK for all six parquet files and the Guide"
    why_human: "The verifier ran `uv sync --locked` only in the existing environment (already in sync) and did not re-run the full conversion. Hook activation (core.hooksPath) is a per-clone step that cannot be proven from the repo contents."
---

# Phase 1: Setup & EDA Verification Report

**Phase Goal:** Both datasets are available locally as parquet in a reproducible environment. Each task's data is understood well enough for the user to settle the open approach decisions.
**Verified:** 2026-10-18
**Status:** human_needed (all automated checks pass; two small human confirmations remain, no gaps)
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths (ROADMAP success criteria, the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Fresh clone: `uv sync` gives a working env; fetch/convert writes parquet for the five census CSVs (only those + Release 2 Guide from the zip) and for the DWI xlsx | VERIFIED (see human item 2 for the fresh-clone leg) | `pyproject.toml` has 7 exact `==` pins, `requires-python >=3.14`, `.python-version` 3.14, `uv.lock` present; `uv sync --locked` -> "Checked 62 packages". `prepare_data.py --check` -> OK for `dwi_1846_1850.parquet` (83,414 rows, 22 cols, all String), `census_{1801,1850,1860,1880,1901}.parquet` (937,944 / 1,405,217 / 1,748,226 / 1,979,455 / 2,468,040 rows, all String, `handicaps` present; row counts match the plan's expected values) and the Guide PDF (7,631,397 bytes). Code reads exactly five census members + `GUIDE_MEMBER` via `ZipFile.open` to fixed filenames; no other zip member is touched. `data/raw/digidata_14001/` holds only the zip, curl.log and the Guide. |
| 2 | Raw and named record-level data never tracked by git | VERIFIED | `git ls-files -- data '*.xlsx' '*.zip' '*.pdf' '*.csv' '*.parquet'` prints nothing; tracked files are code, notebooks, planning docs, README, lock. `git check-ignore` confirms `data/` ignored. Repo root holds no data files (D-05 move done; files are under `data/raw/linking_lab/`). `.githooks/pre-commit` exists, blocks `data/*`, `*.xlsx`, `*.zip`, `*.pdf` and scans staged notebooks; `core.hooksPath` = `.githooks`. Scanner: `OK 2 notebook(s), 60 table output(s) scanned`; `--self-test` OK. |
| 3 | Rendered Task 1 notebook shows `handicaps` per census year (missingness, cardinality, frequency/coverage curve, messy-value examples) plus a column overview without asserting official definitions | VERIFIED | `task1_handicaps/eda.ipynb`: 21 code cells, all executed, 33 outputs, 1 image (coverage curve), 0 errors, no absolute paths. Sections: per-year fill/distinct (1), column overview per year with masked identifiers/free text (2), parish-level missingness (3), 3-level normalisation preview (4), top raw values / cluster variants (5), coverage curve with 200/300/360 lines (6). Independent recomputation from the parquet reproduced the notebook: fill counts 86 / 13,144 / 21,575 / 48,011 / 60,781 and fill rates 0.0001 / 0.0094 / 0.0123 / 0.0243 / 0.0246 (distinct 2 / 1832 / 1300 / 855 / 880 as stored; 1831 / 1298 / 852 / 877 after strip, consistent with the notebook counting "exactly as stored"). Markdown states storage is all-String and the overview is "what the data shows", not official types. |
| 4 | Rendered Task 2 notebook shows the DWI column overview and measures 1846->1850 stability of the free/enslaved flag, owner fields, surnames and age | VERIFIED | `task2_linking/eda.ipynb`: 20 code cells executed, 32 outputs, 1 image, 0 errors. Column overview per census, explicit casts with parse failures, `BIR_YEAR_EST` derived share (1.0, n=83,076), island derivation (0 unmapped), anchors, age-difference distribution, window-cost table, marginals per census/island, anchor agreement, status crosstab, household profile. Independent anchor rebuild with the documented normalisation gave 1381 anchors, equal to the notebook. Direct parquet check confirms the notebook's central finding: the free/enslaved flag is blank for all 39,523 1850 records and the owner surname field is filled for 0 of 1850 records (16,865 in 1846). The notebook reports this honestly (`both_filled.owner=0`, `agree.owner=NA`, crosstab collapses to one `n_1850_blank` column, explained in the cell text), so "stability" of flag and owner is measured as "absent in 1850", which is the true state of the data. |
| 5 | EDA states the facts behind each open decision (Task 1 method, LLM-for-categories, embedding scope, blocking window width); the user can decide; Phase 1 decides nothing | VERIFIED (judgment part flagged, see human item 1) | Task 1 closing section (a)-(e): method (4520 raw -> 3416 trivial -> 1732 clusters@85), LLM (singleton tail 2494 values = 1.74% of records), embedding scope (249 frequent / 1483 rare leaders), File B impact (coverage at 200/300/360: 0.967/0.971/0.973 trivial, 0.984/0.988/0.989 cluster-85), missingness caveat. Task 2 closing section (a)-(e): window table (pairs sex-only 853,817,263; +-1 38.4M, +-2 63.6M, +-3 88.7M, +-5 140.0M; anchor share 0.475/0.594/0.649/0.706), feature-weight hints, household potential (singleton share 0.111 / 0.026; median size 6 / 10), anchor bias, data-quality. All numbers are `FACT` lines computed in cells. Both notebooks end with "Phase 1 makes none of these decisions". PROJECT.md Key Decisions untouched by Phase 1 (decisions deferred to Phases 2/3 as the roadmap requires). |

**Score:** 5/5 truths verified, 0 present-but-behavior-unverified.

### Plan-level must-haves not already covered above

| Truth (plan) | Status | Evidence |
|---|---|---|
| Missing source: exit 2, names absolute path, points to README, no download code | VERIFIED (behavioural) | Ran with `LINKING_LAB_DATA` pointing at an empty scratch dir: `--only dwi` and `--only census` each exit 2, printed the missing absolute path and the README pointer, created nothing. grep finds no download/HTTP code. |
| Interrupted/overlapping run leaves a final parquet absent or complete (pid-suffixed temp, rename) | VERIFIED (behavioural) | Called `write_atomic` with a writer that creates a partial temp file then raises KeyboardInterrupt: final path absent, no leftover temp. Normal write: final present, no leftover, readable. Census path uses the same tmp/replace/cleanup pattern (read in code; not executed to avoid re-running the conversion). |
| Notebooks committed with outputs only after the human D-02 choice; hook not bypassed | VERIFIED (partial, documentary) | 01-04-SUMMARY records the user's `commit-with-outputs`; commit `6c53637` has the expected message; HEAD notebooks have 33 and 32 outputs; scanner OK. That the hook ran (no `--no-verify`) rests on the SUMMARY plus the scanner passing on the committed blobs. |
| README `## EDA notebooks` section | VERIFIED | README line 89. |

### Required Artifacts

| Artifact | Status | Details |
|---|---|---|
| `pyproject.toml`, `uv.lock`, `.python-version` | VERIFIED | Exact pins, 3.14, lock in sync |
| `scripts/project_paths.py` | VERIFIED | Wired: imported by prepare_data.py and both notebooks; `LINKING_LAB_DATA` override works (used in the missing-source test) |
| `scripts/prepare_data.py` (338-line scanner, 218-line converter) | VERIFIED | Substantive, `--check`/`--only` work, `sink_parquet` streaming, atomic writes |
| `scripts/check_notebook_outputs.py` | VERIFIED | Self-test OK; scans committed notebooks OK; wired into pre-commit |
| `.githooks/pre-commit` | VERIFIED | `bash -n` clean; active via `core.hooksPath` |
| `README.md` | VERIFIED | Sections Setup, Data (not in git), Prepare data, Data governance, EDA notebooks |
| `task1_handicaps/eda.ipynb`, `task2_linking/eda.ipynb` | VERIFIED | Executed, with outputs, Level 4: all figures trace to `scan_parquet` of the real parquet (independently reproduced) |

### Key Link Verification

| From | To | Status |
|---|---|---|
| prepare_data.py -> project_paths | WIRED (`import project_paths`) |
| notebooks -> project_paths -> parquet | WIRED (`import project_paths`, `scan_parquet`; outputs reproduce) |
| pre-commit -> check_notebook_outputs.py | WIRED |
| `core.hooksPath` -> `.githooks/` | WIRED locally (config value `.githooks`); per-clone step, see human item 2 |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Outputs valid | `uv run python scripts/prepare_data.py --check` | exit 0, 6 OK + guide OK | PASS |
| Lock in sync | `uv sync --locked` | no changes | PASS |
| Scanner on committed notebooks | `python3 -I scripts/check_notebook_outputs.py ...` | OK, 60 tables | PASS |
| Missing source | `LINKING_LAB_DATA=<empty> prepare_data.py` | exit 2 x2 | PASS |
| Atomic write on interrupt | `write_atomic` with failing writer | no partial final | PASS |

### Probe Execution

No probes declared; none found. SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|---|---|---|---|
| SETUP-01 | 01-01 | SATISFIED | pinned pyproject + uv.lock, `uv sync --locked` clean |
| SETUP-02 | 01-01 | SATISFIED | five census parquet + Guide, only those members read |
| SETUP-03 | 01-01, 01-04 | SATISFIED | DWI parquet 83,414 x 22; nothing data-like tracked; hook + scanner |
| EDA-01 | 01-02, 01-04 | SATISFIED | Task 1 sections 1, 4, 5, 6 |
| EDA-02 | 01-02, 01-04 | SATISFIED | Task 1 section 2 column overview, descriptive wording |
| EDA-03 | 01-03, 01-04 | SATISFIED | Task 2 overview + stability (incl. the finding that flag/owner are empty in 1850) |
| EDA-04 | 01-02, 01-03, 01-04 | SATISFIED | "Facts for open decisions" in both notebooks |

All seven IDs appear in plan frontmatter and in REQUIREMENTS.md (Phase 1 rows). No orphaned requirements: REQUIREMENTS.md maps no other ID to Phase 1. Note: the REQUIREMENTS.md checkboxes and traceability table still read "Pending", and ROADMAP.md still shows Phase 1 / plan checkboxes unticked in the phase list; that is bookkeeping for the orchestrator, not a code gap.

### Anti-Patterns Found

Scanned the Python scripts and notebook sources for TBD/FIXME/XXX/TODO/placeholder markers and stub returns: none found in files modified by the phase. No blockers.

| File | Pattern | Severity | Impact |
|---|---|---|---|
| `.githooks/pre-commit` | Blocks `data/*`, `.xlsx`, `.zip`, `.pdf` but not a stray `.parquet` or `.csv` outside `data/` (only `.gitignore` covers those; `.gitignore` does not list `*.parquet` per CONTEXT) | Info | Narrow residual risk if a parquet is written outside `data/`; no such file is tracked. Worth tightening in a later phase. |
| Scanner | Header-based heuristic; plain prints are only caught by human review (plan acknowledged) | Info | Human review already done at the 01-04 gate. |

### Deferred Items

None.

### Human Verification Required

1. **Judgment-tier prohibitions (flagged, non-authoritative LLM verdict).**
   Test: skim both notebooks' markdown/closing sections.
   Expected: no section states or implies a Phase 1 decision; empty `handicaps` is never read as "no handicap"; columns are never called official definitions; every anchor-based figure has the lower-bound/bias caveat adjacent.
   Why human: ADR-550 judgment tier. The verifier found compliance in every markdown cell it read, plus the user already reviewed the rendered HTML at the 01-04 D-02 gate, but that review's checklist targeted record-level leakage, not these statements. Recorded as `unverified-prohibition: human review recommended`, not as a failure.

2. **Fresh-clone reproducibility and hook activation.**
   Test: clean directory, `uv sync --locked`, `git config core.hooksPath .githooks`, place raw files, `uv run python scripts/prepare_data.py --check`.
   Expected: builds from the lock; hook active; all OK.
   Why human: only the existing environment and existing outputs were checked (full conversion deliberately not re-run); `core.hooksPath` is not carried by a clone.

### Gaps Summary

No gaps. Every roadmap success criterion is backed by files, executed notebook outputs and independent recomputation (fill counts/rates, anchor count, flag/owner emptiness in 1850, parquet shapes). The notable data finding for the user is that in the DWI file the free/enslaved flag and both owner fields are entirely empty in 1850, so they cannot serve as 1846<->1850 agreement features and the 1846->1850 status transition cannot be observed from the file; the notebook surfaces this correctly. Status is `human_needed` only because of the two confirmation items above.

---

_Verified: 2026-10-18_
_Verifier: Claude (gsd-verifier)_
