---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Clustering merges values that differ only in digits, so proposed_standard states a wrong number at high confidence"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "README misattributes the single-letter codes to 1801 (false finding in the deliverable)"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "load_lookup and check_lookup validation lets null labels and conflicting duplicates through"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Merged members inherit the leader's category even when they name a different condition"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "CSV formula injection in the historian CSV files"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "assert_local_only only checks the path is under DATA_ROOT, not that it is gitignored"
  - id: WR-05
    severity: warning
    disposition: deferred
    title: "main_checkout_root assumes the common git dir is named .git, directly under the checkout"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Dead or misleading FACT lines and stale lint suppression"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "Example sampling reuses the same permutation for every cluster of equal size"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "--check does not test the README or the lookup against the actual clustering"
---

# Phase 02 code review disposition

10 findings: 6 fixed in plan 02-03, 4 deferred (D-19)

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | fixed in 02-03, 56f2eb5: D-17 digit guard in leader_clusters; `--check` digit_runs_match_leader violations=0 |
| CR-02 | critical | fixed | fixed in 02-03, 1c611b7: README and 02-01-SUMMARY attribute the single letters s, a, d, b to 1901 and treat 1801 M/K as a separate case |
| WR-01 | warning | fixed | fixed in 02-03, 4d8c6e8: load_lookup exits 2 on null cells or duplicated leaders; check_lookup tests both |
| WR-02 | warning | fixed | fixed in 02-03, 4d8c6e8: `category_inherited` in File A and the review table |
| WR-03 | warning | fixed | fixed in 02-03, 4d8c6e8: csv_safe escapes risky leading characters in the CSV copies only; `--check` cells_safe |
| WR-04 | warning | deferred | deferred (D-19): the guard holds with the default data root (the main checkout's gitignored data/); only a mis-set LINKING_LAB_DATA defeats it |
| WR-05 | warning | deferred | deferred (D-19): the project runs from plain checkouts and git worktrees, where the common git dir is .git |
| IN-01 | info | deferred | deferred (D-19): cosmetic (always-zero FACT, stale noqa, wording); no effect on outputs |
| IN-02 | info | deferred | deferred (D-19): sampling stays uniform within each cluster and reproducible; the cross-cluster correlation biases no cluster's examples |
| IN-03 | info | fixed | fixed in 02-03, 4d8c6e8: `--check` lookup_leaders_equal_review_leaders compares the sets in both directions |
