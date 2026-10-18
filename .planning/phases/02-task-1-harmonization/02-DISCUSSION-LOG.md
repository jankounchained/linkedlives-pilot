# Phase 2: Task 1 — Harmonization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-18
**Phase:** 02-task-1-harmonization
**Areas discussed:** Non-handicap content, Spelling normalisation, Categories & wording, File B impact & size

---

## Non-handicap content

| Option | Description | Selected |
|--------|-------------|----------|
| Flag, keep in File A | value_type=placeholder; excluded from File B and coverage | ✓ |
| Treat as empty | map to null | |
| Drop from File A | remove entirely | |

| Option | Description | Selected |
|--------|-------------|----------|
| Flag + a few into File B | value_type=suspected_misplaced | |
| Flag only | mark, keep out of File B | |
| Treat like any value | no special handling | ✓ (after follow-up) |

**User's choice:** Placeholders flagged. For misplaced values the user asked: "How will you flag them? That adds degrees of freedom to the analysis, which is not something we want." Claude proposed: placeholder rule = no letters after trivial normalisation (nothing to tune); no misplaced flag or keyword list. User: "accepted. Placeholders only."
**Notes:** The detection question (curated keyword list) became moot.

## Spelling normalisation

| Option | Description | Selected |
|--------|-------------|----------|
| Trivial + ratio 85 | EDA method, one fixed parameter | ✓ |
| Trivial only | zero parameters | |
| Ratio 90 | stricter | |

Standard value: cluster leader ✓ (vs most frequent raw spelling). Confidence: fuzz.ratio/100 ✓ (vs score + support). Prefixes: no extra rule ✓ (vs strip single-letter prefix).

## Categories & wording

| Option | Description | Selected |
|--------|-------------|----------|
| Descope embeddings to next step | modern bias, heavy dependency, threshold | ✓ |
| Embeddings on frequent anchors | meets HARM-06 as written | |

Category: LLM lookup, committed ✓ (vs substring rules, vs no category). Vocabulary: historical source terms ✓ (vs modern groups). Rare tail: category left blank ✓ (vs suggest for all).

## File B impact & size

Impact: record count ✓ (vs count × uncertainty, vs per-year top-N). Size: fixed one day = 300 ✓ (vs until 95% coverage = 280, vs 360).
Row unit: user said "the historian will need to judge the cluster in some context, ie will need to see the whole records". Follow-up: two files keyed by cluster_id (Claude's choice after the user said "just commit all needed and then we'll send a zipped repo"), 5 seeded-random records per cluster ✓, record-level File B kept local ✓. Claude flagged the commit-vs-local tension; the user confirmed: git stays clean, the zip from the working tree includes the local File B outputs ("yes that is good").

## Claude's Discretion

Script names/layout, File A column names, exact historical category labels, seed, CSV encoding, the two-file structure for File B.

## Deferred Ideas

Embedding grouping (HARM-06), tail categorisation, using Asbjørn's decisions for automatic standardisation of the tail, the Phase 4 zip build.
