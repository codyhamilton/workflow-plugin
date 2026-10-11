# Report: 3-03 — One survivor-ts rule for ingest and compaction

Status: done

## What changed
- Rule: **first-arriving**. Ingest keeps the first-arriving part's `ts` and answers `duplicate`
  for later parts of an already-stored key. `ts` is parsed and assigned to the arriving row at
  `tools/workflow/internal/ingest/ingest.go:238-243`; the collapse row_hash is set at
  `:250-252`; the row is appended at `:273-284`, where a row that the store refuses becomes
  status Duplicate and changes nothing. The refusal is `INSERT OR IGNORE` at
  `internal/store/store.go:391`. No ingest test was added (not required).
- `tools/workflow/internal/compact/compact.go`: compaction no longer takes a minimum. The
  `minInto` closure is removed. In-batch later parts are deleted and the first-seen (lowest
  rowid) row stays the survivor carrying its own `ts`. The existing-DB branch now selects the
  lowest rowid with `ORDER BY rowid LIMIT 1` and leaves its `ts` alone. The `'t'` retime op is no
  longer emitted for collapse.
- Representation note: `survivors` changed from `map[string]*surv` to `map[string]struct{}`
  because no survivor attributes are needed once the minimum is gone; the `surv` struct was
  deleted.
- Tests: added `TestCollapseSurvivorFirstArrival` (three parts arrive 30, 10, 20; expects the
  survivor ts 30, unchanged on a second Run); updated `TestPreexistingSurvivor` to expect ts 70
  (the first-arriving row) instead of the old minimum 40.

## Evidence
BEFORE (branch `plan/12-analytics-dashboard-overhaul`):
```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact	0.177s
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest	(cached)
```
AFTER:
```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact	0.192s
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest	(cached)
```
`go vet ./internal/compact`: no output (exit 0). `gofmt -l internal/compact`: no output.

`TestResume` stays green: a resumed (interrupted then continued) run still yields identical
facts and archive to an uninterrupted run. Nothing else references `surv`, `sts` or `minInto`.

## Departures
- None.

## Known limits / unfinished
- `surv.ts` no longer exists; grep confirms no dead code remains (`surv`, `sts`, `minInto` all
  absent from `compact.go`).
- None.
