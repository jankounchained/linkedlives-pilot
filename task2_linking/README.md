# Task 2: linking the 1846 and 1850 Danish West Indies censuses

Status: designed, not implemented, for lack of time. There is no linking script and no `links.parquet`. This note gives the planned method and its evidence. Each number is an EDA fact from [`eda.ipynb`](eda.ipynb) (section given as §) or is derived from those facts. None is a linking result.

The file holds 43,891 records from 1846 and 39,523 from 1850 (§1), FamilySearch partner data. Emancipation in July 1848 falls between the two censuses.

## Planned method

### 1. Candidate pairs

A candidate pair is a record from 1846 and a record from 1850 of the same sex whose birth years differ by at most w years. Birth year is census year minus age: `inp_PR_BIR_YEAR_EST` equals exactly that for all 83,076 records where it can be checked (§1), so it adds no evidence. Island, birthplace and surname are score features, not blocks, so a person who moved loses points instead of dropping out.

The width w follows from the age noise, measured on 1,381 unique-name anchors: records whose sex, given name and surname occur once in each census (§2). Their age difference centres on the expected 4 years (median 4.0, IQR 3.0, §2), but the tails are wide, as the window-cost table shows (§3):

| Window w | Candidate pairs | Share of sex-only pairs | Anchors kept |
|---|---|---|---|
| sex only | 853.8M | 100% | 100% |
| ±1 | 38.4M | 4.5% | 47.5% |
| ±2 | 63.6M | 7.4% | 59.4% |
| ±3 | 88.7M | 10.4% | 64.9% |
| ±5 | 140.0M | 16.4% | 70.6% |

The anchors were 88% free in 1846 (§2), so for enslaved people this spread is only a lower bound. I would start with ±5. A narrow window loses true links silently, and loses more of them for enslaved people. Inside the window the age gap is scored, not gated. The 949 records of 1846 and 310 of 1850 without a sex or an age cannot be blocked (§3).

### 2. Score

The score is a sum of feature contributions with hand-set log weights, so each link can be explained term by term.

| Feature | Contribution | Evidence |
|---|---|---|
| Given name | rapidfuzz similarity of the normalised names, weighted by name frequency, so a rare name counts more | filled for over 99% of records (§1) |
| Surname | similarity, only when both are present; a missing surname counts 0 | filled for 91.3% of free and 4.5% of enslaved people in 1846 (§4a) |
| Age | penalty growing with the distance of the age difference from 4 years | anchors: median 4.0, IQR 3.0 (§2) |
| Island | bonus when equal | 89.1% of anchors agree (§4b) |
| Birthplace | small bonus when the normalised values are equal | 56.8% of anchors agree (§4b) |
| Owner | planned, but drops out | empty for every 1850 record (§1, §4a) |

Free/enslaved status is an analysis dimension, not a feature: emancipation changes it by design, and the 1850 flag is empty. No phonetic keys: abbreviations and mixed-language names break them. The anchor agreement rates guide the weights but are optimistic for enslaved people. Anchors share the normalised surname by construction, so they cannot show how often a true match changes surname, and a surname disagreement costs little.

### 3. Assignment

Greedy one-to-one: take the pairs in score order, accept a pair when both records are still unlinked, and stop at a minimum score. `margin` is the accepted score minus the best competing score of either record. `confidence_band` (high, medium, low) combines score and margin, with thresholds read off their distributions. One-to-one caps the result at 39,523 links, 90% of the 1846 records (derived from §1), and deaths and departures lower it further.

### 4. Household second pass

Two households, one per census, count as matched when a high-confidence link joins them. Co-residents in a matched pair get a bonus, smaller in large households, and the assignment runs again. The output reports how many links the pass added and how many it changed. Households are large enough for this to matter (median 6 records in 1846, 10 in 1850, §5). They may not be the same unit in both censuses, though: in 1850 they are fewer (3,531 to 2,452), larger (St. John median 11 to 32) and rarely single-person (11.1% to 2.6% of households, §5).

### 5. Output

`links.parquet` holds `pa_id_1846`, `pa_id_1850`, `score`, `margin` and `confidence_band`, with each `pa_id` at most once. It contains only identifiers and numbers, so it may be committed. The per-link feature breakdown and the sample pairs are record-level and stay in the gitignored `data/outputs/task2/`.

## Plausibility evaluation, without ground truth

- The age-difference distribution of the links per band, against the anchors' (median 4.0, IQR 3.0). A band that spreads much wider is suspect.
- Link rates by sex, island and 1846 free/enslaved status (1850 has no flag). Lower rates for people enslaved in 1846 are expected, and they are reported, not hidden.
- The share of links that change island, against 10.9% of anchors (derived from §4b).
- How many anchors end up linked to their anchor partner. This is a consistency check, not ground truth, since anchors rest on the same names as the score.
- A seeded random sample of pairs per band, read on my own machine under the no-record-level rule. Only the counts per band (plausible, implausible, unsure) are committed.

## Data issues found in the EDA

- The free/enslaved flag and both owner fields are empty for all 39,523 records of 1850 (§1). In 1846 the flag reads Free 16,686, Enslaved 24,844 and blank 2,361. The status change across emancipation cannot be observed in this file.
- The anchors are not ground truth either. For 157 of them the 1850 age is more than 10 years below the 1846 age, and for 74 it is more than 20 years above it (§2). Some are probably different people who share a name. Only 62 of the 1,381 anchors were enslaved in 1846 (§2).
- Surnames are missing for 60.5% of the 1846 records and 47.3% of the 1850 records (§1). The share with a surname rises on every island, on St. Croix from 26.7% to 40.7% (§4a), so a surname that appears only in 1850 is normal.
- Birthplace agrees for only 56.8% of anchors (§4b), and a few birthplace values are pure digits (§1).
- Places are FamilySearch's modern standard names ("..., United States Virgin Islands"). St. Croix falls from 28,390 to 23,606 records. The whole fall is among records placed at island level only (21,050 to 15,456), while Christiansted and Frederiksted grow (§1). That may be migration, deaths or an incomplete transcription.

## Limitations and next steps

- Not implemented. The evaluation above would show whether the design holds.
- Not scalable by design: ±5 gives 140.0M candidate pairs for 83,414 records, so scoring would run in chunks per sex and birth year. Blocking for the metropolitan Danish censuses (2M+ records) is a next step.
- Hand-set weights. Next: Splink (Fellegi–Sunter with EM-estimated weights), as a comparison and a check on them.
- An LLM review layer for medium- and high-confidence links (merge, do not merge, merge with another candidate), if the partner terms allow sending records to a model. Manual annotation for the remaining hard, low-confidence pairs.
- The 1846 owner as a group key in the second pass: people who shared an owner in 1846 and share a household in 1850.
- An age-heaping (digit preference) check per 1846 status group.
