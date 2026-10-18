# Task 1: harmonising `handicaps`

A first iteration, as the brief asks. `harmonise.py` gives each distinct `handicaps` value a proposed standard and a confidence, and selects one reviewer-day of work for Asbjørn: the 300 clusters whose decision standardises the most records, each with up to five whole example records. Spelling is automatic; categories are suggestions, and the historian decides.

## How to run

First run the root README's "Setup" and "Prepare data" (`uv sync`, `uv run python scripts/prepare_data.py`). The script reads only the five census parquet files (1801, 1850, 1860, 1880, 1901).

```bash
uv run python task1_handicaps/harmonise.py                  # write File A and File B
uv run python task1_handicaps/harmonise.py --check          # validate the outputs, write nothing
uv run python task1_handicaps/harmonise.py --write-leaders  # write the review-leader worksheet (local only)
uv run python task1_handicaps/harmonise.py --lookup PATH    # use another category lookup file
```

`--write-leaders` regenerates the per-cluster worksheet the category lookup is written from; rerun it when the clusters change, then update the lookup. Exit status 2 means a missing census parquet or lookup row, or a lookup with a null cell or duplicated leader (D-19). The script prints paths, counts and `FACT` lines, never rows.

## Outputs

| File | Where | Committed? | Content |
|---|---|---|---|
| File A `handicaps_mapping.parquet` | `task1_handicaps/outputs/` | yes | One row per distinct trivially normalised value (value-level counts, no other person attributes; see the note on rare values below). Columns: `value`, `value_type`, `n_1801` to `n_1901`, `n_total`, `raw_variants_n`, `raw_spellings`, `cluster_id`, `proposed_standard`, `confidence`, `in_review`, `suggested_category`, `category_source`, `category_inherited` |
| `category_suggestions.parquet` | `task1_handicaps/` | yes | The LLM category lookup: `leader`, `suggested_category`, `category_source` (300 rows) |
| File B `handicaps_review.parquet` + `.csv` | `data/outputs/task1/` | no | 300 rows, one per cluster: `cluster_id`, `proposed_standard`, `n_total`, per-year counts, `merged_spellings` with counts, `confidence_mean`, `confidence_min`, `examples_n`, `suggested_category`, `category_source`, `category_inherited`, and empty `decision` and `comment` |
| File B `handicaps_review_records.parquet` + `.csv` | `data/outputs/task1/` | no | Up to 5 whole census records per cluster, linked to the review table by `cluster_id`; starts with `cluster_id`, `proposed_standard`, `year`, `pa_id`, `handicaps`, then every census column |

- **File B** holds whole records. It is written only under the gitignored `data/` (the script refuses anywhere else), never committed (D-15), and delivered in the hand-in zip (D-16).
- **Rare values in File A (code review CR-01, deferred).** 2,813 of the 3,333 content values occur in at most 2 records. Such a value and its `raw_spellings` are in effect one person's transcribed text; some describe a household or name a person. File A is therefore not fit for publication. The repo is shared only with Rigsarkivet, which holds the source data. Before wider sharing: mask rare values (say, under 5 records) in the committed File A, keep the full mapping under `data/outputs/`, and purge earlier File A versions from the git history.
- **CSV copies** are UTF-8 with a BOM and semicolon-separated, so Danish-locale Excel splits columns and shows æ, ø, å. A cell starting with `=`, `+`, `-`, `@`, tab or carriage return gets a leading single quote, so Excel shows text, not a formula; parquet keeps the original (D-19).
- **`category_inherited`**: the category comes from the cluster leader, not the value (D-10, D-19). In the review table: any value in the cluster is inherited.
- **`pa_id`** is unique only within a year (one string occurs in 1850 and 1901), so records are identified by `year` and `pa_id`.

## EDA findings

From the Phase 1 notebook [`eda.ipynb`](eda.ipynb) (`FACT task1.*` lines in its output).

| | 1801 | 1850 | 1860 | 1880 | 1901 |
|---|---|---|---|---|---|
| Records filled (share) | 0.0001 | 0.0094 | 0.0123 | 0.0243 | 0.0246 |
| Parishes with nothing filled (share) | 0.9994 | 0.4304 | 0.3 | 0.3011 | 0.3103 |

- 1801 is practically empty (2 distinct raw values). Empty can mean not asked, not transcribed, or checked and nothing found; it must not be read as "no handicap".
- Trivial normalisation (lowercase, punctuation to space, whitespace collapsed) turns 4,520 raw values into 3,416. The 2,494 singletons hold only 1.74% of filled records: short head, long tail. Most filled records are placeholders (`-`, `?`, bare numbers).
- Household and occupation terms appear ("deres børn", "hans kone", "tjenestefolk", "inderste,dagleier,huusfader"), and the 1801 `M` and `K` look like the same effect: possibly transcription or column shift. A question for the reviewers (D-02).
- Leading codes ("d døvstum", "s sindssyg", "b blind") mostly merge; "b blind" stays separate (D-06). The bare letters "s", "a", "d", "b" are 1901 values (1,767, 1,421, 336, 282 records, from File A). Raw spellings such as "D [Døvstum]" suggest abbreviations, but that is a hypothesis, not a finding. The only 1801 values, "M" and "K" (86 records), are a separate case.

## Assumptions and decisions

Assumptions: empty and placeholder values say nothing about a condition; a group's most frequent spelling is the best standard; categories are suggestions. Minimise analyst degrees of freedom (no keyword lists, no thresholds beyond those the EDA fixed). `fuzz.ratio >= 85` can also merge different words (a deaf-mute value under an idiot leader), hence `category_inherited` and historian review of the largest clusters instead of blind trust. Values whose digits differ are never merged (D-17); numbers written as words are not compared and can still merge.

Ids refer to the Phase 2 context file and the project's Key Decisions table.

- **D-01** Placeholder = no letters after normalisation (so "1898" too); no list. Kept in File A as `value_type = placeholder`, without standard or category; excluded from File B and coverage.
- **D-02** No misplaced-value flag (a keyword detector adds degrees of freedom): household and occupation values are frequent enough to reach File B anyway.
- **D-03** Greedy leader clustering of content values by descending pooled count; each joins the best leader with `fuzz.ratio >= 85` (Phase 1 method, amended by D-17).
- **D-04, D-05** Proposed standard = the leader (most frequent form). Confidence = `fuzz.ratio(value, leader) / 100`, 1.0 for the leader.
- **D-06** No prefix stripping: "d døvstum" (87.5) and "s sindssyg" (88.9) merge; "b blind" (83.3 against "blind") stays separate for the historian. A letter may carry source meaning.
- **D-07** HARM-06 embeddings not implemented, a deliberate deviation from the requirement text. The design would assign each rare value to its nearest frequent anchor (cosine similarity as confidence), grouping values that differ in wording, not spelling ("blind", "svagsynet"). Not built because of modern-meaning bias (see the caveat), a large torch and model dependency, and a cosine threshold as one more degree of freedom. The confirmed scope after the EDA is zero; the user accepts this as the requirement outcome (D-18), and HARM-06 and the roadmap criterion are reworded to say so.
- **D-08** Categories are LLM suggestions written once in-session and committed (`category_suggestions.parquet`, `category_source = llm_suggestion`). No API call at runtime; every row is auditable.
- **D-09** Vocabulary in the census's own terms: døvstum/døv, blind, sindssyg, uden forstandsevner/idiot (incl. "forstanden berøvet"), krøbling/vanfør, multiple conditions, other/unclear, "not a condition (suspected misplaced)". The last also holds negations ("nej", "ingen", "rask"), which lack a bucket; it does not change D-02.
- **D-10** Only the 300 review clusters get categories. Merged values inherit them (`category_inherited`); the tail gets none.
- **D-11** Impact (the user's definition) = real-content records a cluster's decision standardises, pooled over five years, placeholders excluded, as in HisPeR's most-frequent-first practice.
- **D-12** 300 clusters = one reviewer-day = 120 records/hour x 2.5 hours (the brief's 100-120/hour and 2-3 hours/day give 200-360). Coverage is computed, not hard-coded.
- **D-13, D-14** File B pairs one review row per cluster with whole example records via `cluster_id`, so clusters are judged in context. Up to 5 examples per cluster, uniformly random with a fixed seed, no typicality judgement; smaller clusters show all.
- **D-15, D-16** Record-level outputs are never committed: after sharing, removal needs a history rewrite. Delivery: a Phase 4 zip of the working tree, with `data/outputs/` and without `data/raw/` and `data/parquet/`.
- **D-17** Digit guard (amends D-03): a value joins a leader only if both have the same digit runs (maximal runs of 0-9, compared as strings); otherwise it starts a new cluster. `fuzz.ratio` treats digits as letters, so the first run mapped "syg i 1 aar" to "syg i 2 aar" (confidence 0.91). No parameter; normalisation, order and threshold unchanged. Lookup refreshed: 189 leaders kept their label, 111 new ones were labelled by the same conventions (D-08, D-09).
- **D-19** Review fixes: `category_inherited`; CSV quoting; a lookup with a null cell or duplicated leader is rejected before writing; `--check` compares lookup and review leaders as sets both ways. Four findings are deferred, with reasons, in the phase folder's `02-REVIEW-DISPOSITION.md`.

## Conclusions

- 3,416 normalised values: 83 placeholders and 3,333 content values in 2,160 clusters.
- The top 300 clusters (one reviewer-day) cover 1,249 values and 92.66% of real-content records; 80%, 90% and 95% need 26, 158 and 601 clusters. The other 1,860 clusters hold about 7.3% of records (2,436) but 2,084 of the 3,333 values.
- The digit guard moved 1,061 values (1,921 records) that would otherwise carry a standard stating a different number. Clusters rise from 1,652 to 2,160; top-300 coverage falls from 95.15% to 92.66%. A correct standard is, I think, worth the 2.49 points.
- Phase 1 printed `FACT task1.clusters.ratio85=1732` because it clustered all 3,416 values, placeholders included, without the guard; the script clusters only the 3,333 content values (D-01).
- Categories are a starting point. "other/unclear" holds 5,091 records, 3,806 of them the 1901 single letters. "not a condition (suspected misplaced)" has 64 of 300 leaders but 2,963 records. 949 of the 1,249 review values inherit their category, so a mixed cluster can carry a label that fits only part of it.

## Next steps

- HARM-06 embeddings (D-07), once Asbjørn's first pass shows which wording groups matter.
- Category suggestions for the 1,860 tail clusters, after the first review.
- Numbered values (onset age, duration) are now separate clusters; moving the number into its own field would let one wording decision cover every number.
- Use Asbjørn's decisions as an offset to standardise the tail automatically (step 3 of the brief's 2019 workflow).
- Phase 4 builds the hand-in zip that carries File B (D-16).
- Questions for Bárbara and Olivia (for `QUESTIONS.md`): Are the household and occupation values transcription or column-shift effects? Do placeholder dashes mean "checked, nothing" or "not asked"? What do the 1801 "M" and "K" mean? Are the 1901 letters "s", "a", "d", "b" and codes like "d døvstum" abbreviations of sindssyg, åndssvag, døvstum and blind?

## Caveat: modern-meaning bias

Terms for illness and disability changed meaning. A model trained on modern text reads "sindssyg" or "åndsvag" with today's meaning and can hide the shifts a historian cares about. Hence the census's own vocabulary (D-09), the `llm_suggestion` marking and the historian's final say; it is also the main reason HARM-06 was descoped (D-07).

## Key figures

Printed by `harmonise.py`. Other numbers come from the Phase 1 notebook or per-value counts in File A (single letters, rare values, "syg i 1 aar").

```text
FACT task1.harmonise.records.filled=143597
FACT task1.harmonise.values.raw=4520
FACT task1.harmonise.records.placeholder=110387
FACT task1.harmonise.records.content=33210
FACT task1.harmonise.values.trivial=3416
FACT task1.harmonise.values.placeholder=83
FACT task1.harmonise.values.content=3333
FACT task1.harmonise.clusters=2160
FACT task1.harmonise.coverage.top100=0.8783
FACT task1.harmonise.coverage.top200=0.9103
FACT task1.harmonise.coverage.top300=0.9266
FACT task1.harmonise.coverage.top360=0.9329
FACT task1.harmonise.clusters_for_coverage.80=26
FACT task1.harmonise.clusters_for_coverage.90=158
FACT task1.harmonise.clusters_for_coverage.95=601
FACT task1.harmonise.review.size=300
FACT task1.harmonise.review.size_low=200
FACT task1.harmonise.review.size_high=360
FACT task1.harmonise.review.values=1249
FACT task1.harmonise.digit_guard.clusters_unguarded=1652
FACT task1.harmonise.digit_guard.values_moved=1061
FACT task1.harmonise.digit_guard.records_moved=1921
FACT task1.harmonise.digit_guard.coverage.top300_unguarded=0.9515
FACT task1.harmonise.lookup.missing=0
FACT task1.harmonise.lookup.unused=0
FACT task1.harmonise.category.labels_used=8
FACT task1.harmonise.category.values=1249
FACT task1.harmonise.category.record_share=0.9266
FACT task1.harmonise.category.inherited_values=949
FACT task1.harmonise.category.leaders.døvstum/døv=14
FACT task1.harmonise.category.records.døvstum/døv=5102
FACT task1.harmonise.category.leaders.blind=18
FACT task1.harmonise.category.records.blind=3483
FACT task1.harmonise.category.leaders.sindssyg=9
FACT task1.harmonise.category.records.sindssyg=5547
FACT task1.harmonise.category.leaders.uden forstandsevner/idiot=97
FACT task1.harmonise.category.records.uden forstandsevner/idiot=8009
FACT task1.harmonise.category.leaders.krøbling/vanfør=6
FACT task1.harmonise.category.records.krøbling/vanfør=422
FACT task1.harmonise.category.leaders.multiple conditions=16
FACT task1.harmonise.category.records.multiple conditions=157
FACT task1.harmonise.category.leaders.other/unclear=76
FACT task1.harmonise.category.records.other/unclear=5091
FACT task1.harmonise.category.leaders.not a condition (suspected misplaced)=64
FACT task1.harmonise.category.records.not a condition (suspected misplaced)=2963
FACT task1.harmonise.examples.records=1479
FACT task1.harmonise.examples.clusters_lt5=21
```

Placeholders are 76.9% of filled records. 21 review clusters have fewer than 5 records, so the example file holds 1,479 records, not 1,500.
