# Phase 1: Setup & EDA - Context

**Gathered:** 2026-10-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers:
- a reproducible `uv` environment;
- a fetch/convert script that turns locally provided source files into parquet (5 Link-Lives census CSVs + the DWI xlsx);
- one rendered Jupyter EDA notebook per task.

The notebooks surface the facts the user needs for the open decisions: Task 1 method, LLM-for-categories, embedding scope (HARM-06), the File B impact definition, and the Task 2 blocking window width. **Phase 1 makes none of these decisions itself.** Each notebook ends with a short "Facts for open decisions" section.

Time budget: ~45 min total (setup minimal, Task 1 EDA ~30 min, Task 2 EDA ~15 min). Requirements: SETUP-01..03, EDA-01..04.

</domain>

<decisions>
## Implementation Decisions

### Notebooks & governance
- **D-01:** EDA notebooks are Jupyter `.ipynb`. GitHub renders them inline with outputs, so no separate HTML export is needed.
- **D-02:** Both notebooks are committed **with outputs**, under a strict rule: **no record-level rows**. Allowed: value-frequency tables (e.g. top `handicaps` strings with counts, top given names with counts), summary statistics, distributions and plots. Not allowed: any cell output that shows individual records (names next to ages, owners, households, `pa_id` rows, `.head()` of the DWI frame, etc.). Before committing, check the rendered outputs for record-level content. — **Reversibility:** one-way — once a notebook with record-level FamilySearch data is committed and the repo is shared/pushed, removing it needs a git history rewrite and may already breach the partner licence.
- **D-03:** Repo layout is per task. `task1_handicaps/` holds its `eda.ipynb`, later scripts and README; `task2_linking/` holds the same. The shared fetch/convert script sits at the root (e.g. `scripts/fetch_data.py` or `prepare_data.py`, Claude's choice of name).

### Data layout & fetch
- **D-04:** No download code. The fetch/convert script expects source files to already be in `data/raw/`, and the README documents where they come from: Digidata 14001 for Link-Lives Release 2; the DWI xlsx was emailed by Linking Lab. The script fails with a clear message if a file is missing.
- **D-05:** Root-level source files move under `data/raw/`. `MF_census_1850_1846_cl.xlsx`, `Linking_Lab_opgave.zip`, `Linking_Lab_brief.pdf` and `Pre_interview_tasks_for_data_scientists_datamanagers_2026.pdf` go to `data/raw/linking_lab/`. The Digidata zip stays at `data/raw/digidata_14001/14001.zip`, and the Guide PDF is extracted next to it. Everything under `data/` stays gitignored (already covered by `.gitignore`).
- **D-06:** Parquet conversion keeps **all columns as strings (Utf8)** and coerces nothing. The EDA and later scripts cast explicitly and report parse failures (e.g. non-numeric ages) as findings.
- **D-07:** Census CSVs are converted with **all columns**, streamed via polars (`scan_csv` → `sink_parquet`, or equivalent low-memory path), reading straight from the zip or from a temporary extraction of only the 5 needed members. Only `census_{1801,1850,1860,1880,1901}__v1__cl.csv` and the Release 2 Guide are extracted. The full ~10.6 GB is never unpacked.

### Task 2 EDA (DWI 1846 ↔ 1850)
- **D-08:** Age noise is estimated from **unique-name anchors**: records where sex + normalised full name (given + surname) is unique within each census and present in both. The notebook shows the distribution of `age_1850 − age_1846` for the anchors. It states clearly that the anchors are biased toward people with surnames (mostly free people), so the spread is a **lower bound** on age noise for enslaved people.
- **D-09:** Stability 1846→1850 is measured two ways: (a) **marginals** per census and island, i.e. the share with a surname, the free/enslaved distribution, owner-field fill rate and birthplace fill rate; (b) **agreement rates on the anchors** for surname, owner, island and birthplace. Part (b) informs feature weights in Phase 3. Same bias caveat as D-08.
- **D-10:** A **window-cost table** for birth-year windows ±1, ±2, ±3, ±5 shows the number of candidate pairs (blocking on sex + window) and the share of anchors kept at each width. This puts the window trade-off on one screen. The user picks the width afterwards.
- **D-11:** A **brief household profile** (`FS_HOUSEHOLD_ID`): household size distribution per census and island, plus the share of singletons. This shows how much the LINK-04 household pass can add.

### Task 1 EDA (`handicaps`)
- **D-12:** **Two-step normalisation preview.** Distinct-value counts are shown at three levels: raw → trivially normalised (lowercase, strip punctuation and whitespace) → rapidfuzz near-duplicate clusters at a loose threshold. This is preview only. The real normalisation lives in the Phase 2 script. The size of each drop is the evidence for the Task 1 method and embedding/LLM decisions.
- **D-13:** **Missingness per year × geography.** The notebook shows fill rate per census year, plus the share of parishes/districts (whatever geographic unit the data offers) where `handicaps` is entirely empty. Fully empty units back the caveat that empty may mean "not asked / not transcribed" rather than "no handicap".
- **D-14:** **The coverage curve marks review capacity.** The curve plots distinct normalised values ranked by frequency against the cumulative share of filled records. It has reference lines at 200, 300 and 360 values (100–120 records/h × 2–3 h) and prints coverage at each line. This informs, but does not set, the user's File B impact definition (Phase 2).

### Claude's Discretion
- Exact script/module names, notebook cell structure and plotting library (keep dependencies minimal; matplotlib or polars' built-in plotting are both fine).
- Name normalisation used for anchors: lowercase, strip accents and punctuation, collapse whitespace. Keep it simple and documented.
- Rapidfuzz scorer and loose threshold for the D-12 cluster count. State the chosen values in the notebook.
- Which geographic column to use for D-13, based on what the census files actually contain.
- Whether the converter reads members directly from the zip or extracts them to a temp dir first.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project planning
- `.planning/PROJECT.md` — constraints (data governance, parquet, uv/polars/rapidfuzz), Key Decisions table, early Task 2 observations (BIR_YEAR_EST derived from age, emancipation 1848, empty surnames for enslaved people)
- `.planning/REQUIREMENTS.md` — SETUP-01..03, EDA-01..04 wording
- `.planning/ROADMAP.md` §"Phase 1: Setup & EDA" — success criteria and time budget

### Source documents (local only, gitignored. Paths after the D-05 move)
- `data/raw/linking_lab/Pre_interview_tasks_for_data_scientists_datamanagers_2026.pdf` — the task statement (Task 1 `handicaps`, Task 2 linking, review capacity numbers)
- `data/raw/linking_lab/Linking_Lab_brief.pdf` — Linking Lab / HisPeR context
- `data/raw/digidata_14001/Link_Lives Release 2 Guide (2025).pdf` (extracted from `Dokumenter/` in `14001.zip`) — column meanings for the Link-Lives census files

### Data
- `data/raw/digidata_14001/14001.zip` — members `Data/CSV/main_datasets/census_{1801,1850,1860,1880,1901}__v1__cl.csv` (~168–675 MB each)
- `data/raw/linking_lab/MF_census_1850_1846_cl.xlsx` — sheet `MF_census_1850_1846_cl`, 83,414 rows, 22 columns incl. leftover index `Column1`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None. Greenfield repo. Only `.planning/`, `.gitignore` and `.claude/CLAUDE.md` are tracked.

### Established Patterns
- `.gitignore` already excludes `data/`, `*.xlsx`, `*.zip`, `*.csv`, `*.pdf`, `.venv/`, `.ipynb_checkpoints/`. Parquet files under `data/` are covered too. Keep all generated parquet under `data/` (e.g. `data/parquet/`).
- `uv` is installed at `~/.local/bin/uv`. System Python is 3.14, with no global packages. Check that the pinned deps (polars, pyarrow, rapidfuzz, jupyter/ipykernel, a plotting lib, plus an Excel reader for polars such as `fastexcel`) have 3.14 wheels. If any doesn't, pin `requires-python` / a uv-managed Python that works.

### Integration Points
- Phase 2 reads `data/parquet/census_<year>.parquet`. Phase 3 reads the DWI parquet. Name them consistently so later scripts can rely on the paths.

</code_context>

<specifics>
## Specific Ideas

- Every number in the notebooks that feeds an open decision is collected in a closing "Facts for open decisions" section: method, LLM, embeddings, impact, window width.
- Bias caveats (anchors favour people with surnames; empty `handicaps` ≠ no handicap) are stated next to the numbers they qualify, not only in the README.

</specifics>

<deferred>
## Deferred Ideas

- Age-heaping / digit-preference check per free/enslaved group (was offered as an add-on to D-08 and not chosen). Candidate for the Task 2 README "limitations / next steps".
- Download automation for the Digidata zip. The README documents the source instead.

</deferred>

---

*Phase: 01-setup-eda*
*Context gathered: 2026-10-18*
