# Brief: 5-19 — Wire the area chart end to end

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/lib/charts/TimeChart.svelte`, `packages/workflow-analytics/src/lib/charts/BuilderChart.svelte`, `packages/workflow-analytics/src/lib/charts/multi.test.ts` and a new `packages/workflow-analytics/tests/e2e/area.spec.ts`. Touch nothing else.
Commits: commit to the current branch when done evidence passes, plain-summary title, owned paths and the report only.
Report: before committing write `docs/plans/12-analytics-dashboard-overhaul/reports/5-19-area-wiring.md` (rubric `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-18. Runs alongside: nothing in Phase 5 touches these paths; the Go unit 5-13 is disjoint.
Budget: 4 files to read, about 60 lines to change, 30 tool turns. Past the budget stop, write a handoff, report `over budget`.

Run npm commands from `packages/workflow-analytics`. Use `E2E_PORT=4519` for e2e.

## Goal

5-18 gave `timeOption` an `area` option (line series with `areaStyle`, stacked), but `TimeChart` has no `area` prop and `BuilderChart` passes `stacked` for `chart=area`, so the builder's area chart still renders as stacked bars.

## Contract

1. `TimeChart.svelte` takes an optional `area` boolean prop and passes it to `timeOption` (`options.ts` already accepts it; read it first for the exact name).
2. `BuilderChart.svelte` passes `area` (not `stacked`) when `config.chart === 'area'`; `line` stays unstacked.
3. `tests/e2e/area.spec.ts`: on the builder route (look at `tests/e2e/builder.spec.ts` for its helpers, URL params and fixture), choose a time-bucketed measure with one dimension and `chart=area`; assert via the chart's data-table or the ECharts option (`getOption()` through the page) that series are `line` with `areaStyle`. Also open a `chart=multiples` view (`cost_usd` x `model` x `harness`, day bucket) and assert `expectSettled` returns, proving 5-18's ready signal in a browser.

## Done evidence

- The new e2e fails before the two edits (area) and passes after; report both outputs.
- `npm test`, `npm run build` and `npm run test:e2e -- builder.spec.ts area.spec.ts` pass.

## Report back

Under 1,500 tokens: status, what changed, before/after output, deviations, contradictions. Never resolve a contradiction silently.
