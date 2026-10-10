# Report: 2-01 — Tenant-dir lock, meta table and compaction state in health

Status: **done with concerns** (migration 5 had to be made idempotent; see Deviations).

## What changed

All against brief 2-01, on branch `plan/12-analytics-dashboard-overhaul`.

- `internal/store/lock.go` (new): `ErrLocked` sentinel; `.lock` file mode 0600; `acquireLock` with non-blocking `LOCK_SH`/`LOCK_EX`; `releaseLock`; exported `TrySharedLock(dir)` probe (take+release).
- `internal/store/store.go`: migration 5 (append only) creates `meta` and seeds `compaction='complete'` for an empty ledger. `Tenant` gains `lock`/`exclusive`. `Open` = shared lock, takes it before SQLite/migration, holds to `Close`; `OpenExclusive` = exclusive. `Close` releases the lock. Added `Raw()` (writer pool only under `OpenExclusive`, else nil), `Meta`, `SetMeta` (writer-queue upsert), `CompactionState`, and package `CompactionStateOf(dir)` (read-only `file:<path>?mode=ro`, no migrate/write).
- `internal/store/store_test.go`: `TestMigrationFast100k` timing assertion gated by `raceEnabled`. `race_on_test.go` (`//go:build race`) / `race_off_test.go` (`!race`) define it. Migration still runs and logs its duration.
- `internal/store/lock_test.go` (new): two shared `Open`s coexist; `OpenExclusive` vs shared and `Open` vs exclusive both `errors.Is(ErrLocked)`; lock released after `Close`; `Raw()` nil for `Open`; meta round-trip; fresh ledger complete; legacy-with-rows required; `CompactionStateOf` agrees and leaves ledger.db mtime unchanged; missing ledger.db complete.
- `internal/serve/serve.go`: `Preflight(dataDir)` probes each tenant dir holding ledger.db; `auth` turns `store.ErrLocked` into 503 whose body is the lock error; `/v1/health` gains `"compaction"` (`required` if any tenant dir under `cfg.Data` is required, using `CompactionState` for open tenants and `CompactionStateOf` otherwise).
- `internal/serve/compaction_state_test.go` (new): health `required` → `complete` after `SetMeta`; `Preflight` error names tenant while `OpenExclusive` held; request to a locked tenant is 503 naming the lock.
- `cmd/workflow/main.go`: `runServe` calls `serve.Preflight(cfg.Data)` before `net.Listen`; on error prints and returns 1.

Not touched: `Append`, writer queue, migrations 1–4, `internal/drain`.

## Check output

Before (tests written first): store build failed with `undefined: OpenExclusive/ErrLocked`, `Raw/Meta/SetMeta/CompactionState` missing; serve build failed with `SetMeta/OpenExclusive/Preflight` missing.

After:
- `go test ./internal/store/ -run 'Lock|Meta|Compaction' -v` → all 7 PASS.
- `go test ./internal/serve/ -run CompactionState -v` → both PASS.
- `go test -race ./internal/store/` → `ok … 15.5s`.
- `go build ./... && go vet ./... && go test ./...` → build OK, vet OK, every package `ok` (store, serve, cmd/workflow, drain, etc.).

## Deviations from the brief

1. **Migration 5 uses `CREATE TABLE IF NOT EXISTS meta`** (brief specified `CREATE TABLE meta`). The brief says only the two `len(migrations)` tests can break when migration 5 is appended; they did not. Instead two *other* existing tests rewind `user_version` after an initial `Open` without dropping `meta`: `store_test.go` `TestMigrationFast100k` and `internal/serve/reads_test.go` `TestAdvisoryReads/backfill`. The first is owned and would be an extra edit; the second is **not** in the owned paths, and the brief forbids touching it. `IF NOT EXISTS` (precedent: migration 3 already does this) makes migration 5 idempotent and keeps both tests' meaning. This resolves the brief/contract contradiction; it is not resolved silently.
2. **Added exported `store.TrySharedLock`** for `Preflight`. The brief named no store probe entry point; keeping lock-path and flock knowledge in `store` beats duplicating them in `serve`.
3. **`store_test.go` edit is only the race timing guard** — the two `len(migrations)` tests needed no change.
4. **Serve legacy fixture** (`compaction_state_test.go`) builds a minimal `facts` table at `user_version = 4` with raw SQL. A genuinely pre-migration-5 ledger cannot be produced through the store API: a ledger that is empty when it migrates is always seeded `complete`, so the `required` path needs rows present before migration 5.

## Problems / unfinished

- No known problems in the delivered code. `CompactionStateOf` relies on a read-only open of the WAL ledger; the test confirms it reads without changing ledger.db mtime. `raw`/`OpenExclusive` hold the writer pool for 2-03; no caller uses `Raw()` here.
- Unfinished (by design, later units): 2-03 compaction engine consumes `OpenExclusive`/`Raw`/`SetMeta`, 2-04 adds `workflow ledger compact`, which `Preflight`'s message already references.
