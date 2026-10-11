# Brief: 4-07 — Trends: any measure over time, in-range buckets and brush-to-zoom

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/trends/+page.svelte`, `tests/e2e/trends.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-07-trends.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06, 4-08 to 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4407`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 8 files to read, about 250 lines to write, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": brush-to-zoom, "each chart picks the finest bucket within the 400-bucket cap", Trends.
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01), `src/lib/buckets.ts` (4-02), `src/lib/charts/TimeChart.svelte` (4-04) — exports and props only.
3. `src/routes/trends/+page.svelte` and `tests/e2e/trends.spec.ts` — the old metric, bucket and group controls and what the spec asserts.
4. `tools/workflow/internal/serve/analytics_query.go` — the `/schema` handler (which measures take which dims) and the `/query` parameters.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Trends plots any schema measure over the window, grouped by one allowed dimension, with a bucket that is always in range, and a horizontal drag narrows the window.

## Contract

- Data: `/query` through the client, `view.paramsFor('query', {measure, bucket, dim?, top: '8'})`. `/query` rows are `{t, k: string[], v}`; `bucket` is one of `hour`, `day`, `week`, `month`. At most 400 buckets per unit: the bucket control offers only buckets for which `bucketCount(...) <= 400`, defaults to `pickBucket(...)` (the finest in range), and when the window changes so the chosen bucket is out of range it falls back to the finest in range. This works for `all`.
- Measure and group lists come from `analytics/schema` (`{measures:[{name, unit, dims}], buckets}`), fetched once and cached. A group option is offered only if it is in the chosen measure's `dims` (an unsupported pairing is a 400 server-side; the page must not be able to select one). A `kind` filter on `hook_events` is listed by the server in `ignored_filters`; the shell shows that notice.
- Route params (kept in the URL with `view.setParam`): `metric`, `bucket`, `group`. Defaults: `hook_events`, auto, none. Test ids kept: `trends-metric`, `trends-bucket`, `trends-group`.
- Brush: `TimeChart` `onbrush({from, to})` calls `view.setWindow(from, to)`. The URL then has `from` and `to` and no `range`, and the brushed window refetches.
- The chart is `testid="trends-chart"`. Its data-table toggle replaces the old `series-<key>-<t>` cells; the spec reads the table.
- Missing buckets are zero-filled (`fillBuckets` in `src/lib/series.ts` for `day` and `week`, or your own for `hour` and `month`), so a gap reads as zero, not as a join.

## Changes

Rewrite `+page.svelte` on `view`, the client and `TimeChart`. Slots: `trends-main`, `trends-schema`. Rewrite `trends.spec.ts` against the recounted fixture (`HOOK_EVENTS_BY_DAY`, `USAGE_*`): the default render matches `HOOK_EVENTS_BY_DAY` through the table toggle; `cost_usd` grouped by `model` shows the two priced days; the group list for a measure without that dim lacks it; with `range=all` the bucket control does not offer `hour` or `day` when that exceeds 400 buckets, and the request that goes out has `all=1` and a bucket in range (read it from `trackRequests`); `brush(page, 'trends-chart', 0.25, 0.75)` leaves `from` and `to` in the URL, the window is narrower, and `preset-*` buttons are not pressed; the timing assertion (under 1,000 ms from change to `expectSettled`).

### Keep untouched

The control test ids `trends-metric`, `trends-bucket`, `trends-group`.

## Done evidence

Run the old `trends.spec.ts` against the new page first and report which tests fail before you rewrite it.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- trends.spec.ts` → all pass, including the brush, the all-time bucket test and the timing assertion.
- A burst of five metric changes inside 250 ms issues one `analytics/query` request (`trackRequests`).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
