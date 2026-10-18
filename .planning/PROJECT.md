# Linking Lab Pre-Interview Tasks

## What This Is

A lean micro-project answering the Linking Lab (Danish National Archives, HisPeR) pre-interview tasks for the data scientist / data manager positions: **Task 1 — explore and prepare the `handicaps` census variable for standardisation**, and **Task 2 — design and implement a simple method to link the 1846 and 1850 Danish West Indies censuses**. It is delivered as a single private git repo (code + small outputs, no raw data) to Bárbara Revuelta-Eugercios and Olivia Robinson, and serves as the basis for the technical part of the interview.

## Core Value

Show sound, transparent, source-critical problem solving on realistic HisPeR data within a ~3.5-hour budget — clear assumptions, decisions and conclusions matter more than completeness or polish.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Phase 1 — Context & EDA (before any planning of the task solutions)**
- [ ] Go through the context (brief, task PDF, Link-Lives Release 2 Guide) and interpret the columns of both datasets
- [ ] EDA of the Task 1 data: the `handicaps` variable in the 1801, 1850, 1860, 1880, 1901 `*__v1__cl.csv` censuses — missingness per year, cardinality, frequency/coverage, messiness
- [ ] EDA of the Task 2 data: `MF_census_1850_1846_cl.xlsx` — columns, missingness, cardinality, age noise, what changes 1846→1850 (free/enslaved flag, owner fields, surnames)
- [ ] One rendered EDA notebook per task (for sharing EDA; not the final product)

**Task 1 — Harmonization (~1.5h incl. its EDA)**
- [ ] Python script(s) producing the Task 1 outputs
- [ ] File A `handicaps_mapping.parquet`: one row per distinct normalised value, per-year frequency, proposed standard value with confidence
- [ ] File B `handicaps_review.parquet` (+ CSV export for historians): subset for Asbjørn chosen by impact; size grounded in the brief's numbers (100–120 records/hour, 2–3 hours/day); empty decision/comment columns
- [ ] Task 1 README (subdirectory): overview incl. EDA, assumptions, decisions, conclusions

**Task 2 — Linking (~1h incl. its EDA)**
- [ ] Python script implementing a hand-rolled linking approach (blocking → comparison features → score → 1:1 assignment → confidence)
- [ ] Household context used as a scoring signal (linking one household member raises the likelihood for co-residents)
- [ ] Links file in parquet: `pa_id_1846`, `pa_id_1850`, score, margin, confidence band
- [ ] Plausibility-based evaluation (no ground truth): age-difference distribution, link rates by sex/island/free-enslaved status, sample pairs per confidence band
- [ ] Task 2 README (subdirectory): overview incl. EDA, assumptions, decisions, conclusions, next steps

**Hand-in (~1h write-up)**
- [ ] Root `README.md`: how to run, what's where, links to task READMEs, one sentence on time spent, one line on AI use pointing to `.planning/`
- [ ] Reproducible environment (`uv`, `pyproject.toml`, `uv.lock`) and a data-fetch step (Digidata download, Excel → parquet); raw data never committed
- [ ] `QUESTIONS.md` — written by the user after we discuss the questions
- [ ] Draft cover email (link/zip, time spent, entry points)

### Out of Scope

- Snakefile / Snakemake pipeline — no real need for 4–5 short scripts; time is the scarcest resource
- Scalable linking design — 3-hour time box; scalability is a deliberate later concern, mentioned in next steps only
- Phonetic keys (Soundex/Metaphone) — overhead with unclear usefulness; abbreviations and mixed-language names make them unreliable here
- Splink / off-the-shelf linkage libraries — hand-rolled approach shows own design; Splink is a next step
- Standalone column dictionary file — shown in the EDA notebook only; we don't know the official column meanings, so we describe what the data shows rather than asserting definitions
- Excel output — artifacts are parquet (CSV export only where historians need it)
- Tests, CI, linter config, package layout — ceremony for a hand-in this size
- Full standardisation of `handicaps` — the brief asks for the first iteration only
- Manual review and LLM review layers for linking — described as design / next steps, not implemented
- Time-log table — a single sentence in the README is enough

## Context

- **Deadline:** submission by email to bre@rigsarkivet.dk and or@rigsarkivet.dk by 23:59 on 2026-10-18. Expected effort 3–4h total; the user received the files on Friday and had no chance to ask questions.
- **Time split:** Task 1 ~1.5h, Task 2 ~1h, write-up ~1h.
- **Outlook blocks `.py` attachments** — hand-in is a private git repo; later decide between inviting them or sending a zip.
- **Task 1 data:** Link-Lives Release 2 (Digidata 14001) zip, downloaded to `data/raw/digidata_14001/14001.zip` (1.52 GB, 10.6 GB unpacked). Needed: `Data/CSV/main_datasets/census_{1801,1850,1860,1880,1901}__v1__cl.csv` (~2 GB) and `Dokumenter/Link_Lives Release 2 Guide (2025).pdf`. Extract only these; convert to parquet once.
- **Task 2 data:** `MF_census_1850_1846_cl.xlsx` (sheet `MF_census_1850_1846_cl`, 83,414 rows: 43,891 from 1846, 39,523 from 1850; 22 columns incl. leftover index `Column1`). Delivered to Linking Lab by data partner FamilySearch, unstandardised; `pa_id` added to track records.
- **Early observations (Task 2):** surnames often empty for enslaved people; `BIR_YEAR_EST` likely = `EVENT_YEAR − AGE` (not independent evidence); emancipation in July 1848 falls between the censuses, so free/enslaved flag and owner fields are expected to change systematically; `FS_HOUSEHOLD_ID` enables household-level linking; odd values (e.g. birthplace "Foaner", empty flag on household heads) are questions for Olivia.
- **Task 1 caveat:** an empty `handicaps` value may mean the census did not ask, not "no handicap".
- **Audience:** Bárbara (sources, historical interpretation, record linkage literature) and Olivia (data, pipelines). They value transparent, replicable, ethical methods; their own stack is Python + Snakemake on Computerome HPC, CSV-based. Interview technical part in English.
- **Interview talking points:** kept outside the repo, low priority; revisit after deliverables exist.

## Constraints

- **Timeline:** ~3.5h of work, hard deadline 23:59 2026-10-18 — everything must be lean
- **Data governance:** raw data and named record-level outputs never enter git — not even the private repo (licence may not allow it); FamilySearch partner data is not ours to publish. Code lives in git; data doesn't. Committed outputs: `pa_id` + aggregates only.
- **Format:** parquet for all artifacts; CSV export only for historians; no Excel
- **Tech stack:** Python via `uv` (system Python 3.14, no global packages); polars + pyarrow; rapidfuzz for string similarity
- **Deliverable form:** scripts are the final product; notebooks are only for sharing EDA

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Phase 1 = context & EDA before planning task solutions | Columns and missingness not yet understood; approaches depend on it | — Pending |
| Private git repo; invite vs zip decided later | Data partner terms; Outlook blocks .py | Decided 2026-10-18: zipped repo built from the working tree; includes local `data/outputs/` (record-level File B) without committing it; excludes `data/raw/` and `data/parquet/` (Phase 2 D-16) |
| Commit `.planning/` and mention AI use in README | Transparency; mirrors the brief's own gen-AI footnote | — Pending |
| One EDA notebook per task | Each task's story self-contained | — Pending |
| Task READMEs = overview incl. EDA, assumptions, decisions, conclusions; root README links to them | One place per task for reviewers | — Pending |
| Task 1: two levels — spelling normalisation (automatic) vs category (suggested, historian decides) | Terminology of illness/disability changed over time; domain expertise stays at the core | Implemented (Phase 2): automatic trivial normalisation and leader clustering in task1_handicaps/harmonise.py; categories are LLM suggestions in task1_handicaps/category_suggestions.parquet; the historian decides |
| Task 1: File A (full mapping) + File B (review subset for Asbjørn) | Turns thousands of raw values into a bounded review task | Implemented (Phase 2): File A task1_handicaps/outputs/handicaps_mapping.parquet (committed, value-level); File B data/outputs/task1/handicaps_review and handicaps_review_records, parquet + CSV (local only, D-15; shipped in the Phase 4 zip, D-16) |
| File B selection "by impact" — user formulates the exact definition | User's call | Decided: impact = number of real-content records a cluster's decision standardises (pooled count, placeholders excluded); size fixed at one reviewer-day = 300 clusters (120/h × 2.5h); one row per cluster plus 5 seeded-random whole example records per cluster, kept local (Phase 2 D-11..D-15) |
| LLM-suggested categories for Task 1 | Decide after EDA, depending on how messy values are | Decided: yes, for the 300 File B clusters only; produced once by Claude, committed as an auditable lookup (no runtime API); historical source vocabulary, not modern groups. HARM-06 embeddings descoped to next steps (modern-meaning bias, heavy dependency, extra threshold) (Phase 2 D-07..D-10). HARM-06 closed with confirmed scope zero (D-18). |
| Task 1 approach (scripts, normalisation/clustering method) | Depends on EDA | Decided: minimise analyst degrees of freedom. Trivial normalisation + greedy leader clustering at fuzz.ratio ≥ 85 (EDA method); leader = proposed standard; confidence = ratio/100; only placeholder rule = no letters; no keyword lists, no prefix stripping, no misplaced-value flag (Phase 2 D-01..D-06) |
| Task 1: digit guard in leader clustering (amends the Task 1 approach, D-03) | fuzz.ratio treats digits like letters, so values with different onset ages or durations merged at high confidence (review CR-01: 1,061 values, 1,921 records; 'syg i 1 aar' became 'syg i 2 aar' at 0.91) | Decided 2026-10-18 (Phase 2 gap closure, D-17): a value joins only a leader whose digit runs are identical, otherwise it becomes a new leader; no parameter; trivial normalisation, visiting order and fuzz.ratio >= 85 stay as they are |
| Task 2: hand-rolled scoring (additive log-weights, given-name agreement weighted by name frequency) | Shows own design; transparent and explainable | — Pending |
| Task 2: blocking on sex + birth-year window; window width set from EDA age noise | Sex is nearly certain; sex alone ≈ 800M pairs; wide year window is not a hard gate | — Pending |
| Task 2: no phonetic key; name similarity is a score feature | Phonetic key would be load-bearing and silently lose links | — Pending |
| Task 2: island, birthplace, owner, surname are score features, not blocks | Block only on near-certain fields; movers lose points instead of being excluded | — Pending |
| Task 2: free/enslaved status is an analysis dimension, not a feature | Emancipation 1848 makes status and owner change by design | — Pending |
| Task 2: greedy 1:1 assignment; confidence from score + margin over second-best | Each person appears at most once per census; ambiguity is the real uncertainty | — Pending |
| Task 2: household context in scope (second scoring pass after base linking works) | Strong signal; base result first protects against running out of time | — Pending |
| Task 2 approach details beyond the above | Still open; finalise after EDA | — Pending |
| Not scalable by design | 3-hour time box; scalable design is future work with more time | — Pending |
| No named DWI record-level data in git — not even the private repo; committed outputs use `pa_id` + aggregates only; notebooks/samples showing names are rendered locally and gitignored | FamilySearch partner licence may not allow any redistribution; clarify with Olivia (candidate for QUESTIONS.md) | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-18 after Phase 2 gap closure (D-17..D-19)*
