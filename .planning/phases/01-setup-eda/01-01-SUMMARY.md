---
phase: 01-setup-eda
plan: 01
subsystem: infra
tags: [uv, polars, parquet, fastexcel, zipfile, git-hooks, data-governance]

requires: []
provides:
  - "Reproducible uv environment: Python 3.14, exact pins, uv.lock"
  - "scripts/project_paths.py: worktree-safe data root and path constants (LINKING_LAB_DATA override)"
  - "scripts/prepare_data.py: DWI xlsx and 5 census CSVs (streamed from the Digidata zip) to all-String parquet, plus the Release 2 Guide PDF; --only and --check"
  - "scripts/check_notebook_outputs.py: stdlib record-level output scanner (--require-empty, --self-test)"
  - ".githooks/pre-commit data guard activated through core.hooksPath"
  - "data/parquet/census_{1801,1850,1860,1880,1901}.parquet and dwi_1846_1850.parquet (gitignored, main checkout)"
affects: [01-02, 01-03, 01-04, phase-02, phase-03]

actuals:
  tokens: 7000   # chars/4 over the changed source files (27898 chars); uv.lock excluded as generated
  tasks: 3
  commits: 2     # measured: git rev-list --count 8b4af21..585aaa0 (production commits; the SUMMARY docs commit follows)
plan_head_before: 8b4af21a321f96d39daef4380592ced9368d649f
plan_head_after: 585aaa0d87fd9df815f2112f4683169c96342968

tech-stack:
  added: [polars==2.0.0, pyarrow==26.0.0, rapidfuzz==3.14.6, fastexcel==0.21.0, matplotlib==3.11.2, ipykernel==7.4.0, nbconvert==7.17.2]
  patterns:
    - "All data paths via scripts/project_paths.py, resolved through the git common dir so worktrees reach the main checkout's data/"
    - "Atomic parquet writes: pid-suffixed temp file then Path.replace"
    - "Zip members streamed with ZipFile.open to fixed file names (no extract helpers, no member-derived paths)"
    - "Missing source: exit 2, absolute path named, README pointer"

key-files:
  created:
    - pyproject.toml
    - uv.lock
    - .python-version
    - scripts/project_paths.py
    - scripts/prepare_data.py
    - scripts/check_notebook_outputs.py
    - .githooks/pre-commit
    - README.md
  modified: []

key-decisions:
  - "Hook blocks data/ paths and .xlsx/.zip/.pdf only, not .parquet/.csv, because project governance allows committing pa_id-plus-aggregate parquet outputs"
  - "Census files keep polars default of empty CSV field = null; no other coercion (D-06)"
  - "Temp CSV directory placed inside data/raw/digidata_14001 (same disk; /tmp is RAM-backed)"

patterns-established:
  - "Script-printed output limited to paths, counts and dtypes; never rows"
  - "Notebook output check = scanner heuristic (pre-commit) plus human review at plan 01-04"

requirements-completed: [SETUP-01, SETUP-02, SETUP-03]

coverage:
  - id: D1
    description: "uv sync --locked builds a Python 3.14 env with exact pins for the seven packages"
    requirement: SETUP-01
    verification:
      - kind: other
        ref: "uv sync --locked (exit 0); pyproject.toml has ==-pinned polars, pyarrow, rapidfuzz, fastexcel, matplotlib, ipykernel, nbconvert"
        status: pass
    human_judgment: false
  - id: D2
    description: "prepare_data.py converts the five census CSVs (only those plus the Guide taken from the zip) to all-String parquet with expected row counts"
    requirement: SETUP-02
    verification:
      - kind: other
        ref: "uv run python scripts/prepare_data.py --check (5 census OK lines, rows 937944/1405217/1748226/1979455/2468040, all_string=True has_handicaps=True, guide OK)"
        status: pass
    human_judgment: false
  - id: D3
    description: "DWI xlsx converted to all-String parquet (83,414 x 22); git tracks no data; pre-commit hook rejects staged data paths and record-level notebook outputs"
    requirement: SETUP-03
    verification:
      - kind: other
        ref: "prepare_data.py --check --only dwi; python3 -I scripts/check_notebook_outputs.py --self-test; temp-repo hook test blocks data/x.txt; git ls-files data-pathspec empty; core.hooksPath=.githooks"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 01: Setup and Data Conversion Summary

**Pinned uv/Python 3.14 environment, a worktree-safe path module, one script that streams the five Link-Lives census CSVs plus the DWI xlsx into all-String parquet (zip-slip-safe, atomic writes), and a tracked pre-commit hook with a stdlib notebook-output scanner that keeps data and record-level outputs out of git.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-10-18T15:46:11Z
- **Completed:** 2026-10-18T15:49:42Z (code); SUMMARY committed after
- **Tasks:** 3 (Task 1 resolved as a checkpoint before dispatch; Tasks 2 and 3 executed)
- **Files modified:** 8 tracked files created (plus gitignored data outputs)

## Accomplishments

- `uv sync --locked` reproduces the environment. Resolved versions: polars 2.0.0, pyarrow 26.0.0, rapidfuzz 3.14.6, fastexcel 0.21.0, matplotlib 3.11.2, ipykernel 7.4.0, nbconvert 7.17.2 (all `==` pinned, `requires-python = ">=3.14"`, `.python-version` 3.14).
- D-05 layout done: the four root-level source files moved into the main checkout's `data/raw/linking_lab/`; the repo root holds no data files.
- `prepare_data.py` writes `dwi_1846_1850.parquet` and the five `census_<year>.parquet` files, all columns String, and extracts the Release 2 Guide next to the zip. Peak extra disk is one CSV at a time; no leftover CSV in `data/raw/digidata_14001`.
- Scanner and hook: `check_notebook_outputs.py --self-test` passes; the hook was exercised in a throwaway repo (blocks `data/x.txt` and `a.xlsx`, rejects a notebook with `pa_id`/`navn` headers, accepts a clean frequency table and a clean commit). Also checked against real polars HTML and text reprs (synthetic frame).

`--check` output (final run):

```
OK dwi_1846_1850.parquet rows=83414 cols=22 all_string=True
OK census_1801.parquet rows=937944 cols=29 all_string=True has_handicaps=True
OK census_1850.parquet rows=1405217 cols=31 all_string=True has_handicaps=True
OK census_1860.parquet rows=1748226 cols=34 all_string=True has_handicaps=True
OK census_1880.parquet rows=1979455 cols=46 all_string=True has_handicaps=True
OK census_1901.parquet rows=2468040 cols=48 all_string=True has_handicaps=True
OK guide Link_Lives Release 2 Guide (2025).pdf bytes=7631397
```

## Task Commits

| Task | Name | Status | Commit |
|------|------|--------|--------|
| 1 | Package legitimacy check before the first install | checkpoint:human-verify (blocking-human): approved by user via orchestrator on 2026-10-18; all seven packages installed as planned, none dropped or replaced | none (no files) |
| 2 | Tracer: uv env, D-05 layout, project_paths and DWI xlsx to parquet | done | `b650953` (feat) |
| 3 | Census conversion, Release 2 Guide, git data guard | done | `585aaa0` (feat) |

**Plan metadata:** docs commit for this SUMMARY follows (STATE.md and ROADMAP.md left to the orchestrator).

Tracer gate: interactive, `end-of-phase`, automated-only verify, so the tracer verify was re-run end-to-end after the Task 2 commit (passed) before expanding.

## Files Created/Modified

- `pyproject.toml`, `uv.lock`, `.python-version` - uv project, exact pins, Python 3.14
- `scripts/project_paths.py` - path constants, `main_checkout_root()` via `git rev-parse --path-format=absolute --git-common-dir`, `LINKING_LAB_DATA` override, CLI `data|raw|parquet|rendered`
- `scripts/prepare_data.py` - `require_sources()`, `write_atomic()`, `convert_dwi()`, `convert_census()`, `extract_guide()`, `check_outputs()`; flags `--only {dwi,census}`, `--check`
- `scripts/check_notebook_outputs.py` - `IDENTIFIER_COLUMNS`, `NAME_COLUMNS`, `RAW_COLUMNS`, rules A/B/C, `--require-empty`, `--self-test`
- `.githooks/pre-commit` (mode 100755) - blocks staged data paths, scans staged notebooks
- `README.md` - Setup, Data (not in git), Prepare data, Data governance

## Decisions Made

- Hook scope follows the plan (data/, .xlsx, .zip, .pdf); parquet and csv are not blocked by extension because the project allows committing `pa_id` plus aggregate parquet outputs; `data/` and `.gitignore` cover the record-level ones.
- Hook runs the scanner with `python3 -I` and prints scanner output only on failure.
- Scanner deduplicates identical violations (an `execute_result` carries both text/html and text/plain of the same table).
- A missing zip member (not only a missing zip) also exits with status 2 and a README pointer.

## Deviations from Plan

None - plan executed exactly as written. Minor additions inside the plan's intent: `_require_member` for missing zip members (D-04 clear failure), dedup of repeated violations, and a README sentence on cleanup of temp files.

**Total deviations:** 0 auto-fixed.

## Issues Encountered

- The worktree tooling refuses compound shell commands that mention git or run in another directory, so two plan-style verification one-liners (the `mktemp`-based missing-source check and the temp-repo hook check) were run as equivalent split commands, with the scratchpad as the temp directory. Same assertions, same results.
- `git config core.hooksPath .githooks` writes to the shared repo config, so it is now active in the main checkout too; the hook files reach the main checkout when this branch is merged.

## Authentication Gates

None. Task 1 was the package-legitimacy checkpoint, resolved by the user before this dispatch.

## Known Stubs

None.

## Threat Flags

None. All new surface (zip streaming, parquet writes, hook) is covered by T-01-01 to T-01-03 in the plan's threat model.

## User Setup Required

None - no external service configuration required. One-time per fresh clone: `git config core.hooksPath .githooks` (documented in README).

## Next Phase Readiness

- Phase 2 can read `data/parquet/census_<year>.parquet` (all String, `handicaps` present in all five); Phase 3 can read `data/parquet/dwi_1846_1850.parquet`.
- Plans 01-02 to 01-04 can import `project_paths` and use `check_notebook_outputs.py --require-empty` / default mode as the D-02 gate.
- The Guide PDF is at `data/raw/digidata_14001/Link_Lives Release 2 Guide (2025).pdf` for column definitions.
- No blockers.

## Self-Check: PASSED

- Files exist: pyproject.toml, uv.lock, .python-version, scripts/project_paths.py, scripts/prepare_data.py, scripts/check_notebook_outputs.py, .githooks/pre-commit, README.md (all FOUND).
- Commits `b650953` and `585aaa0` are ancestors of HEAD.
- Plan-level verification re-run: `uv sync --locked` ok, `prepare_data.py --check` seven OK lines and no FAIL, scanner `SELF-TEST OK`, `git ls-files` with data pathspecs empty.

---
*Phase: 01-setup-eda*
*Completed: 2026-10-18*
