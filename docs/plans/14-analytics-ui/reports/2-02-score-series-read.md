Status: done

## What changed

- Added `store/score_series.go` with `Tenant.ScoreSeries`: bucket assignment on artifact_version `ts` in `tz`, latest score per hash per check, sparse percentile points (p25/median/p75, 3 dp).
- Added `GET /v1/analytics/score-series` in `serve/analytics_score_series.go`; registered in `serve.go`. Validates `kind`, `bucket`, shared filter, 400-day/week cap via `parseFilter`, and >400 buckets via `bucketSpan`.
- Store tests cover two versions of one hash in one bucket (latest score), omitted empty bucket, and brief week series on the main fixture.
- Serve tests cover validation, range cap, and 200 shape; bench adds `score-series/<preset>` with `kind=design&bucket=day`; smoke requires `score-series/` prefix.

## Done evidence

Before (no implementation):

```
go test ./internal/store/ -run TestScoreSeries -count=1
ok ... [no tests to run]

go test ./internal/serve/ -run 'TestScoreSeries|TestAnalyticsBenchSmoke' -count=1
ok ... (TestScoreSeries absent; smoke had no score-series cases)
```

After:

```
go test ./internal/store/ -run TestScoreSeries -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store	0.035s

go test ./internal/serve/ -run 'TestScoreSeries|TestAnalyticsBenchSmoke' -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	2.396s
```

## Departures

None.

## Contradictions

None found between the brief and `DESIGN.md` for this route.

## Problems outside scope

None observed.
