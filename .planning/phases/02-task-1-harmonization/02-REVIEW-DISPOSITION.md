---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: deferred
    title: "Committed File A ships verbatim free-text census strings, including personal narrative and a surname"
  - id: WR-01
    severity: warning
    disposition: deferred
    title: "`load_lookup` silently drops stale leaders that `--check` later rejects"
  - id: WR-02
    severity: warning
    disposition: deferred
    title: "Record-level output guard can be defeated by an empty or repo-level `LINKING_LAB_DATA` (re-raise of deferred WR-04, with reproduction)"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "`main_checkout_root` can resolve the data root to an unrelated parent repository (re-raise of deferred WR-05, delivery path)"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Main run writes the committed File A before the File B guard runs"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "README overstates the digit guard (\"numbers ... never merged\")"
  - id: IN-03
    severity: info
    disposition: deferred
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
open: 0
total: 10
recorded: 2026-10-18T19:23:07.627Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | deferred | deferred (user decision 2026-10-18, hand-in): disclosed in task1_handicaps/README.md (Outputs). The repo goes only to Rigsarkivet, which holds the source data, and the D-16 zip carries record-level File B anyway. Before any wider sharing: mask rare values in the committed File A (complete mapping local under data/outputs/) and purge the earlier File A versions from history |
| WR-01 | warning | deferred | deferred (user decision 2026-10-18, hand-in): --check fails on stale lookup rows (lookup_leaders_equal_review_leaders), so a stale lookup cannot pass the documented check. Later: make the main run exit 2 as well |
| WR-02 | warning | deferred | deferred (user decision 2026-10-18, hand-in): only an empty or repo-level LINKING_LAB_DATA defeats the guard, and the root README documents an absolute path. Later: ignore empty values and add a git check-ignore test |
| WR-03 | warning | deferred | deferred (user decision 2026-10-18, hand-in): the D-16 zip carries .git, so the data root resolves to the unzipped folder. Later: only call git when REPO_ROOT/.git exists |
| IN-01 | info | deferred | deferred (user decision 2026-10-18, hand-in): write order and set atomicity only; each file is still written atomically |
| IN-02 | info | deferred | deferred (user decision 2026-10-18, hand-in): README wording; the guard compares digit runs, so numbers written as words can still merge |
| IN-03 | info | deferred | deferred (user decision 2026-10-18, hand-in): code hygiene, no behaviour change |
| CR-02 | critical | fixed | fixed in 02-03, 1c611b7: README and 02-01-SUMMARY attribute the single letters s, a, d, b to 1901 and treat 1801 M/K as a separate case (not in the current review) |
| WR-04 | warning | deferred | deferred (D-19): the guard holds with the default data root (the main checkout's gitignored data/); only a mis-set LINKING_LAB_DATA defeats it (not in the current review) |
| WR-05 | warning | deferred | deferred (D-19): the project runs from plain checkouts and git worktrees, where the common git dir is .git (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
