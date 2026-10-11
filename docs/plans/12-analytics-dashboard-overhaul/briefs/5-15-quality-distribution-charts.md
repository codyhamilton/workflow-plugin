# Brief: 5-15 — Quality: distribution charts beside the baseline

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/quality/+page.svelte`, `packages/workflow-analytics/tests/e2e/quality.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-15-quality-distribution-charts.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-03.
Runs alongside: 5-07, 5-08, 5-09, 5-10, 5-14, 5-16. The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 5 files to read, about 120 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Quality: distribution charts beside the baseline".
2. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — "4-11-quality": the brief said table only, DESIGN.md says charts; this unit closes the contradiction (Carried 5).
3. `src/routes/quality/+page.svelte` and `tests/e2e/quality.spec.ts` — the kind selector, `scores` and `baselines`, test ids.
4. `src/lib/charts/box.ts` and `BoxChart.svelte` (5-03) — settled props (`BoxRow`, `marker`).
5. `src/lib/types.ts` — `Scores`, `Baselines`; `tests/e2e/fixture.ts` for the scores fixture.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Quality shows the window's score distribution per check as a box plot with the all-time baseline median marked on the same row, above the existing table.

## Contract

`scores` rows give `min, p25, median, p75, max, n` per check; `baselines.checks[name]` gives `p25, median, p75, n` (all time). One `BoxRow` per scores check: the five numbers from `scores`, `marker` = the baseline median for that name when present. Checks with `n = 0` are omitted. Use `BoxChart` with `testid="quality-dist"`. The existing kind selector, table and test ids stay; the chart and table both show.

## Changes

Add the chart only; no new request. Add tests to `quality.spec.ts`: `quality-dist` renders for the default kind and its data table (toggle) has one row per scored check with the fixture's numbers; switching kind re-renders it; dark theme renders (`data-theme`). Recount against the fixture; never edit expected values to match the code.

### Keep untouched

The table, the kind selector, `scoresParams` use and error handling.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm run test:e2e -- quality.spec.ts` → the new tests fail before and pass after; existing tests pass.
- `npm test` and `npm run build` → pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
