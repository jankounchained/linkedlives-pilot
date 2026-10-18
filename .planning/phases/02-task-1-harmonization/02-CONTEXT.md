# Phase 2: Task 1 — Harmonization - Context

**Gathered:** 2026-10-18
**Status:** Ready for planning

<domain>
## Phase Boundary

A first-iteration harmonisation of the `handicaps` variable (1801, 1850, 1860, 1880, 1901 Link-Lives `*__v1__cl` censuses), delivered as:
- **File A** `handicaps_mapping.parquet`: one row per distinct trivially normalised value, with per-year frequency, cluster leader as proposed standard value, confidence, a value type, and a suggested category clearly marked as a suggestion.
- **File B** `handicaps_review.parquet` (+ CSV) for Asbjørn: the 300 highest-impact clusters with empty `decision`/`comment` columns, plus a companion file of example whole records per cluster.
- A Task 1 README (`task1_handicaps/README.md`) covering EDA findings, assumptions, decisions, conclusions and next steps.

Time budget: ~1h. Whole-project time is already tight (~2h of ~3.5h used at the start of this phase), so the plan must be lean.

</domain>

<decisions>
## Implementation Decisions

**Guiding preference (user):** minimise analyst degrees of freedom. Prefer rules that have nothing to tune, or reuse parameters already fixed and shown in the Phase 1 EDA. Do not add hand-made keyword lists or extra weighting choices.

### Non-handicap content
- **D-01:** **Placeholders are the only special value type.** Rule: a value is a placeholder when its trivially normalised form contains no letters (catches `-`, ` -`, `(-)`, `.`, `?`, `--`, `??`, …). There is no list and nothing to tune. Placeholders stay in File A with `value_type = "placeholder"` and no proposed standard or category. They are excluded from File B and from all coverage maths. Measured: 110,387 of 143,597 filled records are placeholders, leaving 33,210 real-content records.
- **D-02:** **No flag for suspected misplaced values** ("deres børn", "hans kone", "tjenestefolk", "inderste,dagleier,huusfader", 1801 `M`/`K`). They go through the same pipeline as every other value. They are frequent, so record-count impact puts them in File B, where the historian decides. The README reports the observation and names it as a candidate question for Barbara/Olivia (transcription or column-shift effect?). The user rejected a curated keyword detector because it adds degrees of freedom.

### Spelling normalisation (HARM-01, HARM-02)
- **D-03:** Use the Phase 1 EDA method unchanged. Trivial normalisation: lowercase, punctuation replaced by a space, whitespace collapsed and stripped. Then greedy leader clustering over the trivial values, visited in descending pooled count, where each value joins the best leader with `rapidfuzz.fuzz.ratio >= 85` and otherwise becomes a new leader. Clustering runs on non-placeholder values only. Measured: 3,333 real distinct trivial values → 1,645 clusters.
- **D-04:** The **proposed standard value** is the cluster leader, i.e. the most frequent trivially normalised form in the cluster. There is no extra rule.
- **D-05:** **Confidence** = `fuzz.ratio(value, leader) / 100`. It is 1.0 for the leader itself.
- **D-06:** **No prefix-stripping rule** for leading letter codes ("d døvstum", "b blind", "s sindssyg"). Clustering merges most of them at 85 ("d døvstum" 87.5, "s sindssyg" 88.9). Some stay separate ("b blind" 83.3), so the historian sees them. The README notes this, and that a letter may carry source meaning.

### Categories & wording (HARM-03, HARM-06)
- **D-07:** **HARM-06 embeddings are descoped to next steps and not implemented.** The README explains why: a modern-text model brings modern-meaning bias, it needs a large torch/model dependency, and it needs a cosine threshold (more degrees of freedom). This is a deliberate deviation from the HARM-06 wording ("scope confirmed after EDA"), and the confirmed scope is zero.
- **D-08:** **The suggested category comes from an LLM, produced once and committed as a lookup table.** Claude (the executor, in-session) writes one suggested category per cluster leader into a committed lookup file (e.g. `task1_handicaps/category_suggestions.parquet`, with columns `leader`, `suggested_category`, `category_source = "llm_suggestion"`). The script joins this lookup and calls no API at runtime. Every row can be audited.
- **D-09:** **Vocabulary = historical source terms, not modern groups.** Use the census's own groupings, e.g. døvstum/døv, blind, sindssyg, forstandsevner/idiot ("uden forstandsevner", "forstanden berøvet"), krøbling, plus an explicit other/unclear bucket. Clearly non-condition values such as household relations get a suggestion like "not a condition (suspected misplaced)". This is a category suggestion only and does not change D-02 (still no flag or detector). The README carries the modern-meaning-bias caveat.
- **D-10:** **Only the File B clusters get a suggested category**, i.e. the same 300 top clusters (see D-12). Values merged into one of those clusters inherit its category. The rare tail stays blank. The README states the coverage this gives. Reusing the File B size avoids a separate "frequent" threshold.

### File B (HARM-04)
- **D-11:** **Impact definition (user's): impact = the number of real-content records a cluster's decision would standardise.** Rank non-placeholder clusters by pooled record count across all five years. This matches HisPeR's synonym-catalogue practice of standardising the most frequent values first for coverage.
- **D-12:** **Size = 300 clusters, fixed at one reviewer-day.** Arithmetic to show in the README: 120 records/h × 2.5 h = 300 (range 100–120/h × 2–3 h = 200–360). Report coverage: the top 300 clusters cover 95.2% of real-content records (95% is reached at 280, the same target as the brief's name catalogue). Recompute and print these numbers in the script; do not hard-code them.
- **D-13:** **Two files linked by `cluster_id`.**
  - `handicaps_review` has one row per cluster (300 rows): `cluster_id`, the leader / proposed standard, the merged raw spellings with counts, per-year counts, pooled count, mean/min confidence, the suggested category (marked as a suggestion), and empty `decision` and `comment` columns.
  - `handicaps_review_records` holds example **whole records** (all census columns plus `pa_id`, `year`, `cluster_id`) for each cluster. The historian needs to see whole records to judge a cluster in context.
- **D-14:** **Example selection: up to 5 records per cluster, uniform random with a fixed seed.** This is reproducible and involves no judgement about which records are "typical". A cluster with fewer than 5 records shows all of them.

### Governance & delivery
- **D-15:** **Record-level outputs are never committed.** `handicaps_review` and `handicaps_review_records` (parquet + CSV) contain whole records, so they are written under `data/` (gitignored and blocked by `.githooks/pre-commit`), e.g. `data/outputs/task1/`. File A (value-level counts only, no records), the category lookup and the scripts are committed (e.g. `task1_handicaps/outputs/handicaps_mapping.parquet`). — **Reversibility:** one-way — once record-level data is committed and the repo is shared, removing it needs a history rewrite.
- **D-16:** **Delivery = zipped repo (user decision; this resolves the earlier "invite vs zip" decision).** The zip is built from the working tree and includes the local record-level File B outputs without committing them. The recipients (Rigsarkivet) own this release. Phase 4 must build the zip so it includes `data/outputs/` but **excludes `data/raw/` and `data/parquet/`** (GBs). This is a note for Phase 4, not built here.

### Gap-closure amendments (after verification, 2026-10-18)
- **D-17 (amends D-03): Digit guard.** A value may only join a leader whose digit runs (`re.findall(r"\d+", value)`) are identical to its own. Otherwise it becomes a new leader. Nothing else in D-03 changes: trivial normalisation, visiting order and `fuzz.ratio >= 85` stay as they are. The guard has no parameter, so it fits the minimise-degrees-of-freedom preference. Reason: verification gap CR-01. Matching that ignored digits gave wrong onset ages and durations at high confidence ("syg i 1 aar" → "syg i 2 aar", 0.91), affecting 1,883 records in 80 of the 300 review clusters. Consequences: cluster counts, coverage and the review leaders change. New review leaders get an LLM category per D-08/D-09, leaders that drop out are removed from the lookup, and the README figures are regenerated from the FACT lines. The README no longer calls the Phase 1 method "unchanged". (User decision.)
- **D-18: HARM-06 is closed by D-07.** The user accepts the D-07 descoping as the HARM-06 outcome. REQUIREMENTS.md HARM-06 and ROADMAP Phase 2 success criterion 3 are reworded to state the confirmed scope: zero, with embedding grouping as a documented next step. No embedding code is written. (User decision.)
- **D-19: Review warnings fixed alongside the gaps.** WR-02: a `category_inherited` boolean in File A and in the review table, true where a row's suggested category comes from a different leader value. WR-03: in the CSV copies only, cells starting with `=`, `+`, `-`, `@`, tab or CR are escaped; the parquet files are unchanged. WR-01 + IN-03: the lookup rejects null and duplicate rows, and `--check` asserts that the lookup leaders and the review leaders match in both directions. WR-04, WR-05, IN-01 and IN-02 stay open (deferred). (Claude's choice; the user delegated it.)

### Claude's Discretion
- Script name(s) and layout inside `task1_handicaps/` (e.g. one `harmonise.py`). Reuse `scripts/project_paths.py` for paths.
- Exact File A column names, as long as they cover HARM-02/03: per-year counts, `value_type`, proposed standard, confidence, `suggested_category` labelled as a suggestion.
- The exact historical category labels, within D-09.
- The seed value and the CSV encoding/delimiter for historians. Prefer UTF-8 with BOM, so Danish characters open correctly in Excel.
- Which census columns to keep in the example records: all of them, per D-13, unless a column is pure pipeline noise.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project planning
- `.planning/PROJECT.md` — constraints (data governance, parquet, uv/polars/rapidfuzz) and the Key Decisions table (Phase 2 decisions recorded there)
- `.planning/REQUIREMENTS.md` — HARM-01..06 wording (HARM-06 is descoped by D-07)
- `.planning/ROADMAP.md` §"Phase 2: Task 1 — Harmonization" — success criteria and time budget
- `.planning/phases/01-setup-eda/01-CONTEXT.md` — D-02 (no record-level rows in committed outputs), D-06 (all-String parquet), D-12 (normalisation preview method reused here)

### Phase 1 evidence
- `task1_handicaps/eda.ipynb` — normalisation preview (§4), messy-value examples (§5), coverage curve (§6) and the FACT lines. The clustering code there is the reference implementation for D-03.

### Source documents (local only, gitignored)
- `data/raw/linking_lab/Pre_interview_tasks_for_data_scientists_datamanagers_2026.pdf` §3 — the Task 1 brief: synonym-catalogue practice, 100–120 records/h × 2–3 h/day, "first iteration", expected output (script(s), a data file for the team, minimal explanation)
- `data/raw/digidata_14001/Link_Lives Release 2 Guide (2025).pdf` — authority for column meanings

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/project_paths.py`: `census_parquet(year)`, `PARQUET_DIR`, `DATA_ROOT`. Use these for inputs and for the `data/outputs/` location.
- `task1_handicaps/eda.ipynb`: trivial normalisation and greedy leader clustering code (D-12 of Phase 1). Port it into the script rather than reinventing it.
- `scripts/prepare_data.py --check`: verifies the parquet inputs exist.

### Established Patterns
- Parquet stores all columns as strings (Phase 1 D-06). Cast explicitly.
- Polars lazy scans over `data/parquet/census_{year}.parquet`. Only the `handicaps` column is needed for File A. File B records need all columns, but only for the sampled rows.
- Numbers in docs come from the code (EDA FACT-line pattern). Print the key figures (coverage, sizes) from the script.

### Integration Points
- `.githooks/pre-commit` blocks anything staged under `data/` and any `.csv` (via `.gitignore`), so record-level outputs placed under `data/outputs/` are protected automatically.
- The root README (Phase 4) will link `task1_handicaps/README.md`.

</code_context>

<specifics>
## Specific Ideas

- Coverage figures measured during discussion (non-placeholder, ratio 85): top 100 = 91.7%, 200 = 94.1%, 280 = 95.0%, 300 = 95.2%, 360 = 95.6%. Reaching 80% takes 22 clusters and 90% takes 71.
- The historian judges a cluster by looking at whole records, so the review is "cluster decision informed by 5 example records".
- Candidate questions for QUESTIONS.md (the user writes that file): misplaced household/occupation values in `handicaps` (column shift?); the meaning of placeholder dashes ("checked, nothing" vs "not asked"); 1801 `M`/`K`; leading letter codes.

</specifics>

<deferred>
## Deferred Ideas

- Embedding-based wording grouping (HARM-06) → README next steps.
- Category suggestions for the rare tail (~1,345 clusters beyond the top 300) → next iteration, after Asbjørn's first pass.
- Using Asbjørn's decisions as an offset for automatic standardisation of the tail (the brief's 2019 workflow step 3) → next steps.
- Zip build that includes `data/outputs/` and excludes raw/parquet → Phase 4.

</deferred>

---

*Phase: 02-task-1-harmonization*
*Context gathered: 2026-10-18*
