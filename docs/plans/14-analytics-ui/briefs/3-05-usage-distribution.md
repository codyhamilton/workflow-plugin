# Brief: 3-05 — Usage models and distribution histograms

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/usage/+page.svelte`; `packages/workflow-analytics/src/lib/types.ts` (add `DistributionResponse` types only); `packages/workflow-analytics/src/lib/charts/DistributionChart.svelte`; `packages/workflow-analytics/src/lib/charts/distribution.ts`; `packages/workflow-analytics/src/lib/charts/distribution.test.ts`; `packages/workflow-analytics/tests/e2e/usage.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/3-05-usage-distribution.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-03-time-chart-interactions.
Runs alongside: 3-04-trends-stacked-drill, 3-07-hooks-timeseries.
Budget: 14 files to read, about 350 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 3 `/usage` outcome; Domain: Analytics reads **`GET /v1/analytics/distribution`** (measures, bins, filters); Domain: Report interaction (model drill, brush).
2. `packages/workflow-analytics/src/routes/usage/+page.svelte` — current queries and charts.
3. `tools/workflow/internal/serve/analytics_distribution.go` — response JSON shape (read the handler, not the whole serve tree).
4. `packages/workflow-analytics/tests/e2e/usage.spec.ts` and `tests/e2e/fixture.ts` — seeded window models.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The usage report compares models with cost and token totals, stacked cost and token time series by model, per-call histograms from the distribution route, and consistent model drill and brush across every panel.

## Contract

Phase 3 outcome:

- On `/usage`, with the seeded e2e window, the page shows cost and token totals by model, a time series of cost split by model, and a time series of tokens split by model. A control draws the per-call histogram for `cost_usd` and for each token measure in the distribution contract, on that measure's bin edges. Clicking a model filters every panel to it. Shift-click excludes it. Brushing either time series sets the window in the URL and every panel follows.

`GET /v1/analytics/distribution` from DESIGN.md (binding): measures `cost_usd`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`; default `grain=call`; `dim` omitted uses row `k` `"all"`; bin edges fixed per measure; filters `repo_id`, `harness`, `model`, `conversation_id` via `view.paramsFor('rest', …)`.

Report interaction: model is a shared filter key; `__other__` not clickable on charts.

## Changes

- Token time series: fetch `tokens_out` (or both in/out if already in table — outcome requires one tokens-over-time chart) with `dim=model` and the same bucket as cost-over-time; render with `TimeChart` stacked by model like cost.
- Wire both time charts with `onbrush` → `view.setWindow` and model drill on bars/table/series consistent with today’s table and cost bar behavior.
- Distribution: selector for the seven measures; `getJSON` to `analytics/distribution` with `measure`, `grain=call`, window params from `view.paramsFor('rest')`, and active model filters. Render bins with `DistributionChart` using API `lo`/`hi`/`n` (shared fixed edges — do not recompute bins client-side).
- Model click on histogram when `dim=model` rows exist is not required for call grain without `dim`; histogram reflects filtered window. Table/bar/time/histogram all respect the same `view.state` filters.
- Keep unpriced bar inert rules and `__other__` inert behavior on the cost bar chart.

### Keep untouched

Backend routes, `query.ts`, and other chart components except new distribution files.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- src/lib/charts/distribution.test.ts` from `packages/workflow-analytics` → passes (option builder maps bins to ECharts series using token/cost edge labels).
- `npx playwright test tests/e2e/usage.spec.ts` → passes, including new tests: distribution control switches measure and requests `/v1/analytics/distribution?measure=cost_usd`; tokens-over-time request includes `dim=model`; brushing `usage-over-time` sets `from`/`to` in the URL and reloads distribution slot; model bar click filters histogram and time series (assert fewer models or chip visible).
- Update the “seven query requests” test if the page adds distribution calls — assert the new count explicitly rather than 7.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
