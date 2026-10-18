# Phase 1: Setup & EDA - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-18
**Phase:** 01-setup-eda
**Areas discussed:** Notebook format & names, Data layout & fetch, Task 2 age-noise probe, Task 1 EDA depth

---

## Notebook format & names

| Option | Description | Selected |
|--------|-------------|----------|
| Jupyter .ipynb | Familiar to reviewers; GitHub renders inline | ✓ |
| marimo (.py) | Clean diffs, HTML export, less familiar | |
| Jupytext .py + HTML export | Clean diffs, separate HTML | |

| Option | Description | Selected |
|--------|-------------|----------|
| Commit, aggregates only | Committed with outputs; no record-level rows | ✓ |
| Task 1 rendered, Task 2 stripped | DWI notebook outputs cleared | |
| Both stripped, render locally | Reviewers see code only | |

| Option | Description | Selected |
|--------|-------------|----------|
| Per-task folders | task1_handicaps/, task2_linking/ + shared fetch script | ✓ |
| By type | notebooks/, scripts/, docs/ | |

**User's choice:** Jupyter, commit with aggregate-only outputs, per-task folders.

---

## Data layout & fetch

| Option | Description | Selected |
|--------|-------------|----------|
| Expect files in data/raw | README documents sources; no download code | ✓ |
| Download Digidata + expect xlsx | Download automation | |

| Option | Description | Selected |
|--------|-------------|----------|
| Move into data/raw/ | Clean root | ✓ |
| Leave them in the root | Less churn | |

| Option | Description | Selected |
|--------|-------------|----------|
| All strings, cast later | Faithful copy; parse failures are findings | ✓ |
| Infer types | Faster, may silently null odd values | |

**User's choice:** Expect files, move root files into data/raw/, all-string parquet.

---

## Task 2 age-noise probe

| Option | Description | Selected |
|--------|-------------|----------|
| Unique-name anchors | Age diff on unique sex+full-name pairs; biased, lower bound | ✓ |
| Anchors + age heaping | Plus digit-preference check | |
| Distributions only | Shifted age pyramids | |

| Option | Description | Selected |
|--------|-------------|----------|
| Marginals + anchors | Per-census distributions + anchor agreement rates | ✓ |
| Marginals only | Distributions side by side | |

| Option | Description | Selected |
|--------|-------------|----------|
| Yes: pairs + anchor recall | Window-cost table ±1/±2/±3/±5 | ✓ |
| No, anchor spread is enough | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Brief profile | Household sizes, singleton share | ✓ |
| Skip for now | | |

**User's choice:** All recommended options.

---

## Task 1 EDA depth

| Option | Description | Selected |
|--------|-------------|----------|
| All columns, all strings | Streamed scan_csv → sink_parquet | ✓ |
| handicaps + a few context columns | Smaller, needs separate overview pass | |

| Option | Description | Selected |
|--------|-------------|----------|
| Two-step preview | raw → trivial norm → rapidfuzz clusters | ✓ |
| Trivial normalisation only | | |
| No preview | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Per year × geography | Fill rate + fully-empty units | ✓ |
| Per year only | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, mark capacity | Reference lines at 200/300/360 values | ✓ |
| Plain curve | | |

**User's choice:** All recommended options.

---

## Claude's Discretion

- Script/module names, notebook structure, plotting library
- Anchor name normalisation details, rapidfuzz scorer/threshold, geographic unit for missingness
- Read zip members directly vs temp extraction

## Deferred Ideas

- Age-heaping check per free/enslaved group (Task 2 README limitations)
- Digidata download automation
