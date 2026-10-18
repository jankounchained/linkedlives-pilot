---
status: testing
phase: 02-task-1-harmonization
source: [02-VERIFICATION.md]
started: 2026-10-18T19:40:00Z
updated: 2026-10-18T19:40:00Z
---

## Current Test

number: 1
name: Accept or mask the rare free-text values in the committed File A (CR-01)
expected: |
  Either (a) accept the recorded user decision (02-REVIEW-DISPOSITION.md: CR-01 deferred 2026-10-18; the repo goes only to Rigsarkivet, which holds the source data; disclosed in the Task 1 README Outputs section) as an explicit exception to the rule that committed outputs are pa_id + aggregates only, or (b) mask rare values in the committed File A and purge the earlier versions from git history.
awaiting: user response

## Tests

### 1. Accept or mask the rare free-text values in the committed File A (CR-01)
expected: Either (a) accept the recorded decision (CR-01 deferred and disclosed; the repo goes only to Rigsarkivet, delivered as the D-16 zip, not pushed to any remote) as an explicit exception to the committed-outputs rule, or (b) mask rare values in File A and purge history. 2,813 of 3,333 content values occur in at most 2 records.
result: [pending]

### 2. Read the Task 1 README and skim the review CSV
expected: task1_handicaps/README.md can be followed from the EDA findings to the next steps without opening the code. data/outputs/task1/handicaps_review.csv opens in a Danish-locale spreadsheet with æ/ø/å intact, 300 rows and empty decision and comment columns. The suggested categories are historically plausible, especially the 111 labels written in 02-03, and the inherited ones are recognisable.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
