---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Scanner does not look at Series reprs, glimpse() or any non-table text, so an identifier column passes"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Column lists are exact-match, case-sensitive, incomplete, and have drifted from the notebooks' own masks"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Text tables truncate headers, so exact header matching fails for `print(df)` / stream outputs"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Any count-like header disables rule C and exempts a column from rule B; the \"name with count below 5\" policy is not enforced"
  - id: WR-05
    severity: warning
    disposition: open
    title: "Hook path rules are case-sensitive and top-level-only; parquet and csv are not blocked outside `data/`; the hook fails open if `git diff` fails"
  - id: WR-06
    severity: warning
    disposition: open
    title: "Empty or relative `LINKING_LAB_DATA` redirects raw-data writes into an unignored, unblocked location"
  - id: WR-07
    severity: warning
    disposition: open
    title: "Task 2 notebook states \"The committed notebook carries no outputs\", which is false"
  - id: IN-01
    severity: info
    disposition: open
    title: "Masking lists differ between the two notebooks"
  - id: IN-02
    severity: info
    disposition: open
    title: "Raw free-text `handicaps` strings are shown below the min-count threshold"
  - id: IN-03
    severity: info
    disposition: open
    title: "Punctuation-only values become an empty \"normalised value\" and are counted"
  - id: IN-04
    severity: info
    disposition: open
    title: "Parish key can collide when a level is missing"
  - id: IN-05
    severity: info
    disposition: open
    title: "Inconsistent whitespace handling between `filled()` and grouping"
  - id: IN-06
    severity: info
    disposition: open
    title: "Planning jargon in deliverables meant for the interviewers"
  - id: IN-07
    severity: info
    disposition: open
    title: "Small quality items"
open: 14
total: 14
recorded: 2026-10-18T16:12:52.603Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| WR-06 | warning | open | - |
| WR-07 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
