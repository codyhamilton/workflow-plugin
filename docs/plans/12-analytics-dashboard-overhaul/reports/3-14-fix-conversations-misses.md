# 3-14 — Fix the conversations misses

Raw artifacts: `/var/tmp/workflow-compact-copy/bench-3-14-before.txt`, `/var/tmp/workflow-compact-copy/bench-3-14-after.txt`. Run on the compacted copy `/var/tmp/workflow-compact-copy/data/local` exactly as 3-11 (the benchmark copies `ledger.db` and opens the copy, so migrations run on the copy; `df /var/tmp` = 29G free).

Status: **done with concerns**.

## What changed

`conversations` is a DISTINCT count (`count(DISTINCT conversation_id)` over all fact types). A covering index alone leaves the grouped cases at 1.4–1.9 s p95, so per the design's "rollup only for measures that miss the bound" a rollup was added, plus an index for the bare page route.

- `store/store.go` — appended **migration 7**: `conversations_hourly(hour,harness,repo_id,model,conversation_id,n)` `WITHOUT ROWID`. `Append` now upserts it for every **inserted** fact in the fact insert's transaction (duplicate row hash inserts neither), so the rollup stays current. `open()` runs `backfillConversationRollup` when `from < 7`, and ensures the conversations page index (`ensureConversationRollupIndex`) on **every** open — the index is ensured each start, and `ANALYZE facts` runs only when the index is newly created, so a normal open does not re-ANALYZE.
- `store/rollup.go` — `convRollupUpsert`, `convRollupFill`, `convRollupColumns`, `convRollupFillApplies`, `backfillConversationRollup` (column-guarded, mirrors the hook rollup), `ensureConversationRollupIndex`.
- `store/query.go` — `measureDef` gained `rollupCols`/`rollupType`; `source()` generalized to project any rollup's columns for the two partial edge hours (base rows) plus whole interior hours (rollup), keeping `pred` inside the base branch; `aggSQL()` sums the weight only for a counting rollup and returns `count(DISTINCT …)` for the distinct rollup (summing would overcount). `conversations` and `hook_events` both wired through it.
- `store/rollup_test.go` — `TestConversationRollupEqualsBaseRows` (windows starting and ending mid-hour, dims none/harness/repo_id/model/hour_of_day/weekday vs a base-row oracle), `TestConversationRollupEqualsBaseSQL` (EXCEPT both directions), `TestConversationRollupDuplicateAppend` (duplicate leaves rollup == base).
- `serve/analytics.go` and `usage.go` were **not changed** — no read path there needed editing.

## Before / after (p95 ms, runs=3)

| case | before | after |
|---|---|---|
| conversations/7d | 490.0 | 353.4 |
| conversations/30d | 563.0 | 379.8 |
| conversations/90d | 562.6 | 385.9 |
| query/conversations/dims=harness+hour_of_day/bucket=none/all | 1855.3 | 32.7 |
| query/conversations/dims=hour_of_day+weekday/bucket=none/all | 1855.3 | 33.3 |
| query/conversations/dims=model+weekday/bucket=none/90d | worst measure after | 37.0 |

- Before: **82/112** cases over 500 ms, worst 1855 ms, elapsed 6m54s.
- After: **0/112** cases over 500 ms, worst 37.0 ms, elapsed 11 s.

## Verification

- `go test ./internal/store ./internal/serve ./internal/compact` → all `ok`.
- `go vet ./...` → clean; `gofmt -l .` → clean.

## Departures from the brief (with reasons)

- **Index is created in Go at open, not as migration 8 SQL.** A plain `CREATE INDEX … facts(conversation_id, ts, type, kind, repo_id)` in the migrations slice fails two existing tests: `legacyLedger` builds `facts(row_hash,type)` at user_version 4 (the migration errors "no such column: conversation_id"), and `reads_test` reconstructs a version-1 ledger by `ALTER TABLE facts DROP COLUMN kind` (fails: "error in index … after drop column"). The index is therefore created by `ensureConversationRollupIndex`, column-guarded and `IF NOT EXISTS`, and it **omits `kind`** (a dropped column) — the page reads `kind` from the base table. The brief allowed migrations 7 "and 8 only if needed"; no migration 8 was needed.
- **`ANALYZE facts` is run once when the index is created.** Without stats the planner keeps `facts_ts` and the bare pages miss the bound; with stats it picks the covering index (0.13 s vs 0.32 s at the CLI).
- **Rollup key is `(hour,harness,repo_id,model,conversation_id)`**, the minimal set for the conversations measure's dims plus its distinct column, not the longer illustrative key in the brief. This matches the same bullet's "limited to the dimensions the missed measures need".
- The distinct rollup is read with `count(DISTINCT conversation_id)` over the union, not `sum(w)`; `source()`/`aggSQL()` were generalized for this, as the brief anticipated.

No contradiction with the design contract: the rollup was added only after indexes failed to reach the bound, edge hours are read from base rows, and a store test asserts rollup == base rows including mid-hour windows.

## Problems / unfinished

- **C1 — `conversations_hourly` is NOT rebuilt after compaction (out of scope; reported, not fixed).** `tools/workflow/internal/compact/compact.go` reconstructs only the hook rollup: its deferred rebuild calls `t.RebuildHookRollup(ctx)` and nothing for conversations. Compaction deletes `remove` events, collapses deltas and fills `model` on the base rows, so the base-row conversations aggregate changes while `conversations_hourly` keeps the pre-compaction presence rows; the rollup drifts from base rows and violates the design's "rollup aggregates equal base-row aggregates". `docs/plans/12-analytics-dashboard-overhaul/briefs/3-16-compact-keeps-rollup-exact.md` currently names only `hook_events_hourly`, so the conversations rebuild is an uncovered gap: 3-16 needs extending to cover it, or a new brief is needed. Fix direction (not implemented here): export `RebuildConversationRollup` mirroring `RebuildHookRollup`, call it from compact's deferred rebuild beside `RebuildHookRollup`, and add a compact test asserting both rollups equal base rows after a run.
- **M3 (unfinished).** The first upgraded start pays a one-time `ANALYZE facts` plus a covering-index build over the large uncompacted ledger. Accepted for this fix; a future open could bound or defer it.
- **M4 (unfinished).** The rollup test has no bucket/tz/2-dim case: `TestConversationRollupEqualsBaseRows` covers `bucket=none` with one dim at a time, so bucketed, two-dimensional and non-UTC paths are unexercised.
- **M1/M2 (now fixed).** `ensureConversationRollupIndex` is ensured on every open (`ANALYZE facts` only when the index is newly created), so a failed first build cannot leave the page unindexed; and `backfillConversationRollup` now runs its DELETE + fill in one transaction, so a crash between them cannot leave the table empty.
- The bare pages pass with a smaller margin (354–386 ms) than the measure cases; that margin is the cost of omitting `kind` from the index to keep the legacy-reconstruction test working. A future index that includes `kind` would require updating that test.
