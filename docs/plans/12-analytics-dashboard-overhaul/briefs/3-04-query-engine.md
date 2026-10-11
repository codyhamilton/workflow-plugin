# Brief: 3-04 — The measure matrix and the query engine for non-usage measures

Consumer: a Go worker (flash-tier); 3-05 registers usage measures into it, 3-06 serves it.
Owned paths: `tools/workflow/internal/store/query.go` (new) and `query_test.go` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-04-query-engine.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-02.
Runs alongside: 3-01, 3-03.
Budget: 5 files to read, about 400 lines to write, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads: **Shared filter**, **`GET /v1/analytics/query`**, **The measure × dimension matrix** (binding, quote the table into your code and tests).
2. `tools/workflow/internal/store/analytics.go` — `AnalyticsFilter` (with 3-02's new fields), `factWhere`, `rejWhere`, `inList`, `Series` (the model for grouping and bucketing).
3. `tools/workflow/internal/store/store.go` lines 28-70 — columns and indexes.
4. `tools/workflow/internal/store/analytics_test.go` — fixture style.
5. `docs/plans/12-analytics-dashboard-overhaul/briefs/3-02-filter-columns.md` — Contract (what the filter now carries).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

One method answers `measure × 0..2 dims × bucket × top-N` for the six non-usage measures, with the design's matrix as the single source of truth for what is allowed.

## Contract

Design, cited: "`measure`, required; `dim`, 0–2 times; `bucket`: `none` (default), `hour`, `day`, `week` (ISO Monday) or `month`; `top`: default 20, max 100. It ranks each dimension's keys independently by the measure's total over the window. Keys outside the top N fold to `"__other__"`, which is not a valid filter value. Responses are capped at 20,000 rows, with `truncated`. ... Rows are sparse, and `t` is RFC3339 in `tz`. An unsupported measure × dimension pairing is 400 `{"error":"unsupported dimension <d> for <measure>"}`." And: "A filter on a dimension the requested measure does not carry is ignored, and that key is listed in `ignored_filters`".

Settled by this brief:
- API (exact):
  ```go
  type MeasureSpec struct{ Name, Unit string; Dims []string }
  func Measures() []MeasureSpec           // the whole matrix in the design's order, usage measures included; every measure's Dims also ends with "hour_of_day","weekday"
  var Buckets = []string{"none","hour","day","week","month"}
  type QueryParams struct{ Measure string; Dims []string; Bucket string; Top int }   // Top 0 means 20; over 100 is clamped to 100
  type QueryRow struct{ T string; K []string; V float64 }                         // T empty when Bucket is none
  type QueryResult struct{ Measure, Bucket string; Dims []string; Rows []QueryRow; Ignored []string; Truncated bool }
  var ErrUnsupported = errors.New("unsupported")  // wrapped as fmt.Errorf("unsupported dimension %s for %s: %w", d, m, ErrUnsupported)
  func (t *Tenant) Query(ctx context.Context, f AnalyticsFilter, p QueryParams) (QueryResult, error)
  var usageExec func(...) ...   // see below
  ```
- Executors: `hook_events` (count of `type='hook_event'`), `conversations` (distinct `conversation_id`; dims `harness`, `repo_id`, `model`), `artifact_versions`, `distinct_content` (distinct `content_hash` of artifact versions), `commits`, `rejections` (from `rejections`, dim `stage`). Dims map to columns (`kind`, `plan`, `source`, `tool`, `norm_event`, `event`, `model`, `harness`, `repo_id`, `conversation_id`); `hour_of_day`, `weekday` and every `bucket` depend on `TZ`. For UTC, group in SQL with `strftime` on `ts`. For another zone SQLite cannot apply a zone with daylight saving, so group in SQL at UTC hour granularity (hour, plus the other dims), then convert each hour to the zone in Go and re-aggregate into the requested bucket, `hour_of_day` or `weekday`. Distinct measures (`conversations`, `distinct_content`) cannot be re-aggregated from hour counts: for a non-UTC zone fetch `(hour, dims…, conversation_id or content_hash)` distinct tuples and count distinct in Go, and note in the report that this path is slower (3-11 measures it).
- Usage measures (`model_calls`, `tokens_*`, `cost_usd`, `unpriced_calls`) are in the matrix but their executor is a package variable `usageQuery func(ctx context.Context, t *Tenant, f AnalyticsFilter, p QueryParams) (QueryResult, error)` that is nil here; `Query` returns `errors.New("measure not available")` while it is nil. 3-05 sets it in its own file.
- Ignored filters: each filter key (`Repos`->`repo_id`, `Harnesses`->`harness`, `Kinds`->`kind`, `Plans`->`plan`, `NormEvents`->`norm_event`, `Events`->`event`, `Tools`->`tool`, `Models`->`model`, `Sources`->`source`, `ConversationIDs`->`conversation_id`) that is non-empty and whose dimension the measure's Dims does not list is not applied and its name is appended to `Ignored` (sorted). For `rejections` all filters except `kind`/`plan` (path-derived) are ignored as before the design.
- Top-N: compute each dimension's ranking from the measure total over the window (one grouped query per dimension), keep the top N keys, fold the rest to `"__other__"` and re-aggregate. Ties break by key ascending. Sum measures re-add; distinct measures (`conversations`, `distinct_content`) must be recomputed distinct after folding (run the final grouped query with a CASE mapping outside-top keys to `__other__`).
- 400 bucket cap: not here (serve's job).

## Done evidence

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store -run Query -v` passes with tests for: the matrix matches the design table row for row (literal in the test); an unsupported pairing returns an error satisfying `errors.Is(err, ErrUnsupported)`; 0, 1 and 2 dimensions on `hook_events` against hand-counted rows; each non-usage measure answers at least one query; bucket `day` and `week` (Monday) on a fixture; `TZ=Australia/Sydney` moves a row at 23:30 UTC into the next local day and `hour_of_day` is local; top-N folding (`Top:2` over 4 keys gives 2 keys plus `__other__`, totals unchanged, and a distinct measure's `__other__` is a true distinct count); a `kind` filter on `hook_events` yields `Ignored == ["kind"]` and the same rows as without it; truncation at 20,000 rows is reached with a lowered package-level cap variable the test sets.
- `go vet ./internal/store` and `gofmt -l internal/store` print nothing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
