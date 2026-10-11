# Brief: 5-07 — Chart builder route

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/builder/+page.svelte` (new), `packages/workflow-analytics/tests/e2e/builder.spec.ts` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-07-builder-route.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-02, 5-05.
Runs alongside: 5-08 (after 5-06), 5-09, 5-10, 5-14, 5-15, 5-16. The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 7 files to read, about 220 lines to change, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Chart builder", "The URL is the view", "Date window" (each chart picks the finest bucket within the cap unless one is set), and the Phase 5 outcome.
2. `src/lib/builder.ts` (5-02) and `src/lib/charts/BuilderChart.svelte` (5-05) — the settled interfaces; do not re-derive rules.
3. `src/lib/view.svelte.ts` — `paramsFor('query', extra)`, `setParam`, `drill`, `facetsReady`.
4. `src/routes/trends/+page.svelte` — the closest existing page: schema load, `pickBucket`, `getJSON`, brush, `untrack` and the `facetsReady` guard. Copy its request pattern.
5. `src/lib/query.ts` exports (`getJSON`, `Superseded`), `src/lib/state.svelte.ts` (`setError`, `clearError`).
6. `tests/e2e/trends.spec.ts` and `tests/e2e/helpers.ts` — spec style.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A Builder page where any legal measure, up to two dimensions, a bucket and a chart kind can be chosen, the choice lives in the URL, and the chart renders from one `/query`.

## Contract

The page loads `GET /v1/analytics/schema` once (`getJSON('builder-schema', 'analytics/schema', new URLSearchParams())`) and builds every control from it. Test ids (5-17 depends on them): selects `builder-measure`, `builder-dim-1`, `builder-dim-2`, `builder-bucket`, `builder-chart-type`, number input `builder-top`; the chart is `builder-chart` (the `testid` given to `BuilderChart`); `builder-notice-range` for the out-of-range message.

Rules:
- Config is read from the URL with `parseConfig` and written with `view.setParam`-style navigation (one navigation per change, keep filter params and route params). The pairing guard is structural: `builder-dim-1`/`-2` list only `allowedDims(schema, measure, chosen)` plus a "none" option; `builder-chart-type` lists only `allowedCharts(dims.length, bucket)`; changing the measure drops dims it does not support. A control never offers an unsupported value (so the server's 400 is unreachable from the UI).
- One request: `view.paramsFor('query', {measure, dim: dims, bucket, top})` through `getJSON('builder-query', 'analytics/query', params)`. All time uses `all=1` only with `bucket=none`; with a time bucket clamp as Trends does. When `pickBucket` says the chosen bucket exceeds the cap for the window, do not request; show `builder-notice-range`. A new window with no explicit `b` uses `pickBucket`.
- A mark click on a dimension value calls `view.drill(dim, key, {shift})` when that dimension is a filter key (`DIM_KEYS` in `urlstate.ts`; `hour_of_day`, `weekday` and `stage` are not, and their marks do nothing); brush calls `view.setWindow`.
- Slots, error handling, `Superseded` and `facetsReady` as in Trends. A non-`Superseded` error calls `setError`.

## Changes

Defaults when the URL has no `m`: `defaultConfig(schema)`. Write `builder.spec.ts` against the fixture ledger: (1) the page opens with a default chart and no console error; (2) measure `cost_usd`, dims `model` then `harness`, bucket `day` renders `builder-chart` with `data-kind="multiples"` once chosen (set via the selects) and at least one `builder-chart-panel`; (3) switching measure to `rejections` leaves `builder-dim-1` offering only `stage`, `hour_of_day`, `weekday` (no `harness`, `repo_id`, `model`); (4) a pasted URL `?m=hook_events&d=weekday&d=hour_of_day&b=none&c=heatmap` renders a heatmap; (5) reload keeps the config. Use `expectSettled`.

### Keep untouched

Nothing else changes; the layout (5-06) already links to `/builder`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm run test:e2e -- builder.spec.ts` → fails before (route missing), passes after.
- `npm test` and `npm run build` → pass.
- With the fixture serve, `builder-dim-1` for `rejections` has exactly the options the schema returns, read from `/v1/analytics/schema` in the test, not hard-coded.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
