Status: done

## What changed

- Added `store/percentile.go` with `/scores`-compatible interpolation and measure rounding (6 dp cost, 1 dp tokens).
- Implemented `Tenant.Distribution` in `store/distribution.go`: call and conversation grain, optional `model` dim, usage filters with ignored dimensions, fixed bin edges, top-N truncation without `__other__`.
- Added `GET /v1/analytics/distribution` handler in `serve/analytics_distribution.go` and registered it in `serve.go`.
- Store tests (`TestDistribution*`) cover cost unpriced exclusion, token `unpriced=0`, shared cost bins, and truncation.
- Serve tests cover 400 validation, range cap, and 200 shape; `analytics_bench_test.go` adds `distribution/cost` and `distribution/tokens` cases per servable preset and smoke coverage for `distribution/`.

## Done evidence

Before (no implementation):

```
go test ./internal/store/ -run TestDistribution -count=1
ok ... [no tests to run]

go test ./internal/serve/ -run 'TestDistribution|TestAnalyticsBenchSmoke' -count=1
(build would fail: no handler)
```

After:

```
go test ./internal/store/ -run TestDistribution -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store	0.047s

go test ./internal/serve/ -run 'TestDistribution|TestAnalyticsBenchSmoke' -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	2.346s
```

## Departures

- **Serve shape test with empty `rows`:** `queryFixture` has no usage facts, so a 200 response has `rows: []` rather than a single `"all"` row. The handler matches store output when there are no kept calls; store tests assert the populated cases from the brief.

## Contradictions

None found between the brief and `DESIGN.md` for this route.

## Problems outside scope

None observed.
