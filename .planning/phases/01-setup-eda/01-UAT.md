---
status: complete
phase: 01-setup-eda
source: [01-VERIFICATION.md]
started: 2026-10-18T16:20:00Z
updated: 2026-10-18T16:22:35.936Z
---

## Current Test

[testing complete]

## Tests

### 1. Skim both committed notebooks for the judgment-tier prohibitions
expected: Every caveat sits next to the numbers it qualifies and no section reads as a decision (no Phase 1 decision stated or implied; empty handicaps never "no handicap"; column descriptions never official; anchor figures next to the lower-bound/bias caveat)
result: skipped
reason: "Deferred follow-up: I can’t skim them right now. Defer UAT and move to the next phase"

### 2. Fresh-clone reproducibility
expected: In a fresh clone, `uv sync --locked` builds the environment from uv.lock, `git config core.hooksPath .githooks` activates the hook, and after placing the raw files `uv run python scripts/prepare_data.py --check` prints OK for all six parquet files and the Guide
result: skipped
reason: "Deferred follow-up: I can’t skim them right now. Defer UAT and move to the next phase"

## Summary

total: 2
passed: 0
issues: 0
pending: 0
skipped: 2
blocked: 0

## Gaps

[none]

## Deferred Follow-Ups

- test: 1
  idea: "I can’t skim them right now. Defer UAT and move to the next phase"
  deferred_at: 2026-10-18
- test: 2
  idea: "I can’t skim them right now. Defer UAT and move to the next phase"
  deferred_at: 2026-10-18
