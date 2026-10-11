# Brief: 5-04 — Chart fixes: usage legend overlap and Hooks bar hit area

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/lib/charts/options.ts`, `src/lib/charts/options.test.ts`, `src/lib/charts/BarChart.svelte`, `tests/e2e/hooks.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-04-chart-legend-and-bar-hit-area.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-01, 5-02, 5-03 (it owns `EChart.svelte`; you must not edit it), 5-11, 5-12, 5-14, 5-15, 5-16. The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 6 files to read, about 90 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — "Phase 4 verification" and "Carried (Phase 4)" item 9: the usage cost-over-time legend overlaps the x-axis labels; the Hooks clickable bar covers only the bar.
2. `src/lib/charts/options.ts` — `timeOption` (legend and grid, lines 94-135) and `barOption` (lines 55-93).
3. `src/lib/charts/BarChart.svelte` and `src/lib/charts/EChart.svelte` (props `onclick`, `cursorFor`) — read only for EChart.
4. `src/routes/hooks/+page.svelte` and `tests/e2e/hooks.spec.ts` — how bars are clicked (`clickBar` in `tests/e2e/helpers.ts`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The usage legend no longer overlaps the axis labels, and a click anywhere on a Hooks bar's row (the whole category band, including the label gutter and empty track) drills, not only on the painted bar.

## Contract

From the Phase 4 verification: "Usage cost-over-time legend overlaps the x-axis labels; the Hooks clickable bar covers only the bar." DESIGN.md: "Every chart mark and table row for a dimension value applies that value as a filter (shift-click excludes it). `__other__` is not clickable."

The legend and the grid must not share space: with a legend (more than one series) the grid reserves room for it (legend at the top, grid `top` raised, or legend at the bottom with `bottom` raised above the axis labels; choose one and cover it in a test). `barOption` keeps its `data-testid` geometry (`BAR_GRID` in `tests/e2e/helpers.ts`): if you change the grid, change nothing in `helpers.ts` (not yours) — keep `left: 120, right: 24, top: 8, bottom: 24` for bars.

## Changes

- `timeOption`: reserve legend space as above; test in `options.test.ts` that with two or more series the legend rectangle (its `top`/`bottom` and the grid's) cannot overlap, and with one series there is no legend and the grid is unchanged.
- `barOption`: make the whole row clickable, e.g. with a full-width background series (`showBackground`, transparent) or a second invisible `bar` series at 100% of the axis, so `params.name` is the row key from a click anywhere on the row; `__other__` rows stay inert (keep the existing guard) and the hover cursor follows. Keep the same `onclick` payload shape `BarChart.svelte` already forwards.
- `hooks.spec.ts`: add one test that clicks the empty track of a short bar (same y as the bar, x near the right edge of the grid) and expects the filter chip; do not change other tests. Use `clickBar` for the normal case; for the empty-track click compute the point from the chart's bounding box with the same geometry.

### Keep untouched

The exports and signatures of `options.ts`, the `barOption` selection and `__other__` behaviour, and every existing test.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- options` → the new legend and bar tests fail before and pass after.
- `npm run test:e2e -- hooks.spec.ts` → all pass, including the empty-track click.
- `npm test` and `npm run build` → pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
