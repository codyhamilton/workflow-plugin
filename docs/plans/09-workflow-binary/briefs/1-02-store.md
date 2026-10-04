---
brief_id: 211
design_id: 209
---

# Brief: 1-02 — Tenant store and group-commit writer

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its API is consumed by unit 1-03
(ingest and HTTP), then by phase 3 (screening writes) and phase 4 (advisory reads).
Owned paths: `tools/workflow/internal/store/`, `tools/workflow/go.mod`, `tools/workflow/go.sum`,
`docs/plans/09-workflow-binary/reports/1-02-store.md`. Touch nothing else.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: 1-01 (the module exists; `internal/keys` for `ContentHash`).
Runs alongside: nothing (shares `go.mod`).
Budget: 6 files to read, about 700 lines to write including tests, 50 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/design/03-remote-service.md` — Storage, Writer, Tables, Behind an interface (lines 109-145),
   Screening and scoring (lines 147-177, for the pending/blobs/screens states), Tests 3 (line 213). Binding.
2. `docs/design/04-advisory-surface.md` — API, the `/v1/artifacts` row (lines 52-60). Binding for the
   shape `Artifact` must be able to fill.
3. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 1 (lines 141-153).
4. `tools/workflow/internal/keys/` — the exported names only (`go doc ./internal/keys`).
5. `docs/plans/09-workflow-binary/reports/1-01-module-keys-secrets.md` — departures from 1-01's brief, if any.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

`internal/store`: one tenant directory (`ledger.db`, `blobs/`, `pending/`), append-only fact
storage through a single group-commit writer per tenant, the content-addressed blob and pending
store, and the reads `/v1/artifacts` needs. It is the `Store` of design 3 "Behind an interface",
with SQLite as its only implementation.

## Contract

Cited, settled:

- Design 3 Storage: "`ledger.db`: SQLite in WAL mode, `synchronous=NORMAL`"; "`blobs/<aa>/<hash>`:
  content stored by SHA-256, written once. Rows hold the hash, never the bytes"; "`pending/<hash>`:
  content awaiting the screen".
- Design 3 Writer: "Each open tenant has one writer goroutine. Ingest requests hand their facts to
  it and wait. The writer takes everything queued within a few milliseconds into one transaction
  (group commit), and each request is answered after its commit. There are no concurrent writers,
  so no `SQLITE_BUSY`. Readers use separate connections and run alongside under WAL."
- Design 3 Tables: "`INSERT OR IGNORE` keyed by row hash, never `UPDATE` on facts", and the four
  tables `facts`, `rejections`, `screens`, `scores` with the columns listed there.
- Design 3 Runtime: "No cgo. SQLite is the pure-Go `modernc.org/sqlite`".

Decisions made at refine (settled):

- Every write (facts, rejections, screens, scores) goes through the writer goroutine; there is no
  other write path to `ledger.db`.
- A failing request must not fail the others in its group: if a group transaction errors, roll it
  back and run each request of that group in its own transaction.
- `received_at` is set by the store at append time as INTEGER Unix nanoseconds; order "latest" by
  `received_at` then `rowid`.
- `facts` columns exactly as design 3 lists (row_hash primary key, type, conversation_id, harness,
  event, ts REAL, received_at, repo_id, path, content_hash, raw). Commit SHA, touched paths and
  `source` stay in `raw` (read with `json_extract`); add indexes, not columns.
- Schema versioned with `PRAGMA user_version` and an ordered migration list, so phases 3 and 4 append
  migrations (for example an FTS5 table) without editing earlier ones.
- Hashes are validated as 64 lowercase hex before any path is built from them.

## Changes

Add `modernc.org/sqlite` (`go get` from `tools/workflow`; the proxy is reachable). Open with DSN
pragmas `journal_mode(WAL)`, `synchronous(NORMAL)`, `busy_timeout(5000)`. One `*sql.DB` with
`SetMaxOpenConns(1)` for the writer, a separate `*sql.DB` for reads.

Exported API (a contract for 1-03; keep the names):

```go
type Options struct{ GroupWindow time.Duration } // default about 2 ms
func Open(dir string, opts Options) (*Tenant, error) // creates dir, blobs/, pending/, migrates
func (t *Tenant) Close() error                       // finishes queued writes, then closes

type FactRow struct {
    RowHash, Type, ConversationID, Harness, Event string
    TS float64
    RepoID, Path, ContentHash string
    Raw []byte // canonical fact JSON without id or content
}
func (t *Tenant) Append(ctx context.Context, rows []FactRow) (inserted []bool, err error)

type Rejection struct{ Stage, FactType, ConversationID, Path, ContentHash, Pattern, Reason string }
func (t *Tenant) AppendRejection(ctx context.Context, r Rejection) error

func (t *Tenant) HasBlob(hash string) bool
func (t *Tenant) WritePending(hash string, content []byte) error // tmp + rename; no-op if blob or pending exists
func (t *Tenant) PendingHashes() ([]string, error)                // arrival order
func (t *Tenant) ReadPending(hash string) ([]byte, error)
type Screen struct{ Verdict, Scorer string }
func (t *Tenant) Promote(ctx context.Context, hash string, s Screen) error // pending → blobs/<aa>/<hash>, then a screens row
func (t *Tenant) DropPending(ctx context.Context, hash string, r Rejection) error // phase 3's flag path
type Score struct{ Check string; Result float64; Scorer string }
func (t *Tenant) AppendScores(ctx context.Context, hash string, s []Score) error
func (t *Tenant) ReadBlob(hash string) ([]byte, error)

type ScreenRow struct{ Verdict, Scorer string; At time.Time }
type ScoreRow struct{ Check string; Score float64 }
type Latest struct {
    ContentHash string; ReceivedAt time.Time; ConversationID, Source string
    Screen *ScreenRow; Scores []ScoreRow
}
type Artifact struct{ RepoID, Path string; Versions int; Latest Latest }
func (t *Tenant) Artifact(ctx context.Context, repoID, path string) (*Artifact, error) // nil, nil when none
```

`Artifact` reads `artifact_version` facts only. `Versions` counts distinct content hashes; `Latest`
is the newest fact; `Screen` is the newest `screens` row for its hash, or nil; `Scores` the newest
row per check for its hash. `Promote` of an existing blob just records the screen. Blob and pending
writes are atomic (temp file in the tenant dir, fsync, rename), files mode 0600, dirs 0700.

### Keep untouched

`internal/keys`, `internal/secrets` and anything outside the owned paths. Do not add HTTP, precheck
or ingest logic here; that is 1-03.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

- `go vet ./... && go test ./...` → passes.
- `go test -race -run 'Append|Concurrent' ./internal/store` → 50 goroutines appending at once all
  succeed with no `SQLITE_BUSY`; re-appending the same rows returns `inserted=false`; a group
  containing one failing request still commits the others.
- `go test -run 'Pending|Promote|Artifact' -v ./internal/store` → content written to `pending/`,
  promoted to `blobs/<aa>/<hash>` with `pending/<hash>` gone and a `screens` row (`unscreened`);
  `DropPending` removes the file and records the rejection; `Artifact` returns `Versions`, `Latest`
  and `Screen` as defined, and nil for an unknown path.
- `go test -run TestWriterBurst -v ./internal/store` → design 3 Test 3: 8 tenants, each with 10
  concurrent clients sending bursts of 20 facts carrying realistic raw JSON (about 1 KB), prints one
  line `writer-burst: tenants=8 facts=<n> p50=<d> p99=<d> db_bytes=<total>`. No threshold; quote the
  line in your report.

Safety: test only in temp dirs (`t.TempDir()` or `mktemp -d`). Never read or write
`~/.local/share/workflow*`, the live queue, or the legacy service. Never print or log
`TYPESAFE_API_KEY` or any key.

Commit: title `[exec <execution_id>] Phase 1: tenant store and group-commit writer` (the
orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write `docs/plans/09-workflow-binary/reports/1-02-store.md`
(design 1, Execution report: what was done against this brief, verifiably, including the
`writer-burst` line; departures and why; unfinished work; known problems; nothing derivable) and
include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
