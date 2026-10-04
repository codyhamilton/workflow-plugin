# Execution report: 1-02 Tenant store and group-commit writer

Status: done.

## Done against the brief
- `tools/workflow/internal/store` implements the exported API of the brief with the names unchanged. SQLite is `modernc.org/sqlite` v1.60.1 (no cgo); DSN pragmas WAL, synchronous NORMAL, busy_timeout 5000. One `*sql.DB` with `SetMaxOpenConns(1)` for the writer, a second for reads.
- All writes (facts, rejections, screens, scores) go through one writer goroutine per tenant. It collects requests for `GroupWindow` (default 2 ms) into one transaction. If a group errors it rolls back and runs each request alone, so a failing request does not fail the others.
- Schema via `PRAGMA user_version` and an ordered `migrations` slice (migration 1 creates the four tables and indexes). `received_at` is Unix nanoseconds set at append; "latest" orders by `received_at` then `rowid`.
- Hashes are validated as 64 lowercase hex before any path is built. Blob and pending writes: temp file under `<tenant>/tmp/`, fsync, rename; files 0600, dirs 0700.
- Evidence: tests were written first and failed to compile (`undefined: Options`). Afterwards `go vet ./... && go test ./...` passes; `go test -race -count=3 -run 'Append|Concurrent'` passes (50 concurrent appenders, no SQLITE_BUSY, re-append returns `inserted=false`, a group with one failing request commits the others); the Pending/Promote/Artifact tests pass.
- `writer-burst: tenants=8 facts=4800 p50=11.076127ms p99=30.070506ms db_bytes=5992448` (latency is per Append request of 20 facts, measured at the client including queue wait; p99 varied 20-30 ms across runs).

## Departures
- Rows with empty `Raw` are rejected with an error inside the writer transaction. `INSERT OR IGNORE` silently swallows the NOT NULL violation, so an explicit check was needed; it is also what the failing-request test uses.
- The tenant directory gets a fourth subdirectory `tmp/` for atomic-write temp files (brief said "temp file in the tenant dir").
- Added indexes `facts_artifact`, `facts_content`, `facts_conv` and per-hash indexes on rejections, screens, scores (brief asked for indexes, not their names).

## Behaviour choices
- `Promote` moves the pending file with `os.Rename` before the `screens` row; if the blob already exists it removes any pending file and only records the screen. Promote with neither blob nor pending returns the rename error.
- `DropPending` fills `Rejection.ContentHash` with the hash when empty.
- `PendingHashes` orders by file mtime then name; arrival order is only as fine as filesystem mtime resolution.
- `Append` validates `ContentHash` (when non-empty) but not `RowHash`.

## Unfinished / known problems
- Promote's file move and the screens insert are not atomic together: a crash between them leaves a blob with no screens row. Phase 3's worker should re-promote (idempotent) on restart.
- A request whose context is cancelled after queueing may still commit.
