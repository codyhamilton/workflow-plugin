# Brief: 7-04 — Design doc contract sections

Consumer: a phase 7 worker on the restructure branch after Phases 5 and 6 are closed.
Owned paths:
`docs/design/01-event-model-and-ingest.md`,
`docs/design/02-edge-capture.md`,
`docs/design/03-remote-service.md`,
`docs/design/04-advisory-surface.md`,
`docs/design/05-distribution.md`,
`docs/design/07-analytics-site.md`,
`docs/design/system-architecture.md`,
`docs/design/conversation-indexer.md`,
`docs/plans/13-monorepo-restructure/reports/7-04-design-contract-sections.md` (new).
Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/7-04-design-contract-sections.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phases 5 and 6.
Runs alongside: `7-01`, `7-02`, `7-03`, `7-05`.
Budget: 20 files to read, about 200 lines to change, 55 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 7 outcome [judgement]; Architectural Implications (design docs list); Domain: Names; Packages and Plugin contracts for paths.
2. `tools/release/scan_residual_names.py` — `design_sections_to_skip` (dated `YYYY-MM-DD` headings stay historical).
3. Each owned `docs/design/*.md` — grep `workflow`, `WORKFLOW_`, `packages/workflow`, `bin/workflow`, `tools/hooklog`.

## Goal

Rewrite **contract sections** (layout, paths, env, binaries, hooks, release) in every design doc to yakka names and add the trailer dual-read rule where the doc describes plan/PR artifacts.

## Contract

Cited, binding (Phase 7 outcome): "[judgement] `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` and the contract sections of `docs/design/*` describe the yakka names and state the trailer dual-read rule."

Cited, binding (Architectural Implications): "The rename phases then rewrite the contract sections of those docs, plus `docs/design/04-advisory-surface.md` and `docs/design/system-architecture.md`, to the yakka names, and add the trailer dual-read rule to the PR Artifact Seam and the phase-boundary contract."

Cited, binding (Domain: Names, writers/readers): "Writers emit `Yakka-Phase: <slug>:<n>`, `Yakka-Phase: <slug>:done`, a PR body starting `Yakka-Plan: docs/plans/<NN>-<slug>/`, and a `yakka-report` fence. Readers accept `Workflow-Phase` / `Yakka-Phase`, `Workflow-Plan:` / `Yakka-Plan:`, and both fences, permanently, through one shared key list in `tools/driver/`."

Cited, binding (Solution Shape / Packages): binary package `packages/yakka`, module `github.com/codyhamilton/yakka/packages/yakka`, `cmd/yakka`, hook edge `packages/hooklog`, plugin install root `plugins/yakka`, Cursor hooks `./script/...`.

Cited, binding (scan): in `docs/design/*.md`, sections whose heading contains `YYYY-MM-DD` remain excluded from residual scan — do not rewrite dated research sections; update undated contract/layout sections only.

## Changes

- Path literals: `packages/yakka`, `packages/yakka-analytics`, `packages/opencode-yakka-hooks`, `plugins/yakka/bin/yakka`, `yakka-<os>-<arch>` release artifacts.
- Env and state: `YAKKA_*` (except document `WORKFLOW_QUALITY_*` where the legacy quality service is named).
- `05-distribution.md` Layout: packages, `tools/`, `plugins/yakka` (already partially done in Phase 4 — align remaining rows).
- `04-advisory-surface.md` and any phase-boundary / PR Artifact Seam prose: insert dual-read rule (quoted sentence above).
- `system-architecture.md` maintainer lab row → `.claude/skills/`; runtime row → Go `yakka` binary.

### Keep untouched

Sections matching `DATE_SECTION` in `scan_residual_names.py` (headings with `YYYY-MM-DD`). Historical plan references inside `docs/plans/` paths in prose are fine.

## Done evidence

Before: `python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^docs/design/'` → non-zero.

After:

- `python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^docs/design/'` → no output.
- `rg 'Yakka-Plan|Workflow-Phase' docs/design/04-advisory-surface.md docs/design/system-architecture.md` → at least one dual-read mention across those two files.
- `rg 'packages/yakka' docs/design/05-distribution.md` → at least one hit.

## Report back

Under 1,500 tokens. Status, scan before/after, deviations, contradictions.
