# Task 1: harmonising `handicaps`

This is a first iteration, as the brief asks. One script maps every distinct value of the `handicaps` column to a proposed standard value with a confidence. It then gives Asbjørn one reviewer-day of work: the 300 clusters whose decision standardises the most records, each with up to five whole example records. The spelling step is automatic. The category step is a suggestion, and the historian decides.

## How to run

Prerequisites: the root README sections "Setup" and "Prepare data" (`uv sync`, then `uv run python scripts/prepare_data.py`). The script reads the five census parquet files (1801, 1850, 1860, 1880, 1901) and nothing else.

```bash
uv run python task1_handicaps/harmonise.py                  # write File A and File B
uv run python task1_handicaps/harmonise.py --check          # validate the outputs, write nothing
uv run python task1_handicaps/harmonise.py --write-leaders  # write the review-leader worksheet (local only)
uv run python task1_handicaps/harmonise.py --lookup PATH    # use another category lookup file
```

`--write-leaders` regenerates the worksheet (one row per review cluster) that the category lookup is written from. Use it when the clusters change, then update the lookup. The script exits with status 2 if a census parquet or a lookup row is missing, or if the lookup has a null cell or a duplicated leader (D-19). It prints only paths, counts and `FACT` lines, never rows.

## Outputs

| File | Where | Committed? | Content |
|---|---|---|---|
| File A `handicaps_mapping.parquet` | `task1_handicaps/outputs/` | yes | One row per distinct trivially normalised value (value-level only, no records). Columns: `value`, `value_type`, `n_1801` to `n_1901`, `n_total`, `raw_variants_n`, `raw_spellings`, `cluster_id`, `proposed_standard`, `confidence`, `in_review`, `suggested_category`, `category_source`, `category_inherited` |
| `category_suggestions.parquet` | `task1_handicaps/` | yes | The LLM category lookup: `leader`, `suggested_category`, `category_source` (300 rows) |
| File B `handicaps_review.parquet` + `.csv` | `data/outputs/task1/` | no | 300 rows, one per cluster: `cluster_id`, `proposed_standard`, `n_total`, per-year counts, `merged_spellings` with counts, `confidence_mean`, `confidence_min`, `examples_n`, `suggested_category`, `category_source`, `category_inherited`, and empty `decision` and `comment` |
| File B `handicaps_review_records.parquet` + `.csv` | `data/outputs/task1/` | no | Up to 5 whole census records per cluster, linked to the review table by `cluster_id`; starts with `cluster_id`, `proposed_standard`, `year`, `pa_id`, `handicaps`, then every census column |

File B holds whole census records, so it is written only inside the gitignored `data/` directory and is never committed (D-15). The script refuses to write it anywhere else. It reaches the recipients inside the hand-in zip, which Phase 4 builds from the working tree to include `data/outputs/` and exclude `data/raw/` and `data/parquet/` (D-16).

The CSV files are UTF-8 with a BOM and separated by semicolons, so Excel with a Danish locale splits the columns and shows æ, ø and å correctly. In the CSV copies only, a cell that begins with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading single quote, so that Excel shows it as text and not as a formula. The parquet files keep the original value (D-19). `category_inherited` is true when a value's category comes from its cluster leader and not from the value itself (D-10, D-19); in the review table it is true when any value of the cluster is inherited. `pa_id` identifies a record within one census year only: one `pa_id` string appears in both 1850 and 1901. Records are therefore identified by `year` and `pa_id` together.

## EDA findings

Source: the Phase 1 notebook [`eda.ipynb`](eda.ipynb). Its figures are `FACT task1.*` lines in the notebook output.

- **Fill rate.** The share of records with a filled `handicaps` value is 0.0001 in 1801 (only 2 distinct raw values), 0.0094 in 1850, 0.0123 in 1860, 0.0243 in 1880 and 0.0246 in 1901. The 1801 column is practically empty.
- **Parishes with nothing filled.** The share of parishes where no record has a filled value is 0.9994 in 1801, 0.4304 in 1850, 0.3 in 1860, 0.3011 in 1880 and 0.3103 in 1901. An empty value may mean the census did not ask, the value was not transcribed, or someone checked and found nothing. It must not be read as "no handicap".
- **Cardinality.** 4,520 distinct raw values become 3,416 after trivial normalisation (lowercase, punctuation to space, whitespace collapsed). 2,494 of those are singletons, but they cover only 1.74% of the filled records. The distribution has a short head and a long tail.
- **Placeholders dominate.** Most filled records hold a placeholder such as `-`, `?` or a bare number, not a condition (counts in Key figures).
- **Non-condition content.** Household relations and occupations sit in the column: "deres børn", "hans kone", "tjenestefolk", "inderste,dagleier,huusfader". The 1801 values `M` and `K` look like the same effect. This may be a transcription or column-shift effect, and it is a question for Bárbara and Olivia (D-02).
- **Letter codes.** Leading codes such as "d døvstum", "s sindssyg" and "b blind" occur. Clustering merges most of them. "b blind" stays a separate cluster (D-06). The bare single letters "s", "a", "d" and "b" are 1901 values: 1,767, 1,421, 336 and 282 records in 1901 (from File A). They are possibly abbreviations of a condition. Raw spellings such as "D [Døvstum]" point that way, but this is a hypothesis, not a finding. The only values in 1801 are "M" and "K" (86 records), which are a separate case.

## Assumptions

- Empty and placeholder values carry no information about a condition.
- The most frequent spelling in a group is the best proposed standard.
- `fuzz.ratio >= 85` merges spelling variants, but it can also merge different words, for example a deaf-mute value under an idiot leader. Values whose numbers differ are never merged (D-17). This is why inherited categories are flagged (`category_inherited`) and the largest clusters go to a historian instead of being trusted blindly.
- Categories are suggestions. The historian decides.
- Guiding preference: minimise analyst degrees of freedom. No keyword lists, no extra thresholds, nothing to tune beyond what the EDA already fixed and showed.

## Decisions

Ids refer to the Phase 2 context file; they are also summarised in the project's Key Decisions table.

- **D-01 Placeholder rule.** A value is a placeholder when its trivially normalised form contains no letters. There is no list. Placeholders stay in File A with `value_type = placeholder` and no standard or category. They are excluded from File B and from all coverage figures. Bare numbers such as "1898" fall under this rule.
- **D-02 No misplaced-value flag.** Household and occupation values go through the same pipeline as everything else. They are frequent, so the impact ranking puts them in File B, where the historian decides. A keyword detector would add degrees of freedom.
- **D-03 Spelling method.** The Phase 1 EDA method as amended by D-17: trivial normalisation, then greedy leader clustering over the content values, visited by descending pooled count, each value joining the best leader at `fuzz.ratio >= 85`, but only a leader that states the same numbers (D-17).
- **D-04 Proposed standard = cluster leader**, the most frequent trivially normalised form in the cluster.
- **D-05 Confidence = `fuzz.ratio(value, leader) / 100`.** It is 1.0 for the leader.
- **D-06 No prefix stripping.** "d døvstum" (87.5) and "s sindssyg" (88.9) merge into their clusters. "b blind" scores 83.3 against "blind" and stays a separate cluster, so the historian sees it. A letter may carry source meaning.
- **D-07 HARM-06 embeddings not implemented.** See Next steps. This is a deliberate deviation from the requirement text. The confirmed scope after the EDA is zero, and the user accepts this as the requirement outcome (D-18): HARM-06 and the roadmap criterion are reworded to say so.
- **D-08 Categories come from an LLM, written once and committed.** `suggested_category` is a suggestion produced in-session and stored in `category_suggestions.parquet`. The script joins it and calls no API at runtime. Every row can be audited. `category_source` is `llm_suggestion`.
- **D-09 Vocabulary = the census's own terms.** døvstum/døv, blind, sindssyg, uden forstandsevner/idiot (including "forstanden berøvet"), krøbling/vanfør, multiple conditions, other/unclear, and "not a condition (suspected misplaced)". That last label also holds explicit negations such as "nej", "ingen" and "rask", because the fixed vocabulary has no separate bucket for them. The label is a suggestion only and does not change D-02.
- **D-10 Categories only for the 300 review clusters.** Values merged into one of them inherit its category. The tail has no category. `category_inherited` marks the values whose category comes from their leader (D-19).
- **D-11 Impact.** The user's definition: impact = the number of real-content records a cluster's decision would standardise. Clusters are ranked by pooled record count over all five years, placeholders excluded. This matches the HisPeR practice of standardising the most frequent values first.
- **D-12 Size = 300 clusters, one reviewer-day.** The arithmetic, from the brief's 100-120 records per hour and 2-3 hours per day:

  ```text
  120 records/hour x 2.5 hours = 300
  100-120 records/hour x 2-3 hours = 200-360
  ```

  The coverage this gives (top 100, 200, 300 and 360 clusters, and the number of clusters needed for 80%, 90% and 95%) is printed by the script and quoted in Conclusions. Nothing is hard-coded.
- **D-13 Two files linked by `cluster_id`.** One review row per cluster, plus whole example records. The historian judges a cluster by looking at records in context.
- **D-14 Examples.** Up to 5 records per cluster, drawn uniformly at random with a fixed seed. No judgement about which are typical. A cluster with fewer than 5 records shows all of them.
- **D-15 Record-level outputs are never committed.** File B stays under `data/outputs/task1/`. This is one-way: once record-level data is committed and shared, removal needs a history rewrite.
- **D-16 Delivery is a zipped repo,** built in Phase 4, including `data/outputs/` and excluding `data/raw/` and `data/parquet/`.
- **D-17 Digit guard (amends D-03).** A value joins a leader only when both contain the same runs of digits (maximal runs of 0-9, compared as strings); otherwise it becomes a new leader. Reason: `fuzz.ratio` treats digits like letters, so the first run merged values that state different ages or durations. For example, "syg i 1 aar" was mapped to "syg i 2 aar" at confidence 0.91. The guard moved 1,061 values (1,921 records) out of clusters they had joined (`digit_guard.values_moved`, `digit_guard.records_moved`). It has no parameter, and trivial normalisation, the visiting order and the threshold of 85 stay as they were. Its cost is coverage: the clusters grow from 1,652 (`digit_guard.clusters_unguarded`) to 2,160 (`clusters`), and the top 300 clusters cover 92.66% of the real-content records (`coverage.top300`) instead of 95.15% (`digit_guard.coverage.top300_unguarded`). The category lookup was refreshed for the new review leaders: 189 leaders kept their label, and 111 new leaders got a label from the same conventions (D-08, D-09).
- **D-19 Review fixes.** `category_inherited` shows which categories come from a leader. In the CSV copies, risky leading characters get a single quote (parquet unchanged). The category lookup is rejected, before anything is written, when it has a null cell or a duplicated leader. `--check` compares the lookup leaders and the review leaders as sets in both directions. Four review findings are deferred, each with a reason, in `02-REVIEW-DISPOSITION.md` in the phase folder.

## Conclusions

- The mapping holds 3,416 trivially normalised values: 83 placeholders and 3,333 content values, which form 2,160 clusters. Only the 300 review clusters carry a category.
- One reviewer-day covers the top 300 clusters. Together they hold 1,249 distinct values and 92.66% of the real-content records (category record share 0.9266). 90% needs 158 clusters, 95% needs 601 clusters, and 80% is reached at 26.
- The digit guard (D-17) trades coverage for correctness. Without it, one reviewer-day would cover 95.15% of the records, but 1,061 values (1,921 records) would carry a proposed standard that states a different number. With it, one reviewer-day covers 92.66%. I think a correct proposed standard is worth the 2.49 percentage points.
- The remaining 1,860 clusters hold about 7.3% of the real-content records (2,436) but most of the distinct values (2,084 of 3,333). The tail is small in records and large in distinct values.
- The cluster count differs from the Phase 1 preview. The notebook `eda.ipynb` prints `FACT task1.clusters.ratio85=1732` (1,732 clusters). It clustered all 3,416 trivial values, placeholders included, and had no digit guard. The script clusters only the 3,333 content values (D-01), which gives 1,652 clusters without the guard, and the guard (D-17) gives the final 2,160.
- The category suggestions are a starting point. "other/unclear" holds 5,091 records. Most of them, 3,806, are the 1901 single letters "s", "a", "d" and "b" (1,767, 1,421, 336 and 282 records in 1901), which may be abbreviations. The 1801 values "M" and "K" (86 records) are a separate case. "not a condition (suspected misplaced)" is large in leaders (64 of 300) but small in records (2,963). Of the 1,249 review values, 949 take their category from their leader (`category_inherited`), so a mixed cluster can carry a label that fits only part of it.

## Next steps

- **HARM-06 was deliberately not implemented (D-07).** The requirement asks for embedding-based grouping of values that differ in wording rather than spelling, for example "blind" and "svagsynet". The design would assign each rare value to its nearest frequent anchor, with the cosine similarity as the confidence. I did not build it, for three reasons. A modern-text model brings modern-meaning bias (see the caveat below). It needs a large torch and model dependency. And it needs a cosine threshold, which is one more degree of freedom. It stays a candidate once Asbjørn's first pass shows which wording groups really matter.
- Category suggestions for the 1,860 tail clusters, after the first review.
- Numbered values (onset age, duration) are now separate clusters. A next iteration could move the number into its own field, so that one decision on the wording covers every number.
- Use Asbjørn's decisions as an offset to standardise the tail automatically (step 3 of the brief's 2019 workflow).
- Questions for Bárbara and Olivia (for `QUESTIONS.md`):
  - Are the household and occupation values in `handicaps` transcription or column-shift effects?
  - Do placeholder dashes mean "checked, nothing" or "not asked"?
  - What do the 1801 values "M" and "K" mean?
  - What do the 1901 single letters "s", "a", "d" and "b", and the leading codes such as "d døvstum", mean? Are they abbreviations of sindssyg, åndssvag, døvstum and blind?
- Phase 4 builds the hand-in zip that carries File B (D-16).

## Caveat: modern-meaning bias

Terms for illness and disability changed meaning over time. The category suggestions come from a modern language model, so they are written in the census's own vocabulary (D-09), marked `category_source = "llm_suggestion"`, and left for the historian to decide. The same bias is the main reason the HARM-06 embeddings were descoped (D-07). A model trained on modern text reads "sindssyg" or "åndsvag" through today's meaning of the words, which can hide exactly the shifts a historian cares about.

## Key figures

These lines are printed by `harmonise.py`. The numbers in this README come from three sources: these lines, the Phase 1 notebook, and per-value counts read from File A (the single-letter counts and the "syg i 1 aar" example).

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

Reading guide: of 143,597 filled records, 110,387 (76.9%) are placeholders and 33,210 are real content. Coverage at 100, 200, 300 and 360 clusters is 87.83%, 91.03%, 92.66% and 93.29%. The review table has 300 rows; 21 of those clusters have fewer than 5 records, so the example file holds 1,479 records, not 1,500.
