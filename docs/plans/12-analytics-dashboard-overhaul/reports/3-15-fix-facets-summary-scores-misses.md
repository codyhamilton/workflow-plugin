# Report: 3-15 — Fix the facets, summary and scores misses

Status: **done with concerns**

## What changed

Two store changes on `/v1/analytics/{facets,summary,scores}`; no facts indexes (Deviation 1).

- **facets** — new hourly rollup `facets_hourly(dim,hour,value,n)` (migration 8, `store.go:97-106`), filled at Open by `backfillFacetRollup` (`rollup.go:186`) and kept current in `Append` (8 dims; `store.go:455-493`). `Facets` (`analytics.go:180`) now reads whole interior hours from the rollup and the two partial edge hours from base (the same shape as `query.go`'s `measureDef.source`); `facetsBase` (`analytics.go:249`) is the previous query, used when `rollupEligible()` (`analytics.go:170`) is false. The rollup is 9,660 rows on the copy.
- **summary** — `Summary` (`analytics.go:299`) counts `conversations` and `hook_events` from the existing `conversations_hourly`/`hook_events_hourly` rollups (interior + base edge hours) on time-only windows, and the artifact/commit/content counts from base; it falls back to the previous single query otherwise. No new table.
- **scores** — unchanged; already passing (Contradiction 1).
- Tests (`rollup_test.go`): `TestFacetRollupEqualsBaseRows`, `TestFacetRollupDuplicateAppend` (mid-hour windows + duplicate `Append`), `TestSummaryRollupEqualsBase`, `TestFacetsFilteredFallback`.

## Done evidence — before / after p95 ms (`WORKFLOW_BENCH_RUNS=3`, `/var/tmp/workflow-compact-copy/data/local`)

Before = this branch pre-change; after = now:

```
facets/7d   1881.6 -> 2.9     summary/7d   587.1 -> 219.8     scores/7d   30.9 -> 36.1
facets/30d  2102.1 -> 3.9     summary/30d  703.8 -> 370.1     scores/30d  33.3 -> 35.1
facets/90d  2004.5 -> 4.2     summary/90d  736.9 -> 378.8     scores/90d  33.3 -> 33.3
```

Every `facets/`, `summary/` and `scores/` case PASS (<500 ms). 3-11's recorded before: facets 1552.1/1775.7/1822.6; summary 532.9/753.5/782.6; scores 4939.0/6574.1/6452.6.

`go test ./internal/store ./internal/serve ./internal/compact` ok; `go vet` clean; `gofmt -l internal/store` empty.

## Deviations

1. **No covering index was added (brief Step 1).** On the copy, covering indexes on the facet dimensions moved facets only 10-20% (measured ~1.8-2.0 s -> ~1.5-1.7 s), so an index cannot meet the bound; the `facets_hourly` rollup does (~180x on the same queries). For summary the only helping index is `(type,norm_event,...)`, and any index on an extracted column breaks `internal/serve/reads_test.go` and `compaction_state_test.go` (hard-coded index/column teardown), which are outside the owned paths; reusing the 3-12/3-14 rollups gets summary to 219-379 ms with no schema/index change. So: a rollup for facets, rollup reuse for summary.
2. `rollup.go` and `rollup_test.go` already existed (the brief calls them "new"); appended to them.

## Contradictions (named, not resolved silently)

1. **scores.** The brief and 3-11 put scores at the worst miss (4.9-6.6 s). On the current copy it is ~33 ms and passes untouched. Root cause: `ANALYZE facts`, added by 3-14 in `ensureConversationRollupIndex` (`rollup.go`), runs on the benchmark's migrated copy and flips the `WindowScores` plan from a per-row co-routine rescan of `scores` to an automatic partial covering index; the `scores` table (9,592 rows) and `WindowScores` are unchanged since 3-11. No 3-15 change was needed for scores.
2. **Index instruction.** Brief Step 1 says "add the narrowest covering index as a new migration"; for summary that index type is blocked by the out-of-scope tests (Deviation 1).

## Concerns / unfinished

- Compaction rebuilds only `hook_events_hourly` (`compact/compact.go:91`), so `facets_hourly` — and `conversations_hourly`, which `Summary` now reads — drift after a compaction run. This is scheduled as brief 3-17 ("compact rebuilds all rollups"), which depends on 3-15 and owns `rollup.go`; it must land before phase proof 3-13.
- `Append` now issues 8 extra upserts per inserted fact (write amplification; no ingest benchmark was in scope).
- Inherited, not new: an open that commits `user_version=8` but crashes before `backfillFacetRollup` leaves an empty rollup that `Facets` treats as authoritative; migrations 6/7 share that window.

## Bug outside this brief's evidence

None found beyond the pre-existing compact-vs-`conversations_hourly` drift noted above.
