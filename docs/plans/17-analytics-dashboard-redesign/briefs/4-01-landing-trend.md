# Brief: 4-01 — Landing trend view

Consumer: the phase 4 implementation worker.
Owned paths: `packages/yakka-analytics/src/routes/+page.svelte`, `packages/yakka-analytics/tests/e2e/overview.spec.ts`, `packages/yakka-analytics/tests/e2e/session.spec.ts` (only the two tests named below), `packages/yakka-analytics/tests/e2e/explore.spec.ts` (only `the overview does not load Perspective`), `packages/yakka-analytics/tests/hosted/hosted.spec.ts` (only `overview loads same-origin with no token` and `immutable assets are cached for a year`), `docs/design/07-analytics-site.md` (the `/` row of the route table, and the overview KPI link sentences in the Drill-down bullet). The report path below is allowed. Touch nothing else. No other new files. Do not add a dependency.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to `origin` branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/4-01-landing-trend.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit. Test results, not a file list, model, or cost.
Depends on: phases 1, 2, and 3 (already on this branch).
Runs alongside: nothing.
Budget: 16 files to read, about 450 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Landing trend view, Assumption 1, and Phase 4 — Landing trend view. Those are the contract. Phase 5's first outcome sentence is out of scope; read it only so you do not build it.
2. `packages/yakka-analytics/src/lib/aggregate.ts` — `AggregateRequest`, `TrendAsk`, `TrendResult`, `Series`, and `export async function aggregate`. Grep `const SLOT`. Do not re-read the ask branches.
3. `packages/yakka-analytics/src/lib/analysis/chart-frame/index.ts` and `types.ts` — `TrendChart`, `TrendFrameData`. The frame does not fetch.
4. `packages/yakka-analytics/src/routes/+page.svelte` — the current overview this unit replaces. Note `sessionTenant` / `sessionGate.ready` only; do not preserve the summary, sparkline, or heatmap fetches.
5. `docs/design/07-analytics-site.md` — the route-table row for `/`, and the Drill-down sentences that start `Each overview KPI links`.
6. `packages/yakka-analytics/tests/e2e/session.spec.ts` — `collector overview sends tenant from /v1/me on summary` and `session summary mock loads overview tiles`.
7. `packages/yakka-analytics/tests/e2e/explore.spec.ts` — `the overview does not load Perspective` only.
8. `packages/yakka-analytics/tests/hosted/hosted.spec.ts` — the two tests named in Owned paths.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A logged-in user opening `/` with an empty query string sees two trends, `hook_events` and `cost_usd`, over the preselected window, drawn in the chart frame. They do not choose a measure, a chart, or a saved analysis, and the old overview picture is gone.

## Contract

Cited from `DESIGN.md`, Domain: Landing trend view, Assumption 1, and Phase 4. Settled.

> `/` with an empty query string shows two trends for the preselected window, read through the aggregation boundary and drawn in the chart frame.
>
> - The gate has allowed the load. The query string is empty. The person does not choose a measure, a chart type, or a saved analysis first.
> - The picture is two `ask: trend` results, same window and bucket, measures `hook_events` and `cost_usd`. See Assumption 1.
> - The picture is not the current `/` content: the nine KPI tiles, the grouped counts, and the weekday-by-hour heatmap.

Assumption 1, same file:

> Yes. Two `ask: trend` results, same window and bucket, measures `hook_events` and `cost_usd`. Nine KPI tiles are not required.

Phase 4 outcome, same file:

> A logged-in user opening `/` with an empty query string sees two `ask: trend` results, measures `hook_events` and `cost_usd`, same window and bucket, over the preselected window (design 7's thirty-day judgement when `from` is omitted), without choosing a measure, a chart, or a saved analysis. The chart's module is not `src/lib/charts/EChart.svelte`. The nine KPI tiles and the weekday-by-hour heatmap are not that picture.

Aggregation boundary, the sentences this call must satisfy:

> one request, one result. Callers do not name `/v1/analytics/*` or `GET /v1/baselines`.
>
> The request carries `tenant` for a session read, from the `GET /v1/me` body. A bearer read uses the token's tenant and does not invent one.
>
> Omitted range resolves as design 7 Shared filter: `to` now, `from` thirty days earlier.

Phase 5 owns this sentence. Do not implement it:

> A control on the landing trend opens the investigation at `/` with an `ask` query, on the landing window and on `hook_events` and `cost_usd`.

## Changes

Replace the body of `src/routes/+page.svelte`. The route no longer renders the overview. There is no second picture for a non-empty query: this unit does not read `ask`, does not apply URL filters, and does not add a control that opens the investigation. `/?repo_id=` still shows the same two preselected trends.

Two calls to `aggregate`, one measure each. Both use the same window and the same bucket.

- Window: `{ tz }` only. `tz` is `Intl.DateTimeFormat().resolvedOptions().timeZone`. Omit `from`, `to`, and `preset`, so the boundary applies the thirty-day judgement. Do not pass the `30d` preset. Do not import `view`.
- Bucket: `day` on both. An hour bucket over that thirty-day span exceeds the boundary's 400-bucket refusal and returns no points. `day` is inside the cap. Do not call `pickBucket`.
- Tenant: `isCollectorMode() ? tenantNameFromMe(sessionGate.me) : null`, from `$lib/api`, `$lib/session-gate`, and `$lib/session-gate.svelte`, as the page does now. Pass `tenant` only when that value is a non-empty string. Do not call `aggregate` until `sessionGate.ready`.
- Ask: `{ ask: 'trend', measure: 'hook_events', bucket: 'day' }` and `{ ask: 'trend', measure: 'cost_usd', bucket: 'day' }`. No breakdown dim.

The default fetcher inside `aggregate` uses one slot, `aggregate`. A second in-flight `getJSON` on that slot supersedes the first. Await the `hook_events` call, then the `cost_usd` call. Do not start them together. Import `Superseded` from `$lib/query` only to ignore that rejection. Do not call `getJSON`. A rejection that is not `Superseded` calls `setError` from `$lib/state.svelte`; a fulfilled call calls `clearError`.

Draw each result with `TrendChart` from `$lib/analysis/chart-frame`. Map the result onto `TrendFrameData`: `measure` and `bucket` are the ones you requested (`TrendResult` does not echo them); `series` is `(result.series ?? []).map((s) => ({ name: s.key, points: s.points }))`. Do not pass `onhover`, `onbrushend`, or `ondrill`. Test ids: `landing-trend-hook_events` and `landing-trend-cost_usd`. A text label on each chart is the measure name. It is not an input.

Do not import `$lib/charts/` or mount `EChart.svelte`, `Heatmap`, or `Sparkline`. The page source does not contain `analytics/summary`, `analytics/query`, or `getJSON(`.

Amend `docs/design/07-analytics-site.md` in two places only.

- The route-table row whose path is `` `/` ``. Replace the report and lens cells so the row states that `/` is the landing: two trends, measures `hook_events` and `cost_usd`, same window and bucket, over the preselected window. Not the nine KPI tiles, the grouped counts, or the weekday-by-hour heatmap.
- In the Drill-down bullet, the sentences from `Each overview KPI links` through `Overview counts do not link to `/explore`.`. Replace that stretch with one sentence: `/` does not show those KPI tiles and does not link them to `/conversations`, `/hooks`, `/trends`, or `/usage`. Leave the zero-fill sentence and the rest of that bullet as they are.

Tests that still require the old picture:

- Replace `tests/e2e/overview.spec.ts` with the checks in Done evidence. Do not keep assertions on `summary-*`, `overview-heatmap`, `overview-spark-*`, KPI hrefs, or filter-driven numbers.
- `session.spec.ts`: `collector overview sends tenant from /v1/me on summary` — `tenant=acme` is on the `analytics/query` requests for `hook_events` and `cost_usd`. Do not require `analytics/summary`. `session summary mock loads overview tiles` — fulfill `analytics/facets` and `analytics/query` (the boundary calls facets, then query) and expect the two landing test ids. Do not expect `summary-conversations`. Leave every other test in that file unchanged.
- `explore.spec.ts`: in `the overview does not load Perspective`, wait on `landing-trend-hook_events` instead of `summary-conversations`. Keep the Perspective assertion.
- `hosted.spec.ts`: in `overview loads same-origin with no token`, drop the `SUMMARY_ALL` tile loop; wait on the two landing test ids; keep the same-origin and no-authorization assertions. In `immutable assets are cached for a year`, wait on `landing-trend-hook_events` instead of `summary-conversations`; keep the cache-control assertion. Do not run the hosted config.

### Keep untouched

`src/lib/aggregate.ts`, `src/lib/analysis/chart-frame/`, `src/routes/+layout.svelte`, the session gate, report routes, `src/lib/charts/`, `src/lib/view.svelte.ts`, `packages/yakka/internal/serve`, and `packages/yakka/internal/store`. Do not fix the two failing `tests/e2e/shell.spec.ts` cases carried from phase 2. Do not fix the `aggregate.ts` type errors carried from phase 3. Do not add the investigation control.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npx playwright test tests/e2e/overview.spec.ts` → fails first because the landing test ids are absent, then passes. `page.goto('/')` has an empty query string. `landing-trend-hook_events` and `landing-trend-cost_usd` are visible and `data-ready="true"`. `overview-summary`, `overview-heatmap`, and `summary-conversations` are absent. The `analytics/query` requests are exactly two, measures `hook_events` and `cost_usd`, both `bucket=day`, the same `from` and the same `to`, and `Date.parse(to) - Date.parse(from)` is 30 days. Neither query URL carries `repo_id`. `page.goto('/?repo_id=r1')` still shows those two test ids, and those query URLs still have no `repo_id`.
- `cd packages/yakka-analytics && npx playwright test tests/e2e/session.spec.ts tests/e2e/explore.spec.ts` → passes, including the tenant check and the Perspective check above.
- `cd packages/yakka-analytics && npm test` → the package unit suite passes.
- Observable: `src/routes/+page.svelte` does not import `$lib/charts/` or `EChart.svelte`, and does not call `getJSON`. `git diff --name-only` against the parent commit includes no path under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
