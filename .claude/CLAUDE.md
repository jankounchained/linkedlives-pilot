<!-- GSD:project-start source:PROJECT.md -->

## Project

**Linking Lab Pre-Interview Tasks**

A lean micro-project answering the Linking Lab (Danish National Archives, HisPeR) pre-interview tasks for the data scientist / data manager positions: **Task 1 — explore and prepare the `handicaps` census variable for standardisation**, and **Task 2 — design and implement a simple method to link the 1846 and 1850 Danish West Indies censuses**. It is delivered as a single private git repo (code + small outputs, no raw data) to Bárbara Revuelta-Eugercios and Olivia Robinson, and serves as the basis for the technical part of the interview.

**Core Value:** Show sound, transparent, source-critical problem solving on realistic HisPeR data within a ~3.5-hour budget — clear assumptions, decisions and conclusions matter more than completeness or polish.

### Constraints

- **Timeline:** ~3.5h of work, hard deadline 23:59 2026-10-18 — everything must be lean
- **Data governance:** raw data and named record-level outputs never enter git — not even the private repo (licence may not allow it); FamilySearch partner data is not ours to publish. Code lives in git; data doesn't. Committed outputs: `pa_id` + aggregates only.
- **Format:** parquet for all artifacts; CSV export only for historians; no Excel
- **Tech stack:** Python via `uv` (system Python 3.14, no global packages); polars + pyarrow; rapidfuzz for string similarity
- **Deliverable form:** scripts are the final product; notebooks are only for sharing EDA

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
