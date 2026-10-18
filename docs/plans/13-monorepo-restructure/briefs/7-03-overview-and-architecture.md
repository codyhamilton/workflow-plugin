# Brief: 7-03 — OVERVIEW and ARCHITECTURE

Consumer: a phase 7 worker on the restructure branch after Phases 5 and 6 are closed.
Owned paths:
`docs/OVERVIEW.md`,
`docs/ARCHITECTURE.md`,
`docs/plans/13-monorepo-restructure/reports/7-03-overview-and-architecture.md` (new).
Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/7-03-overview-and-architecture.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phases 5 and 6.
Runs alongside: `7-01`, `7-02`, `7-04`, `7-05`.
Budget: 12 files to read, about 120 lines to change, 40 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 7 outcome [judgement]; Architectural Implications; Domain: Names trailer dual-read.
2. `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` — grep `workflow`, `WORKFLOW_`, `plugins/yakka`, `packages/workflow`.
3. `plugins/yakka/.claude-plugin/marketplace.json` (via repo root marketplaces) — current plugin name `yakka`.

## Goal

Stable overview docs describe one `yakka` plugin, the monorepo layout, and the trailer dual-read rule.

## Contract

Cited, binding (Phase 7 outcome): "[judgement] `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` and the contract sections of `docs/design/*` describe the yakka names and state the trailer dual-read rule." (This unit owns the first two files only; `7-04` owns `docs/design/*`.)

Cited, binding (Domain: Names): "Writers emit `Yakka-Phase: <slug>:<n>`, `Yakka-Phase: <slug>:done`, a PR body starting `Yakka-Plan: docs/plans/<NN>-<slug>/`, and a `yakka-report` fence. Readers accept `Workflow-Phase` / `Yakka-Phase`, `Workflow-Plan:` / `Yakka-Plan:`, and both fences, permanently, through one shared key list in `tools/driver/`."

Cited, binding (Solution Shape): single marketplace plugin at `plugins/yakka`; packages and tools trees; maintainer skills at `.claude/skills/` (not shipped to end users).

## Changes

- Replace product/plugin/binary names with `yakka` where they name this repo's shipped surfaces (`plugins/yakka`, `packages/yakka`, `bin/yakka`, marketplace `yakka`).
- Component map: `plugins/yakka`, `packages/{yakka,hooklog,yakka-analytics,opencode-yakka-hooks}`, `tools/`, `.claude/skills/`.
- Env and state paths: `YAKKA_*`, `~/.local/share/yakka/`, `~/.cache/yakka/`, etc., per Domain: Names path table.
- Add a short **Trailer dual-read** subsection (or bullet under protocol): quote the Domain: Names writers/readers sentence above verbatim or as a single block quote; do not paraphrase the acceptance rule.
- Keep the common noun "workflow" only where it means the method, not the product name.

### Keep untouched

Dated `docs/lab/` references that are notebooks. Do not edit `docs/design/*` (unit `7-04`).

## Done evidence

Before: `python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^docs/(OVERVIEW|ARCHITECTURE)'` → non-zero lines.

After:

- `python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^docs/(OVERVIEW|ARCHITECTURE)'` → no output.
- `rg 'Yakka-Phase|dual-read|Workflow-Phase' docs/OVERVIEW.md docs/ARCHITECTURE.md` → at least one hit documenting both writer and reader forms.
- `rg 'plugins/yakka' docs/ARCHITECTURE.md` → at least one hit.

## Report back

Under 1,500 tokens. Status, scan output before/after, deviations, contradictions.
