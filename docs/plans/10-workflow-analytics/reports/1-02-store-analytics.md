# Report: 1-02 Store analytics queries

Status: done with concerns (one contradiction with a cited design point and one existing-test interaction, both below).

## Done

- `tools/workflow/internal/store/analytics.go`: the full API from the brief with the exact signatures (`Facets`, `Summary`, `Series`, `WindowScores`, `Executions`, `Conversations`, `Explore`, plus the types). No signature changed. SQLite scalar functions `wf_kind` (calls `keys.Kind`) and `wf_plan` registered once in `init()`.
- `store.go`: migration 3, `CREATE INDEX IF NOT EXISTS facts_ts ON facts(ts);`.
- `analytics_test.go`: one hand-counted fixture (19 facts, 6 rejections, screens, scores) and 7 tests (`TestAnalyticsSummary`, `Series`, `WindowScores`, `Executions`, `Conversations`, `Facets`, `Explore`) covering every edge the brief lists: window edges at exactly From/To and 1s (rejections 1ns) outside; `at` vs `ts`; OR within / AND across filters; kind filter dropping hook events and commits; Sunday vs Monday week buckets with `t` the Monday; `conversations` distinct count; `tool` group with the `""` key; latest score row and in-window hashes only; `complete`/`unreported`/`started` with out-of-window commit and report, a report in another conversation not counting, two briefs in one conversation with one report; harness tie-break; facets tool order and 100 cap; explore order and `truncated`.

## Check output

Before (tests first): `go test ./internal/store/ -run Analytics` failed to compile (`undefined: AnalyticsFilter`, `Summary`, `tn.Summary` ...).
After: `go test ./internal/store/ -run Analytics -v` passes all 7 tests. `go vet ./...` clean; `go test ./...` all packages ok, including `internal/serve`.

## Departures and decisions

- Migration 3 uses `IF NOT EXISTS`, not the bare `CREATE INDEX` the brief gave. The existing `TestAdvisoryReads/backfill` in `internal/serve` sets `PRAGMA user_version = 1` and drops `search` to force a re-migration; with a bare `CREATE INDEX facts_ts` migration 3 re-ran against a DB that already had the index and the tenant failed to open (503). `IF NOT EXISTS` fixes it without touching that test.
- Explore tie-break key (brief left it open): `ts` descending, then key ascending, where key is `row_hash` for facts and `rej-<20-digit id>` for rejections. At an identical instant facts therefore come before rejections.
- `Facets` applies the whole filter (window and dimension lists) as given. If 1-03 wants filter controls unaffected by the selected filters, it should pass a filter with only `From`/`To`.
- `Series` returns an error for an unknown metric, bucket or group, and for a rejections group other than `none`/`stage`; the caller still validates pairings per the contract.
- Plan derivation cleans the path as `keys.Kind` does and returns segment 2; empty when the path has no kind.

## Contradictions

None with DESIGN.md. The only conflict was the migration/existing-test one above.

## Unfinished / known problems

None. Large tenants: `Conversations` aggregates in Go over all filtered in-window facts and `Executions` uses correlated EXISTS per brief; both are fine at current sizes but not measured at scale.
