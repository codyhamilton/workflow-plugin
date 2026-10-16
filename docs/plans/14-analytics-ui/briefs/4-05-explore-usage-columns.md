# Brief: 4-05 — Explore model, cost, and norm event

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/explore/+page.svelte`; `packages/workflow-analytics/tests/e2e/explore.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/4-05-explore-usage-columns.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 4-01-quality-score-series, 4-06-e2e-pricing-fixture.
Budget: 8 files to read, about 80 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 4 `/explore` outcome.
2. `packages/workflow-analytics/src/routes/explore/+page.svelte` — `COLUMNS` and `toRows`.
3. `tools/workflow/internal/serve/analytics_explore_test.go` or grep explore handler for row fields (read response fields only).
4. `packages/workflow-analytics/tests/e2e/explore.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Explore’s Perspective table includes `model`, `cost_usd`, and `norm_event` from the API slice.

## Contract

Phase 4 outcome:

- On `/explore`, the table columns include `model`, `cost_usd`, and `norm_event`.

Existing explore route fields are unchanged beyond exposing these columns; the API already returns them on usage and hook rows.

## Changes

- Add `model`, `cost_usd`, and `norm_event` to `COLUMNS` and `SCHEMA` (`cost_usd` as number or string consistent with other numeric columns in `toRows`).
- Map API values in `toRows` (empty string for null; cost as number when parseable).
- Do not change fetch params or Perspective plugins.

### Keep untouched

Backend, other routes, WASM loading path.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/explore.spec.ts` → passes, including a new test: after load, evaluate Perspective schema or column names and assert `model`, `cost_usd`, and `norm_event` are present; row count assertions unchanged.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
