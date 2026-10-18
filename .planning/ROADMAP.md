# Roadmap: Linking Lab Pre-Interview Tasks

## Overview

This is a lean, time-boxed path to a hand-in by 23:59 on 2026-10-18. Phase 1 sets up a reproducible environment and parquet data, then runs one EDA notebook per task. The EDA produces the facts for the approach decisions that are still open. Phase 2 (Task 1) turns the messy `handicaps` values into a full mapping and a bounded review file for the historians. Phase 3 (Task 2) links the 1846 and 1850 Danish West Indies censuses with a transparent, hand-rolled scoring method and evaluates the links for plausibility. Phase 4 packages everything for the reviewers. The total budget is about 3.5h. Each phase notes its share.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Setup & EDA** - Reproducible env, data as parquet, one rendered EDA notebook per task that yields the facts for the open decisions
- [ ] **Phase 2: Task 1 — Harmonization** - `handicaps` mapping (File A) plus an impact-ranked review subset for Asbjørn (File B), with a README
- [ ] **Phase 3: Task 2 — Linking** - Hand-rolled 1846→1850 DWI linking with score, margin, confidence band, plausibility evaluation and a README
- [ ] **Phase 4: Hand-in** - Root README, QUESTIONS.md, cover email draft; delivered before 23:59 2026-10-18

## Phase Details

### Phase 1: Setup & EDA

**Goal**: Both datasets are available locally as parquet in a reproducible environment. Each task's data is understood well enough for the user to settle the open approach decisions.
**Depends on**: Nothing (first phase)
**Requirements**: SETUP-01, SETUP-02, SETUP-03, EDA-01, EDA-02, EDA-03, EDA-04
**Time budget**: ~45 min. Keep setup minimal. The Task 1 EDA (~30 min) comes out of Task 1's ~1.5h and the Task 2 EDA (~15 min) out of Task 2's ~1h.
**Success Criteria** (what must be TRUE):
  1. On a fresh clone, `uv sync` gives a working environment, and the fetch/convert step writes parquet for the five `census_{1801,1850,1860,1880,1901}__v1__cl.csv` files (taking only those plus the Release 2 Guide from the zip) and for `MF_census_1850_1846_cl.xlsx`.
  2. Raw data and named record-level data are never tracked by git. `git status` / `git ls-files` show only code and small outputs.
  3. The rendered Task 1 EDA notebook shows `handicaps` per census year (missingness, cardinality, frequency/coverage curve, examples of messy values). It also has a column overview (type, % missing, cardinality, examples) that describes what the data shows without asserting official definitions.
  4. The rendered Task 2 EDA notebook shows the DWI column overview. It measures how stable the free/enslaved flag, owner fields, surnames and age are from 1846 to 1850.
  5. The EDA states the facts behind each open decision: Task 1 method, LLM-for-categories, embedding scope and blocking window width. The user can decide them from these facts. Phase 1 makes none of the decisions itself.

**Plans**: 3/4 plans executed

Plans:
**Wave 1**
- [x] 01-01-PLAN.md — uv env, D-05 data layout, prepare_data.py (DWI xlsx + 5 census CSVs + Guide to all-String parquet), notebook-output scanner and pre-commit data guard (wave 1, package-legitimacy checkpoint)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02-PLAN.md — Task 1 EDA notebook: handicaps per year, column overview, missingness by geography, normalisation preview, coverage curve, facts (wave 2)
- [x] 01-03-PLAN.md — Task 2 EDA notebook: DWI overview and casts, unique-name anchors and age noise, window-cost table, stability, households, facts (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 01-04-PLAN.md — D-02 one-way-door gate: human review of rendered outputs, then commit notebooks with outputs (wave 3, blocking-human checkpoint)

**UI hint**: no

### Phase 2: Task 1 — Harmonization

**Goal**: The historians get a first-iteration harmonisation of `handicaps`: a complete mapping from raw values to proposed standard values, and a bounded, impact-ranked review file Asbjørn can work through.
**Depends on**: Phase 1, plus the user's decisions after the EDA (Task 1 method, impact definition, LLM/embedding scope)
**Requirements**: HARM-01, HARM-02, HARM-03, HARM-04, HARM-05, HARM-06
**Time budget**: ~1h (what is left of Task 1's ~1.5h after its EDA in Phase 1)
**Success Criteria** (what must be TRUE):
  1. The decisions made after the EDA are recorded in PROJECT.md Key Decisions before the scripts are written: the Task 1 method, the impact definition (written by the user) and the LLM/embedding scope. The outputs follow these decisions.
  2. Running the Task 1 script(s) regenerates `handicaps_mapping.parquet`. It has one row per distinct, automatically spelling-normalised value (case, punctuation, whitespace, variant spellings) with per-year frequency, a proposed standard value, a confidence, and a category column clearly marked as a suggestion for historians.
  3. Values that differ in wording rather than spelling (e.g. "blind" vs "svagsynet") are grouped under the nearest frequent anchor, with cosine similarity as the confidence. This applies within the scope the user confirmed after the EDA. The output stays a suggestion, and the modern-meaning-bias caveat is documented.
  4. `handicaps_review.parquet` and its CSV export hold the review subset chosen by the user's impact definition. Its size is calculated from the brief's 100–120 records/hour × 2–3 hours/day, with the arithmetic shown. It has empty `decision` and `comment` columns.
  5. A reviewer can follow the Task 1 README (in its subdirectory) from EDA findings through assumptions, decisions, conclusions and next steps without opening the code.

**Plans**: TBD
**UI hint**: no

### Phase 3: Task 2 — Linking

**Goal**: The 1846 and 1850 DWI censuses are linked by a transparent, hand-rolled method. Each link has an explainable score and a confidence, and its plausibility can be judged without ground truth.
**Depends on**: Phase 1 (blocking window width from its EDA). Does not need Phase 2's outputs.
**Requirements**: LINK-01, LINK-02, LINK-03, LINK-04, LINK-05, LINK-06, LINK-07
**Time budget**: ~45 min (what is left of Task 2's ~1h after its EDA in Phase 1). Get the base linking working before the household pass.
**Success Criteria** (what must be TRUE):
  1. The blocking window width is recorded in PROJECT.md Key Decisions with the Phase 1 age-noise evidence. Candidate pairs come only from same-sex records inside that birth-year window, and the number of candidate pairs is reported.
  2. Running the Task 2 script writes `links.parquet` with `pa_id_1846`, `pa_id_1850`, `score`, `margin`, `confidence_band`. Each `pa_id` appears at most once (greedy 1:1).
  3. Each link's score can be explained from its features: given-name similarity weighted by name frequency, surname similarity when both surnames are present, |age difference − 4|, and birthplace / island / owner agreement.
  4. A household second pass raises the score for co-residents of household members who are already linked. The output shows how many links that pass added or changed compared with the base result.
  5. The plausibility evaluation and the Task 2 README show the age-difference distribution, link rates by sex / island / free-enslaved status, and sample pairs per confidence band. The README also covers method, assumptions, decisions, limitations and next steps (Splink, scalable blocking, LLM/manual review).

**Plans**: TBD
**UI hint**: no

### Phase 4: Hand-in

**Goal**: The reviewers receive a repo before the deadline that they can open, set up and run from the root README, and they can find each task's entry point straight away.
**Depends on**: Phase 2, Phase 3
**Requirements**: DOC-01, DOC-02, DOC-03
**Time budget**: ~1h write-up (also covers final polish of the task READMEs drafted in Phases 2–3)
**Success Criteria** (what must be TRUE):
  1. A reviewer can follow only the root README to set up (`uv sync`), fetch and convert the data, and reproduce the Task 1 and Task 2 outputs.
  2. The root README shows what is where and links both task READMEs. It has one sentence on time spent and one line on AI use that points to `.planning/`.
  3. `QUESTIONS.md` exists and was written by the user after discussing the questions. Claude does not write it.
  4. A cover email draft is ready to send to bre@rigsarkivet.dk and or@rigsarkivet.dk before 23:59 2026-10-18. It states the delivery form (repo invite or zip, the user's decision), time spent and the entry points.

**Plans**: TBD
**UI hint**: no

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Setup & EDA | 3/4 | In Progress | - |
| 2. Task 1 — Harmonization | 0/TBD | Not started | - |
| 3. Task 2 — Linking | 0/TBD | Not started | - |
| 4. Hand-in | 0/TBD | Not started | - |
