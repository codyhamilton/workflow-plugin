# Report: 2-03 — Compaction engine

Status: done

## What changed
- New package `tools/workflow/internal/compact`: `compact.go` holds `Run(ctx, *store.Tenant, Options) (Stats, error)` and its helpers. `Run` requires `OpenExclusive` (`Raw()!=nil`), calls `archive.Repair` first, reads meta `compaction`/`compact_cursor`, then walks `facts` by `rowid` in batches inside one transaction each: it archives every non-removed hook body verbatim (`archive.Append` once per batch, from the in-memory original raw), calls `AfterArchive`, applies the batch's SQL, advances `compact_cursor`, commits, and calls `AfterCommit`. When the scan passes the last rowid it sets meta `compaction='complete'`. Every 20 batches it checkpoints the WAL; every 50 it writes a counts-only progress line. Policy: `Remove` deletes with no archive line; `Collapse` folds each part to one row via the collapse hash with the survivor's `ts` the minimum over the part (in-batch survivors tracked in memory, earlier-batch survivors found by a read); survivors and `Keep` rows get `ingest.Envelope` and the `Derive` columns. Non-hook rows get `kind`/`plan`/`source`/`sha` filled.
- New `tools/workflow/internal/store/plan.go`: exported `PlanOf(p) = planOf(p)`.
- `tools/workflow/internal/ingest/ingest.go`: added only `func Envelope(obj map[string]any) ([]byte, error) { return envelope(obj) }`; nothing else changed.
- New `tools/workflow/internal/compact/compact_test.go`: `TestRequiresExclusive`, `TestEquivalence`, `TestOutcome`, `TestResume` (AfterArchive and AfterCommit, `Batch=3`), `TestRepair`, `TestPreexistingSurvivor`, and `TestThroughput` (env-gated).

## Check output
Before (new test file against unchanged code):
```
# github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact [github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact.test]
internal/compact/compact_test.go:207:15: undefined: Run
internal/compact/compact_test.go:207:45: undefined: Options
...
FAIL	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact [build failed]
FAIL
```
After (`go test -race -count=1 ./internal/compact/ ./internal/ingest/ ./internal/store/ && go vet ./... && go build ./...`, exit 0):
```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact	2.892s
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest	1.767s
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store	15.331s
```
Throughput (`COMPACT_THROUGHPUT=1 go test -run TestThroughput -v ./internal/compact/`, no `-race`):
```
compact_test.go:478: throughput: scanned=50000 archived=50000 in 1.660988128s = 30103 rows/sec
```

## Departures
- Planning issues a read-only `SELECT` for an earlier-batch collapse survivor before `archive.Append`; no write touches the ledger before the archive is appended, so the brief's archive-before-SQL ordering holds in effect. Named because the brief's "before touching SQL" is literal and a read does not meet it.
- `Stripped` counts hook rows whose raw is actually rewritten (Keep and survivors), excluding collapse duplicates that are deleted; `Archived` counts entries written and so can exceed the distinct count on a resumed batch. The brief leaves counter semantics free; tests assert behaviour, not counters.

## Contradictions
- The brief's collapse rule sets the survivor's `ts` to the **minimum** over the part, while the ingest it cites (`Ingest` + `INSERT OR IGNORE`) keeps the **first-arriving** part's `ts`. The two agree only when parts arrive in ascending `ts` order — which the fixture happens to do, so `TestEquivalence` passes. Ingested-out-of-order parts would leave ingest and compaction with different survivor `ts`. Not resolved here; named for 2-04/2-05.
- No other contradiction. The DESIGN Phase 2 "distinct archive row_hash == pre-compaction non-removed hook count" holds: legacy rows carry the full-envelope hash as their existing `row_hash`, so each archived line's hash is distinct per received body.

## Known limits and residual risk
- Throughput is measured on a synthetic 50k-row all-`Keep` ledger; a ledger dense in collapse deltas pays one extra `SELECT` per delta part, so the real rate can be lower.
- For a **post-Phase-1** survivor already in the table (row_hash = collapse hash, no payload), a re-compaction archives it under its collapse hash, not the full-envelope hash its original ingest line used. Correct for pure legacy ledgers (the only case where compaction has work); noted for mixed ledgers.
- `instr(raw,'"payload"')` treats a hook raw that literally contains the string `"payload"` elsewhere as carrying a payload; no such fixture value exists and the stored keys are the only realistic source.

## Unfinished
- None in this unit. 2-04 should parse flags/vacuum and call `compact.Run`; 2-05 should estimate the real run from the rows/sec above.
