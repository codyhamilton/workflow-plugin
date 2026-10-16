Status: done

## What changed

- **Store** (`analytics.go`): `ExecutionsPage` takes optional `shapes []string` and applies them to the rows query only; window `counts` unchanged. Added `ExecutionsShapeSeries` with three fixed keys (`complete`, `unreported`, `started`), sparse `{t,n}` points via `scoreSeriesBucketStart`.
- **Serve** (`analytics.go`): `parseExecShapes`, repeatable `shape` validation (400 `unknown shape <s>`), optional `bucket` (`day|week|month`) attaching `series`, `bucketSpan` cap, week-aware `parseFilter` when `bucket=week`. `canonFilter` includes `shape` and `bucket` for cursor binding.
- **Tests**: store `TestExecutionsPageShapeFilter`, `TestExecutionsShapeSeries`; serve `TestExecutionsShapeAndSeries`; bench cases `executions/shape/*` and `executions/shape-bucket/*`.

## Done evidence

**Before** (no shape/series tests; implementation absent): new tests would fail — e.g. `ExecutionsPage` arity mismatch and HTTP responses without `series`.

```
go test ./internal/store/ -run 'TestAnalyticsExecutions|TestExecutionsPage|TestExecutions.*Series' -count=1
# (TestExecutionsPageShapeFilter / TestExecutionsShapeSeries did not exist yet)

go test ./internal/serve/ -run 'TestExecutions|TestAnalyticsBenchSmoke' -count=1
# TestExecutionsShapeAndSeries did not exist; bench had no shape/bucket executions URLs
```

**After**:

```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store	1.343s
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	2.297s
```

## Deviations

None.

## Contradictions

None.
