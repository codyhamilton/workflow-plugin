# Brief: 2-01 — Tenant-dir lock, meta table and compaction state in health

Consumer: a Go worker (flash-tier) adding the tenant lock and the compaction-state plumbing that units 2-03 and 2-04 build on.
Owned paths: `tools/workflow/internal/store/store.go`, `tools/workflow/internal/store/store_test.go`, `tools/workflow/internal/store/lock.go` (new), `tools/workflow/internal/store/lock_test.go` (new), `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/compaction_state_test.go` (new), `tools/workflow/cmd/workflow/main.go` (only `runServe`: the preflight call). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/2-01-lock-meta-health.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 2-02.
Budget: 6 files to read, about 300 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Ledger shape and compaction" (Compaction command, Uncompacted ledgers) and "Phase 2 — Historical compaction and reclaim" Outcome (binding).
2. `tools/workflow/internal/store/store.go` — lines 23-70 (`migrations`), 99-191 (`Open`, `migrate`, `Close`).
3. `tools/workflow/internal/serve/serve.go` — `tenant()` (about line 345) and `health()` (about line 521).
4. `tools/workflow/cmd/workflow/main.go` — `runServe` (from about line 74).
5. `tools/workflow/internal/store/store_test.go` — lines 280-295 and 405-420 (they depend on `len(migrations)`) and `TestMigrationFast100k` (about line 496).
6. `tools/workflow/internal/drain/drain.go` — lines 130-185, the existing `syscall.Flock` pattern (do not change it; it is a different lock).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A tenant directory has one lock: serve and every normal `store.Open` hold it shared, compaction holds it exclusive, and serve refuses to start while compaction holds it. The store has a `meta` table, and `/v1/health` reports whether the ledger still needs compaction.

## Contract

Cited from DESIGN.md "Compaction command": "It runs when it can take an exclusive lock on the tenant dir; serve takes the same lock shared and refuses to start while compaction holds it." And "Until compaction completes, `/v1/health` reports `"compaction":"required"`". Phase 2 Outcome: "`/v1/health` no longer reports `compaction: required`" after compaction, and "Starting serve while compaction holds the lock fails with a clear error. This guards against two writers on one SQLite file."

Settled by this brief:
- Lock file: `<tenant dir>/.lock`, created mode 0600, `syscall.Flock` non-blocking. `Open` takes `LOCK_SH` before it opens SQLite or migrates, and holds the file open until `Close`. A failed non-blocking lock returns `ErrLocked` (exported sentinel; the error text names the directory and says "locked by compaction or another exclusive holder; wait for `workflow ledger compact` to finish").
- New `OpenExclusive(dir string, opts Options) (*Tenant, error)`: same as `Open` but takes `LOCK_EX`. It fails with `ErrLocked` while any other holder (shared or exclusive, in this process or another) has the lock. Flock locks belong to the open file description, so two `Open` calls in one process on one directory both succeed (shared) and an `OpenExclusive` on the same directory fails: tests rely on this.
- New `(t *Tenant) Raw() *sql.DB`: returns the writer connection pool only when the tenant was opened with `OpenExclusive`, otherwise `nil`. Document that it exists for offline compaction only.
- Migration 5 (append it; never edit earlier ones): `CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);` plus a seed `INSERT INTO meta(key,value) SELECT 'compaction','complete' WHERE NOT EXISTS (SELECT 1 FROM facts);` so a ledger that is empty when it migrates never needs compaction. A ledger with rows gets no seed, so it is `required`.
- Meta API on `Tenant`: `Meta(ctx, key) (string, bool, error)` and `SetMeta(ctx, key, value string) error` (SetMeta goes through the writer queue; it is an upsert).
- `(t *Tenant) CompactionState() string` returns `"complete"` when meta `compaction` equals `complete`, else `"required"`. Package function `CompactionStateOf(dir string) string` answers the same for a directory whose tenant is not open: it opens `ledger.db` read-only (`file:<path>?mode=ro`), treats a missing `meta` table or key as `required` unless `facts` has no rows (then `complete`), and a missing `ledger.db` as `complete`. It must not migrate or write.
- `/v1/health` gains `"compaction"`. Value: `"required"` if any tenant directory under `cfg.Data` (a subdirectory holding `ledger.db`) is `required`, else `"complete"`. Use `CompactionState()` for open tenants and `CompactionStateOf` for the rest. Existing fields are unchanged.
- Serve start: add `serve.Preflight(dataDir string) error`. For each tenant directory under `dataDir` holding `ledger.db` it tries a shared lock (take and release), and on `ErrLocked` returns an error naming the tenant and telling the operator to wait for or stop `workflow ledger compact`. `runServe` calls it before `net.Listen` and exits 1 printing the error. `Server.tenant()` returning `ErrLocked` at request time must produce HTTP 503 whose body names the lock (follow how that function's errors are written today).
- `TestMigrationFast100k` fails with "migration too slow" under `go test -race` only (Phase 1 carried item). Fix by keeping the 100k timing assertion for normal runs and, under the race detector, skipping only the timing assertion (use a `raceEnabled` constant defined in two small files with `//go:build race` and `//go:build !race`; put them in the store package, new files `race_on_test.go` and `race_off_test.go`, which you also own). The migration must still run and the test must still log its duration.

### Keep untouched

`Append`, the writer queue, existing migrations 1-4, the drain flock in `internal/drain`, and every existing test's meaning. Update the two tests that read `len(migrations)` only if they break.

## Done evidence

Write the failing checks first (they fail to compile or fail until the code exists) and report output before and after.

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store/ -run 'Lock|Meta|Compaction' -v` → pass, with tests for: two `Open` on one dir both succeed; `OpenExclusive` fails with `ErrLocked` while an `Open` is held and `Open` fails with `ErrLocked` while an `OpenExclusive` is held (`errors.Is`); lock released after `Close`; `Raw()` is nil for `Open`; meta round-trip; a fresh empty ledger is `complete`; a ledger with a row inserted before migration 5 is `required`; `CompactionStateOf` on an unopened directory agrees and writes nothing (file mtime unchanged).
- `go test ./internal/serve/ -run CompactionState -v` → pass: `/v1/health` shows `"compaction":"required"` on a data dir holding a legacy ledger with rows, `"complete"` after `SetMeta('compaction','complete')`, and `Preflight` returns an error naming the tenant while a second handle holds `OpenExclusive`; a request to a locked tenant returns 503.
- `go test -race ./internal/store/` → pass (including `TestMigrationFast100k`).
- `go build ./... && go vet ./... && go test ./...` from `tools/workflow` → pass; paste the summary lines.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
