# Brief: 4-01 — Quality score drift bands

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/quality/+page.svelte`; `packages/workflow-analytics/src/lib/types.ts` (add `ScoreSeries*` types only); `packages/workflow-analytics/src/lib/params.ts` (add `scoreSeriesParams` only); `packages/workflow-analytics/src/lib/charts/ScoreBandChart.svelte`; `packages/workflow-analytics/src/lib/charts/score-series.ts`; `packages/workflow-analytics/src/lib/charts/score-series.test.ts`; `packages/workflow-analytics/tests/e2e/quality.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/4-01-quality-score-series.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 4-05-explore-usage-columns, 4-06-e2e-pricing-fixture.
Budget: 16 files to read, about 400 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 4 `/quality` outcome; Domain: Analytics reads **`GET /v1/analytics/score-series`**; Domain: Report interaction (“A score series leaves the gap”, brush on a time axis sets the custom range); Decisions (“The quality chart leaves a gap where a bucket has no point”).
2. `packages/workflow-analytics/src/routes/quality/+page.svelte` — today’s `/scores` + baselines + `BoxChart`.
3. `tools/workflow/internal/serve/analytics_score_series_test.go` — response JSON shape.
4. `packages/workflow-analytics/src/lib/charts/TimeChart.svelte` — `onbrush` wiring pattern (read only; do not edit).
5. `packages/workflow-analytics/tests/e2e/quality.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Quality shows per-check score drift over the window (median line and p25–p75 band), the all-time baseline median on each panel, and keeps the existing window box plot against that baseline; kind switch and brush reload both views.

## Contract

Phase 4 outcome:

- On `/quality`, for one kind, each check with points shows a median line and a p25–p75 band over the window, and the all-time baseline median is drawn on that panel. A bucket with no point is a gap, not a zero. The box plot against the baseline remains. Switching kind reloads both. Brushing the band sets the custom window in the URL and the panel follows.

`GET /v1/analytics/score-series` from DESIGN.md (binding):

- `kind` is required and is exactly one of `design`, `brief`, `report`. `bucket` is required and is `day`, `week`, or `month`.
- Response: `{"kind","bucket","checks":[{"name","points":[{"t","n","p25","median","p75"}]}]}`. Points are sparse. Checks with no points are omitted. Percentiles use the `/scores` method, rounded to 3 decimal places. The route does not emit `partial`. The quality chart leaves a gap where a bucket has no point.
- A point's population is the distinct content hashes with a version timestamp in that bucket. This does not sum to `GET /v1/analytics/scores`, which is the latest score per hash over the whole window. The page does not present them as the same population.

Report interaction: brush on a time axis sets the custom range.

## Changes

- Fetch `GET /v1/analytics/score-series` alongside existing `/scores` and `/baselines` when kind and window params are ready. Reuse `view.paramsFor('rest')` plus `scoreSeriesParams(params, kind, bucket)` mirroring `scoresParams`.
- Add a bucket control (`day` | `week` | `month`) on the page (URL param is fine). Pick default bucket with the same cap logic other reports use when the window is wide (grep `pickBucket` usage on `/trends` or `/usage`).
- Render one band chart per check that has at least one score-series point (or per check returned — align with outcome “each check with points”). Use `ScoreBandChart`: median line, shaded p25–p75, horizontal mark at baseline median when present. Do not zero-fill missing buckets.
- Keep `BoxChart` (`quality-dist`) and the numeric table as they are today; baseline marker behavior unchanged.
- Wire `onbrush` on the band chart(s) to `view.setWindow`.
- Kind tabs must refetch score-series, scores, and baselines together (same effect as today for scores/baselines).

### Keep untouched

`BoxChart.svelte`, `TimeChart.svelte`, backend routes, and Phase 3 report pages.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- src/lib/charts/score-series.test.ts` from `packages/workflow-analytics` → passes (option builder maps sparse points to line + band series with gaps, baseline mark optional).
- `npx playwright test tests/e2e/quality.spec.ts` → passes, including new tests: stubbed score-series returns two buckets for one check and omits a middle bucket → chart/table shows a gap (not 0) at that time; brush on the band chart sets `from`/`to` in the URL; kind switch requests `/v1/analytics/score-series` with the new `kind`; existing box/table tests still pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
