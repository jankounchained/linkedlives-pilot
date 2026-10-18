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

`--write-leaders` regenerates the worksheet (one row per review cluster) that the category lookup is written from. Use it when the clusters change, then update the lookup. The script exits with status 2 if a census parquet or a lookup row is missing. It prints only paths, counts and `FACT` lines, never rows.

## Outputs

| File | Where | Committed? | Content |
|---|---|---|---|
| File A `handicaps_mapping.parquet` | `task1_handicaps/outputs/` | yes | One row per distinct trivially normalised value (value-level only, no records). Columns: `value`, `value_type`, `n_1801` to `n_1901`, `n_total`, `raw_variants_n`, `raw_spellings`, `cluster_id`, `proposed_standard`, `confidence`, `in_review`, `suggested_category`, `category_source` |
| `category_suggestions.parquet` | `task1_handicaps/` | yes | The LLM category lookup: `leader`, `suggested_category`, `category_source` (300 rows) |
| File B `handicaps_review.parquet` + `.csv` | `data/outputs/task1/` | no | 300 rows, one per cluster: `cluster_id`, `proposed_standard`, `n_total`, per-year counts, `merged_spellings` with counts, `confidence_mean`, `confidence_min`, `examples_n`, `suggested_category`, `category_source`, and empty `decision` and `comment` |
| File B `handicaps_review_records.parquet` + `.csv` | `data/outputs/task1/` | no | Up to 5 whole census records per cluster, linked to the review table by `cluster_id`; starts with `cluster_id`, `proposed_standard`, `year`, `pa_id`, `handicaps`, then every census column |

File B holds whole census records, so it is written only inside the gitignored `data/` directory and is never committed (D-15). The script refuses to write it anywhere else. It reaches the recipients inside the hand-in zip, which Phase 4 builds from the working tree to include `data/outputs/` and exclude `data/raw/` and `data/parquet/` (D-16).

The CSV files are UTF-8 with a BOM and separated by semicolons, so Excel with a Danish locale splits the columns and shows æ, ø and å correctly. `pa_id` identifies a record within one census year only: one `pa_id` string appears in both 1850 and 1901. Records are therefore identified by `year` and `pa_id` together.

## EDA findings

Source: the Phase 1 notebook [`eda.ipynb`](eda.ipynb). Its figures are `FACT task1.*` lines in the notebook output.

- **Fill rate.** The share of records with a filled `handicaps` value is 0.0001 in 1801 (only 2 distinct raw values), 0.0094 in 1850, 0.0123 in 1860, 0.0243 in 1880 and 0.0246 in 1901. The 1801 column is practically empty.
- **Parishes with nothing filled.** The share of parishes where no record has a filled value is 0.9994 in 1801, 0.4304 in 1850, 0.3 in 1860, 0.3011 in 1880 and 0.3103 in 1901. An empty value may mean the census did not ask, the value was not transcribed, or someone checked and found nothing. It must not be read as "no handicap".
- **Cardinality.** 4,520 distinct raw values become 3,416 after trivial normalisation (lowercase, punctuation to space, whitespace collapsed). 2,494 of those are singletons, but they cover only 1.74% of the filled records. The distribution has a short head and a long tail.
- **Placeholders dominate.** Most filled records hold a placeholder such as `-`, `?` or a bare number, not a condition (counts in Key figures).
- **Non-condition content.** Household relations and occupations sit in the column: "deres børn", "hans kone", "tjenestefolk", "inderste,dagleier,huusfader". The 1801 values `M` and `K` look like the same effect. This may be a transcription or column-shift effect, and it is a question for Bárbara and Olivia (D-02).
- **Letter codes.** Leading codes such as "d døvstum", "s sindssyg" and "b blind" occur. Clustering merges most of them. "b blind" stays a separate cluster (D-06).

## Assumptions

- Empty and placeholder values carry no information about a condition.
- The most frequent spelling in a group is the best proposed standard.
- `fuzz.ratio >= 85` merges spelling variants, but it can also merge different terms. This is why the largest clusters go to a historian instead of being trusted blindly.
- Categories are suggestions. The historian decides.
- Guiding preference: minimise analyst degrees of freedom. No keyword lists, no extra thresholds, nothing to tune beyond what the EDA already fixed and showed.

## Decisions

Ids refer to the Phase 2 context file; they are also summarised in the project's Key Decisions table.

- **D-01 Placeholder rule.** A value is a placeholder when its trivially normalised form contains no letters. There is no list. Placeholders stay in File A with `value_type = placeholder` and no standard or category. They are excluded from File B and from all coverage figures. Bare numbers such as "1898" fall under this rule.
- **D-02 No misplaced-value flag.** Household and occupation values go through the same pipeline as everything else. They are frequent, so the impact ranking puts them in File B, where the historian decides. A keyword detector would add degrees of freedom.
- **D-03 Spelling method.** The Phase 1 EDA method, unchanged: trivial normalisation, then greedy leader clustering over the content values, visited by descending pooled count, each value joining the best leader at `fuzz.ratio >= 85`.
- **D-04 Proposed standard = cluster leader**, the most frequent trivially normalised form in the cluster.
- **D-05 Confidence = `fuzz.ratio(value, leader) / 100`.** It is 1.0 for the leader.
- **D-06 No prefix stripping.** "d døvstum" (87.5) and "s sindssyg" (88.9) merge into their clusters. "b blind" scores 83.3 against "blind" and stays a separate cluster, so the historian sees it. A letter may carry source meaning.
- **D-07 HARM-06 embeddings not implemented.** See Next steps. This is a deliberate deviation from the requirement text.
- **D-08 Categories come from an LLM, written once and committed.** `suggested_category` is a suggestion produced in-session and stored in `category_suggestions.parquet`. The script joins it and calls no API at runtime. Every row can be audited. `category_source` is `llm_suggestion`.
- **D-09 Vocabulary = the census's own terms.** døvstum/døv, blind, sindssyg, uden forstandsevner/idiot (including "forstanden berøvet"), krøbling/vanfør, multiple conditions, other/unclear, and "not a condition (suspected misplaced)". That last label also holds explicit negations such as "nej", "ingen" and "rask", because the fixed vocabulary has no separate bucket for them. The label is a suggestion only and does not change D-02.
- **D-10 Categories only for the 300 review clusters.** Values merged into one of them inherit its category. The tail has no category.
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

## Conclusions

- The mapping holds 3,416 trivially normalised values: 83 placeholders and 3,333 content values, which form 1,652 clusters. Only the 300 review clusters carry a category.
- One reviewer-day covers the top 300 clusters. Together they hold 1,877 distinct values and 95.15% of the real-content records (category record share 0.9515). 95% is already reached at 284 clusters, and 80% at 21.
- The remaining 1,352 clusters hold about 4.9% of the real-content records but a large share of the distinct values (1,456 of 3,333). The tail is small in records and large in distinct values.
- The category suggestions are a starting point. "other/unclear" is the largest bucket after idiocy and madness terms in records, mostly because of the 1801 single-letter codes ("s", "a", "d", "b"). "not a condition" is large in leaders (94 of 300) but small in records (3,065).

## Next steps

- **HARM-06 was deliberately not implemented (D-07).** The requirement asks for embedding-based grouping of values that differ in wording rather than spelling, for example "blind" and "svagsynet". I did not build it, for three reasons. A modern-text model brings modern-meaning bias (see the caveat below). It needs a large torch and model dependency. And it needs a cosine threshold, which is one more degree of freedom. It stays a candidate once Asbjørn's first pass shows which wording groups really matter.
- Category suggestions for the 1,352 tail clusters, after the first review.
- Use Asbjørn's decisions as an offset to standardise the tail automatically (step 3 of the brief's 2019 workflow).
- Questions for Bárbara and Olivia (for `QUESTIONS.md`):
  - Are the household and occupation values in `handicaps` transcription or column-shift effects?
  - Do placeholder dashes mean "checked, nothing" or "not asked"?
  - What do the 1801 values "M" and "K" mean?
  - What do the leading letter codes mean?
- Phase 4 builds the hand-in zip that carries File B (D-16).

## Caveat: modern-meaning bias

Terms for illness and disability changed meaning over time. The category suggestions come from a modern language model, so they are written in the census's own vocabulary (D-09), marked `category_source = "llm_suggestion"`, and left for the historian to decide. The same bias is the main reason the HARM-06 embeddings were descoped (D-07). A model trained on modern text reads "sindssyg" or "åndsvag" through today's meaning of the words, which can hide exactly the shifts a historian cares about.

## Key figures

These lines are printed by `harmonise.py`. Every number in this README comes from them or from the Phase 1 notebook.

```text
FACT task1.harmonise.records.filled=143597
FACT task1.harmonise.values.raw=4520
FACT task1.harmonise.records.placeholder=110387
FACT task1.harmonise.records.content=33210
FACT task1.harmonise.values.trivial=3416
FACT task1.harmonise.values.placeholder=83
FACT task1.harmonise.values.content=3333
FACT task1.harmonise.clusters=1652
FACT task1.harmonise.coverage.top100=0.9166
FACT task1.harmonise.coverage.top200=0.9405
FACT task1.harmonise.coverage.top300=0.9515
FACT task1.harmonise.coverage.top360=0.9561
FACT task1.harmonise.clusters_for_coverage.80=21
FACT task1.harmonise.clusters_for_coverage.90=71
FACT task1.harmonise.clusters_for_coverage.95=284
FACT task1.harmonise.review.size=300
FACT task1.harmonise.review.size_low=200
FACT task1.harmonise.review.size_high=360
FACT task1.harmonise.review.values=1877
FACT task1.harmonise.lookup.missing=0
FACT task1.harmonise.lookup.unused=0
FACT task1.harmonise.category.labels_used=8
FACT task1.harmonise.category.values=1877
FACT task1.harmonise.category.record_share=0.9515
FACT task1.harmonise.examples.records=1363
FACT task1.harmonise.examples.clusters_lt5=86
```

Reading guide: of 143,597 filled records, 110,387 (76.9%) are placeholders and 33,210 are real content. Coverage at 100, 200, 300 and 360 clusters is 91.66%, 94.05%, 95.15% and 95.61%. The review table has 300 rows; 86 of those clusters have fewer than 5 records, so the example file holds 1,363 records, not 1,500.
