# Brief: 2-03 — Executions shape and series

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `tools/workflow/internal/store/analytics.go` (executions paging, counts, and new series read only); `tools/workflow/internal/store/analytics_test.go` (executions-related tests only); `tools/workflow/internal/serve/analytics.go` (`canonFilter`, `analyticsExecutions`, and cursor binding for `shape`/`bucket` only); `tools/workflow/internal/serve/analytics_test.go` or a new `analytics_executions_test.go` if you add one (executions HTTP tests only); `tools/workflow/internal/serve/analytics_bench_test.go` (executions cases with `shape` and `bucket`). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/2-03-executions-shape-series.md` and include it in the commit.
Depends on: `2-02-score-series-read` (sequential edits to shared `analytics.go` / bench file).
Runs alongside: nothing.
Budget: 8 files to read, about 400 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — **`GET /v1/analytics/executions`** delta (repeatable `shape`, optional `bucket`, `series`), Phase 2 executions fixture bullets.
2. `tools/workflow/internal/store/analytics.go` — `execShapeSQL`, `ExecutionsPage`, `ExecCursor`.
3. `tools/workflow/internal/serve/analytics.go` — `cursor`, `canonFilter`, `analyticsExecutions`, `parseFilter`.
4. `tools/workflow/internal/store/analytics_test.go` — `TestAnalyticsExecutions`, `TestExecutionsPage`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

`GET /v1/analytics/executions` accepts repeatable `shape` filters and an optional time `bucket` that returns a three-key shape series, while window `counts` stay independent of `shape`.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Domain: Analytics reads, **`GET /v1/analytics/executions`**. Settled:

- Repeatable `shape`: `complete`, `unreported`, `started`; unknown → 400 `{"error":"unknown shape <s>"}`. Repeatable values OR'd. No `shape` means all rows.
- `shape` filters `rows` and the cursor only. `counts` stays the three window totals with `shape` ignored.
- Other filters apply to both `rows` and `counts`.
- Optional `bucket` `day`, `week`, or `month` adds `series`: exactly three objects, keys `complete`, `unreported`, `started`, in that order, each sparse `points` of `{"t","n"}`. `shape` does not change `series`.
- `t` bucket start matches score-series (RFC3339 in `tz`; week Monday, month first).
- Cursor binds `shape` and `bucket` like other filters (extend `canonFilter` query keys and cursor `Filter` string accordingly).

## Changes

- `ExecutionsPage`: optional shape filter on the brief CTE result; counts query unchanged (all shapes in window).
- New store method for shape series over buckets (reuse bucket boundary logic consistent with 2-02).
- Handler: parse `shape` repeatables, validate, pass to store; when `bucket` set, attach `series`; include `shape`/`bucket` in encoded cursor filter.
- Tests: `shape=complete` narrows rows but leaves `counts` as full window; with `bucket=day`, `series` has three keys in order `complete`, `unreported`, `started`. Paging cursor with shape still works.
- Bench: add cases with `shape=complete` and `bucket=day` per preset (or at least 24h) alongside existing executions cases.

### Keep untouched

Distribution and score-series routes. Conversations handlers and store aggregates. `execShapeSQL` semantics (only extend filtering/series).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `go test ./internal/store/ -run 'TestAnalyticsExecutions|TestExecutionsPage|TestExecutions.*Series' -count=1` from `tools/workflow` → passes with shape filter and series assertions.
- `go test ./internal/serve/ -run 'TestExecutions|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow` → passes; executions bench cases include shape and bucket at 200.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output before and after, deviations, contradictions. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
