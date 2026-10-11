# 3-12 — Fix the hook_events misses (indexes, then the hourly rollup)

Status: **done with concerns**

## What changed

- New migration 6 (`internal/store/store.go`): creates `hook_events_hourly`, an hourly rollup of
  hook_events keyed `(hour, harness, repo_id, norm_event, event, tool, conversation_id)` with a
  count `n` (WITHOUT ROWID, that tuple as the primary key).
- New `internal/store/rollup.go`: `hookRollupUpsert` (the Append upsert), `backfillHookRollup`
  (fills the table from base rows when a tenant first gains it), `columns`.
- `Append` (`store.go`) increments the rollup in the same transaction as the fact insert, and only
  when the fact row was actually inserted, so a collapsed duplicate adds nothing.
- `query.go`: `measureDef.rollup` selects the rollup read path for `hook_events`; `measureDef.source`
  builds the FROM source as `(first partial hour from facts) UNION ALL (last partial hour from facts)
  UNION ALL (interior whole hours from the rollup)`; `aggSQL` is `coalesce(sum(w),0)` over that source.
  `rankSQL`, `rankLocalTimeDim`, `finalUTC`, `finalLocal` thread the source through.
- New `internal/store/rollup_test.go`: rollup == base-row aggregates over windows starting and
  ending mid-hour (7 windows × 7 dims), an EXCEPT-equal check both directions, a duplicate-append
  invariant, and a rewind-to-5 reopen proving the backfill refills from base rows.

## Benchmark (compacted copy `/var/tmp/workflow-compact-copy/data/local`, filter `query/hook_events/`, RUNS=3)

`before` (3-11 report) — 152 of 213 hook_events cases over 500 ms; key lines:

| case | before p95 |
|---|---|
| dims=event+conversation_id/bucket=none/all | 1460.8 |
| dims=harness+tool/bucket=none/all | 1383.4 |
| dims=norm_event+hour_of_day/bucket=none/7d | 1169.9 |
| dims=harness/bucket=day/7d | 878.9 |
| dims=tool/bucket=none/7d | 627.9 |

`after` — **213/213 under 500 ms; 0 non-200; 62 s elapsed** (`/tmp/opencode/bench-after-rollup2.txt`):

| case | after p95 |
|---|---|
| dims=conversation_id+hour_of_day/bucket=none/all | 146.5 (max case) |
| dims=event+conversation_id/bucket=none/all | 129.7 |
| dims=harness+tool/bucket=none/all | 110.9 |
| dims=norm_event+hour_of_day/bucket=none/7d | 95.0 |
| dims=harness/bucket=day/7d | 73.6 |
| dims=tool/bucket=none/7d | 44.6 |

## Departures from the brief, with reasons

1. **The covering index (Step 1) was added and then removed.** As suggested, migration 6 first was
   `CREATE INDEX facts_type_ts_dims ON facts(type, ts, harness, ...)`. It left 139/213 cases over
   500 ms (e.g. `harness+tool/all` 998.4), and it broke two existing tests: `TestCompactionStateHealth`
   (migration references `ts`, absent from the pre-migration-4 layout `legacyLedger` builds) and
   `TestAdvisoryReads/backfill` (`ALTER TABLE facts DROP COLUMN norm_event` failing because the index
   referenced it). Removed; the rollup alone gets every case under the bound.
2. **The rollup is created by migration 6 but filled by a Go backfill in `open()`**, not by the
   migration SQL. The fill selects facts columns that the `legacyLedger` stub lacks, so plain SQL in
   the migration fails that test; the backfill no-ops when those columns are absent. This is the
   brief's "filled by the same new migration from base rows", moved one step into `open`.
3. **`rollup.go` holds the rollup's write side; the read source is in `query.go`** (the brief owns
   both). No rollup read helper was needed beyond `measureDef.source`.

## Perf finding fixed during Step 2

The first rollup source took edge hours as
`ts>=from AND ts<=to AND (ts < hFrom+3600 OR ts >= hTo)`. SQLite used the ts range of the whole
window and applied the OR as a residual, so the base arm scanned the full `facts_type_ts` range
(~448k entries); that alone was 112 ms per scan and left the "all"-pair cases at ~450–500 ms
(`event+conversation_id/all` 501.2 on one 3-run sample). Splitting the base arm into two bounded
one-hour ranges (`[from, hFrom+3600)` and `[hTo, to]`) dropped a scan to ~5 ms and the whole class
to ~130 ms. In-memory timing of `Tenant.Query` on the copy: `event+conversation_id/all` 373→131 ms,
`conversation_id+hour_of_day/all` 390→146 ms, `dims=none` 94→14 ms.

## Contradictions between the brief and cited contracts

None found. The design's "rollups are conditional" is satisfied: the index alone did not meet the
bound, so the rollup was added, and it is exact (partial-edge hours read from base rows).

## Done evidence

- Filtered rerun: 213/213 `query/hook_events/` cases under 500 ms p95 (paste above).
- `go test ./internal/store ./internal/serve ./internal/compact` → all `ok`.
- `go vet ./internal/store ./internal/serve ./internal/compact` → clean.
- `gofmt -l` on `store.go`, `query.go`, `rollup.go`, `rollup_test.go` → empty.

## Known problems

- Full unfiltered benchmark not run here (3-13 runs it). The other measures' misses (conversations,
  facets, summary, scores) are unchanged and remain for 3-14/3-15.
- Latent blocker introduced by this unit's rollup: compaction drift (see below).

## Non-trivial bug outside this unit's evidence (introduced by this unit's rollup)

Symptom: after compaction touches `facts`, the `hook_events` measure no longer equals its base-row
aggregate. Compaction mutates/deletes hook_event rows but never updates `hook_events_hourly`, and the
rollup is rebuilt only when `from < 6`, so the drift is permanent (later appends only increment).

Location: `internal/compact/compact.go:276` (`DELETE FROM facts WHERE rowid=?`, ops Remove/Collapse)
and `:280-285` (`UPDATE facts SET norm_event=?, tool=?`), both touching rollup key columns; missing
rebuild in `applyOps` (`compact.go:271-295`) / after `Run`. The only rollup writers are `Append`
(`store.go:435-439`, `rollup.go:11`) and `backfillHookRollup` (`rollup.go:29-33`), the latter gated
on `from < 6` (`store.go:172`) and skipped once `user_version == 6`.

Root cause: this brief scoped rollup maintenance to `Append` only; compaction is an out-of-owned-path
writer, so the rollup drifts. Reproduced on a temp store: Append one Remove/Collapse-policy hook,
run `compact.Run` -> `facts count 2 -> 1`, `rollup sum(n) 2 -> 2`, one base tuple absent from the
rollup afterwards.

Not fixed here: compaction is not an owned path and the brief says report, do not fix. Follow-up
needed to maintain/rebuild the rollup in `applyOps`/after `Run` (or gate the rebuild on a state flag
rather than `user_version`). Related minor: the backfill's `from < 6` gate commits separately from
`migrate()`'s `user_version = 6`, so a crash between them leaves an unrepaired v6.
