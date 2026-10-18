# Brief: 7-07 — CHANGELOG rows for identifiers 7-01 missed

Consumer: a phase 7 fixer after `7-01` landed and verification compared `git diff d7b78c1 f11f303` `WORKFLOW_*` tokens to the `3.0.0` table.
Owned paths:
`CHANGELOG.md` (only the `## 3.0.0` section),
`docs/plans/13-monorepo-restructure/reports/7-07-changelog-missing-identifiers.md` (new).
Touch nothing else. Do not edit `tools/release/scan_residual_names.py`. Do not rewrite `reports/7-01-changelog-migration-guide.md`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/7-07-changelog-missing-identifiers.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `7-01`.
Runs alongside: nothing.
Budget: 4 files to read, about 20 lines to change, 15 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 7 outcome [cmd] CHANGELOG clause; Domain: Names `WORKFLOW_` rule.
2. `CHANGELOG.md` — the `## 3.0.0 — 2026-10-18 — rename to yakka` environment table only.

## Goal

The `3.0.0` environment map accounts for every `WORKFLOW_*` identifier Phases 5–6 removed that the table still omits.

## Contract

Cited, binding (Phase 7 outcome): "[cmd] The CHANGELOG rename entry carries one `YAKKA_*` row for every `WORKFLOW_*` identifier removed by Phases 5–6, every path in the state-path table, remove-and-install commands for Claude Code, Cursor, Codex and OpenCode, and the numbered maintainer actions."

Cited, binding (Domain: Names): "Every identifier that starts with `WORKFLOW_` becomes `YAKKA_` with the same suffix, in shipped code and in maintainer tools, except `WORKFLOW_QUALITY_`."

Settled from the phase 4 close (`d7b78c1`) to the phase 6 close (`f11f303`). Do not re-inventory. Add these and nothing else:

| Was | Becomes |
|---|---|
| `WORKFLOW_ALIGNMENT_CRITERIA` | `YAKKA_ALIGNMENT_CRITERIA` |
| `WORKFLOW_ALIGNMENT_INSTRUCTIONS` | `YAKKA_ALIGNMENT_INSTRUCTIONS` |
| `WORKFLOW_LEGACY` | `YAKKA_LEGACY` |
| `WORKFLOW_REPORT_FENCE` | `REPORT_FENCE` (no `YAKKA_` prefix; Python constant in `tools/driver/report.py`) |
| `WORKFLOW_SIGNAL_STATE_DIR` | removed (unused test assignments; no successor) |
| `WORKFLOW_ARTIFACT_SUBMIT_CLI` | removed (retired-pattern token; no `YAKKA_` successor) |

`WORKFLOW_QUALITY_*` stays the exception already written. Do not add a `YAKKA_QUALITY_URL` row.

## Changes

- Insert the six rows into the existing `### Environment variables` table, in alphabetical order with the other rows.
- For the three rows whose Becomes cell is not `YAKKA_*`, keep that cell exactly as the table above states.
- Leave every other `3.0.0` subsection and every older changelog section unchanged.

### Keep untouched

State paths, harness steps, `.gitignore`, MCP note, maintainer actions, and the `WORKFLOW_QUALITY_*` / `WORKFLOW_HOOKLOG_CLI` exception paragraph.

## Done evidence

Before: `rg 'WORKFLOW_ALIGNMENT_CRITERIA|WORKFLOW_LEGACY|WORKFLOW_REPORT_FENCE|WORKFLOW_SIGNAL_STATE_DIR|WORKFLOW_ARTIFACT_SUBMIT_CLI' CHANGELOG.md` → no matches in the `3.0.0` section.

After: each of those five tokens, plus `WORKFLOW_ALIGNMENT_INSTRUCTIONS`, appears in the `3.0.0` table with the Becomes cell from the contract table. `python3 tools/release/scan_residual_names.py --scope all` → exit 0.

## Report back

Under 1,500 tokens. Status, the six rows, scan exit code, deviations.
