# Report: fix-02 — `workflow ledger purge-deltas` removes every `message.part.delta`

Status: **done**

## What changed

Against each part of the brief:

- `internal/archive/archive.go`: added exported, documented `Filter(tenantDir string, keep func(Line) bool) (FilterStats, error)` and `FilterStats{Dropped, Rewritten, Deleted}`. Per `archive/*/*.jsonl.zst`, it decodes, and if any line is dropped rewrites the file as one fresh frame with survivors in order and duplicates kept (reusing `rewriteFile`: temp file in the same dir, fsync, rename); if no line survives it deletes the file and removes its month dir when empty; an untouched file keeps its bytes and mtime. It repairs nothing (the caller runs `Repair` first), holds the package mutex as `Repair` does, and bounds memory to one file's lines. Added `removeIfEmpty`.
- `internal/compact/purge.go` (new): `PurgeDeltas(ctx, t *store.Tenant, o Options) (PurgeStats, error)` with `PurgeStats{FactsDeleted, ArchiveDropped, FilesRewritten, FilesDeleted}`. Order: `archive.Repair`, facts delete of `harness='opencode' AND event='message.part.delta'` in `o.Batch` (default 5000) rowid ranges, one transaction per batch; `archive.Filter` with the delta predicate; `t.RebuildRollups(ctx)` last. The predicate `isDeltaLine` lives here, decoding only the envelope's `event` and never requiring the payload to parse. `ctx` is checked between batches and before the filter. A comment states why a rerun converges.
- `cmd/workflow/ledger.go`: `runLedger` now dispatches `compact` or `purge-deltas` with the same flag shape; new `purgeDeltasTenant` stats `ledger.db` first (a missing db exits 1 and never lets `OpenExclusive` create the dir), opens exclusive, prints `before:`, requires free space ≥ the current `ledger.db` size, runs `PurgeDeltas` under the SIGINT/SIGTERM session, prints the `purge:` counts line, reuses `vacuum` (VACUUM + `wal_checkpoint(TRUNCATE)`), and prints `after:`. Exit codes: 1 missing db/locked/short of space/interrupted, 2 usage.
- `cmd/workflow/main.go`: `usage` lists `ledger purge-deltas --tenant-dir <dir>`.
- Tests: `internal/archive/archive_test.go` (`TestFilterDropsDeltas`, `TestFilterAfterRepairHandlesTornTail`), `internal/compact/purge_test.go` (`TestPurgeDeltasRemovesAllDeltas`, `TestPurgeDeltasResumesAndConverges`), `cmd/workflow/ledger_test.go` (`TestLedgerPurgeDeltasSuccess`, `TestLedgerPurgeDeltasMissingTenantDir`, `TestLedgerPurgeDeltasLocked`).

`compact.Run` and the `compaction` meta key are untouched.

## Check output

```
go build ./... && go vet ./...           clean
gofmt -l .                                (nothing)
go test -race ./internal/archive ./internal/compact
  ok  .../internal/archive   1.670s
  ok  .../internal/compact   4.163s
go test ./...                             every package ok (cmd/workflow 53.3s)
```

Targeted verbose: archive Filter 2/2 PASS; compact Purge 2/2 PASS; cmd/workflow Purge 3/3 PASS.

Done-evidence mapping: archive — three conversation-months (delta-only deleted + month dir gone, mixed rewritten with survivors in order and a duplicate kept, untouched bytes+mtime), second `Filter` a no-op, torn tail handled after `Repair`. compact — zero delta rows, non-delta rows byte-identical, every rollup exact both EXCEPT directions (`assertAllRollupsExact`), non-delta archive lines present by `row_hash` and delta lines gone, resume after `errStop` on batch 1 equals an uninterrupted run, third run reports `PurgeStats{}`, and `cdelta` (delta-only) leaves `conversations_hourly`. CLI — success prints before/after; missing dir exits 1 and creates nothing; a held lock exits 1.

## Deviations

1. **Line budget exceeded.** The brief estimated ~350 changed lines; the change is ~750 (≈360 edited + 387 in the two new `purge*.go` files). The two test files account for most of it; the contract's done evidence (three archive cases, four rollup tables, resume, a non-hook row, a delta-only conversation, three CLI cases) needs it. All checks pass and no work was dropped.
2. **`ctx` between files is checked before `archive.Filter`, not inside it.** The brief says "respect ctx between batches and files"; `Filter` has no `ctx` parameter and is the files step, so it runs whole. Cancellation between batches is honoured.
3. Ledger delete uses `event='message.part.delta' AND harness='opencode'`; the archive predicate uses `event` only, exactly as the brief words them. See the asymmetry note below.

## Contradictions / observations

- **Predicate asymmetry (named, not resolved).** The brief's ledger step filters on `harness='opencode'` as well as the event, while its archive predicate is the fact's `"event":"message.part.delta"` alone. A non-`opencode` `message.part.delta` fact would therefore survive in `facts` but lose its archive line. The brief states both literally, so I implemented both literally; in the real ledger every delta is opencode, so the two predicates agree. Flagging so the consumer can decide whether the archive predicate should also require `harness='opencode'`.
- The brief's CLI line names `vacuum` and a separate `wal_checkpoint(TRUNCATE)`; `vacuum` already runs both, so the command calls `vacuum` once.

## Unfinished

None. `compact.Run` and the `compaction` key stay as they were, as required.
