---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Committed File A ships verbatim free-text census strings, including personal narrative and a surname"
  - id: WR-01
    severity: warning
    disposition: open
    title: "`load_lookup` silently drops stale leaders that `--check` later rejects"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Record-level output guard can be defeated by an empty or repo-level `LINKING_LAB_DATA` (re-raise of deferred WR-04, with reproduction)"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`main_checkout_root` can resolve the data root to an unrelated parent repository (re-raise of deferred WR-05, delivery path)"
  - id: IN-01
    severity: info
    disposition: open
    title: "Main run writes the committed File A before the File B guard runs"
  - id: IN-02
    severity: info
    disposition: open
    title: "README overstates the digit guard (\"numbers ... never merged\")"
  - id: IN-03
    severity: info
    disposition: open
    title: "Private cross-module import and stale suppression"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "README misattributes the single-letter codes to 1801 (false finding in the deliverable)"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "assert_local_only only checks the path is under DATA_ROOT, not that it is gitignored"
  - id: WR-05
    severity: warning
    disposition: deferred
    title: "main_checkout_root assumes the common git dir is named .git, directly under the checkout"
open: 7
total: 10
recorded: 2026-10-18T19:23:07.627Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| CR-02 | critical | fixed | fixed in 02-03, 1c611b7: README and 02-01-SUMMARY attribute the single letters s, a, d, b to 1901 and treat 1801 M/K as a separate case (not in the current review) |
| WR-04 | warning | deferred | deferred (D-19): the guard holds with the default data root (the main checkout's gitignored data/); only a mis-set LINKING_LAB_DATA defeats it (not in the current review) |
| WR-05 | warning | deferred | deferred (D-19): the project runs from plain checkouts and git worktrees, where the common git dir is .git (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
