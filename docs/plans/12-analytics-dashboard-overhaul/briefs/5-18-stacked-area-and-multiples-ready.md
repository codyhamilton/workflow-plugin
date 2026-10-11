# Brief: 5-18 — Stacked area type and small-multiples settle signal

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/lib/charts/options.ts`, `options.test.ts`, `SmallMultiples.svelte`, `multi.test.ts`, and `packages/workflow-analytics/src/lib/charts/EChart.svelte` only if the area series needs registering. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, plain-summary title, owned paths and the report only.
Report: before committing write `docs/plans/12-analytics-dashboard-overhaul/reports/5-18-stacked-area-and-multiples-ready.md` (rubric `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-04, 5-05, 5-07. Runs alongside: 5-17 is after this; nothing else.
Budget: 5 files to read, about 80 lines to change, 30 tool turns. Past the budget, stop, write a handoff, report `over budget`.

Run npm commands from `packages/workflow-analytics`. Use your own `E2E_PORT` if you run e2e.

## Goal

Two defects found by 5-05 and 5-07: (1) the builder's `area` chart renders stacked bars because `timeOption` in `options.ts` has no area variant (`BuilderChart.svelte` passes `stacked` for `area`); (2) `SmallMultiples.svelte` emits no `data-ready`, so `expectSettled` never settles on `kind=multiples` panels.

## Contract

1. `timeOption` gains an `area` option: when set, series are `type: 'line'` with `areaStyle` and `stack: 'total'`; `stacked` (without `area`) keeps today's stacked-bar behaviour. `BuilderChart.svelte` is not owned: if it must change to pass `area`, report it as a contradiction rather than editing it; first check whether `TimeChart.svelte` props already allow it (read only).
2. `SmallMultiples.svelte` renders `data-ready="true"` on its root once its child charts have mounted, `"false"` before, matching the other chart components (see `GroupedBar.svelte` lines 48-50).
3. Tests in `options.test.ts` (area emits line series with `areaStyle` and a shared `stack`; stacked alone still emits bars) and `multi.test.ts` (ready attribute). Failing before, passing after.

## Done evidence

- `npm test` passes; the new tests fail before and pass after (report both outputs).
- `npm run build` passes.

## Report back

Under 1,500 tokens: status, what changed, before/after output, deviations, contradictions. Never resolve a contradiction silently.
