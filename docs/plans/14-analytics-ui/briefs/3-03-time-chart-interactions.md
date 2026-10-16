# Brief: 3-03 — Time chart series click and brush

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/lib/charts/TimeChart.svelte`; `packages/workflow-analytics/src/lib/charts/options.ts` (only if needed for series click styling); `packages/workflow-analytics/src/lib/charts/options.test.ts` (extend only for any option change you make). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/3-03-time-chart-interactions.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-01-filter-bar-ten-dims, 3-02-overview-kpi-links, 3-06-repos-cost-rank, 3-08-builder-scalar-heatmap.
Budget: 6 files to read, about 80 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Domain: Report interaction (clicking a mark whose key is a shared filter value; `__other__` and empty key not clickable).
2. `packages/workflow-analytics/src/lib/charts/TimeChart.svelte` — brush wiring.
3. `packages/workflow-analytics/src/lib/charts/EChart.svelte` — click dispatch.
4. `packages/workflow-analytics/src/lib/charts/BarChart.svelte` — shift-click drill pattern.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Time series charts support legend/series click drill (include/exclude) and keep the existing brush-to-window behavior, so trends and usage routes can wire filters without duplicating ECharts logic.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Domain: Report interaction:

- Clicking a mark whose key is a shared filter value includes it. Shift-click excludes it. `__other__` and the empty key are not clickable. `hour_of_day`, `weekday`, and check names are not filters.
- Brush on a time axis sets the custom range.

## Changes

- Add optional props to `TimeChart`: `filterDim?: DimKey` (import from `$lib/urlstate`) and `onseries?: (d: { key: string; shift: boolean }) => void`.
- On ECharts `click`, when the target is a series/legend item, map `seriesName` back to the dimension key: ignore `all`, `__other__`, and `''`; call `onseries` with native shift key when `filterDim` and `onseries` are set.
- Do not drill from axis labels or blank plot area.
- Keep `onbrush` and brush initialization unchanged.
- Stacked mode must still emit one key per series name (cost-by-model and stacked area depend on this).

### Keep untouched

Other chart components, routes, and table toggle behavior.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- src/lib/charts/options.test.ts` from `packages/workflow-analytics` → passes.
- Add a focused unit test in `options.test.ts` only if you change `timeOption`; otherwise document manual verification in the report: mount is not required if e2e covers it in dependent units.
- `npm test -- src/lib/charts/options.test.ts -t timeOption` → passes after any option tweak.

Dependent routes (3-04, 3-05, 3-07) own Playwright proof of end-to-end drill/brush; this unit’s evidence is tests above plus a short report note that `TimeChart` exports the new props.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
