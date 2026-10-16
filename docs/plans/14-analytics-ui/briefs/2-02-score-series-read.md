# Brief: 2-02 — Score series read

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `tools/workflow/internal/store/score_series.go`; `tools/workflow/internal/store/score_series_test.go`; `tools/workflow/internal/serve/analytics_score_series.go`; `tools/workflow/internal/serve/analytics_score_series_test.go`; `tools/workflow/internal/serve/serve.go` (register `GET /v1/analytics/score-series` only); `tools/workflow/internal/serve/analytics_bench_test.go` (score-series bench cases and smoke route coverage for `score-series/`). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/2-02-score-series-read.md` and include it in the commit.
Depends on: `2-01-distribution-read` (`store/percentile.go` must exist).
Runs alongside: nothing.
Budget: 10 files to read, about 350 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — **`GET /v1/analytics/score-series`**, executions `series` bucket `t` rule (same bucket starts), Phase 2 score-series fixture bullet.
2. `tools/workflow/internal/store/analytics.go` — `WindowScores` (contrast: whole-window latest per hash, not per bucket).
3. `tools/workflow/internal/store/percentile.go` — from unit 2-01.
4. `tools/workflow/internal/serve/analytics.go` — `parseFilter`, bucket/week handling on `/series` if useful for `week`/`month` starts.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The read API exposes `GET /v1/analytics/score-series`: per-check percentile points over time buckets for one artifact kind, with sparse points and the bucket-start `t` rule aligned to executions series.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Domain: Analytics reads, **`GET /v1/analytics/score-series`**. Settled:

- `kind` required, exactly one of `design`, `brief`, `report` (same validation as `/scores`).
- `bucket` required: `day`, `week`, or `month`. Wider than 400 days or more than 400 buckets → 400 `{"error":"range too wide"}`.
- `t` is bucket start, RFC3339 in `tz`. `week` starts Monday, `month` on the first, both in `tz` (same rule as executions `series`).
- Population per point: distinct content hashes with a version timestamp in that bucket; several versions of one hash in the bucket contribute the latest only. A hash may appear in multiple buckets. This does not sum to `GET /v1/analytics/scores`.
- Response: `{"kind","bucket","checks":[{"name","points":[{"t","n","p25","median","p75"}]}]}`. Sparse points; checks with no points omitted. Percentiles use `/scores` method, rounded to 3 decimal places. No `partial`.

## Changes

- Store method scans `facts` + `scores` with bucket assignment on artifact_version `ts` (respect window filter; `kind` on the route, not the shared `kind` filter dimension unless design applies — score-series uses the route `kind` param like `/scores`).
- Handler: require `kind` and `bucket`, validate bucket enum, apply `parseFilter` with appropriate week cap when `bucket=week`, reject >400 buckets, shape JSON via catalog checks like `analyticsScores`.
- Tests: fixture where two versions of one hash in one bucket yield the latest score; a bucket with no versions produces no point (not a zero). Serve tests for 400 on bad bucket/kind and 200 shape.
- Register route. Bench cases `score-series/<preset>` with `kind=design&bucket=day`. Smoke route list requires `score-series/`.

### Keep untouched

`WindowScores` behavior for `/scores`. Do not change distribution or executions handlers.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `go test ./internal/store/ -run TestScoreSeries -count=1` from `tools/workflow` → passes, including latest-in-bucket and omitted-empty-bucket cases.
- `go test ./internal/serve/ -run 'TestScoreSeries|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow` → passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output before and after, deviations, contradictions. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
