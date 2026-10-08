# Brief: 1-01 — Event archive package

Consumer: a Go worker (Sonnet-tier is enough) building the on-disk archive that unit 1-05 (ingest policy) writes to and that later transcript tools read.
Owned paths: `tools/workflow/internal/archive/` (new), `tools/workflow/go.mod`, `tools/workflow/go.sum`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report (`git add <paths>`, `git commit -- <paths>`) because other units commit in parallel.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/1-01-archive-package.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 1-02, 1-03, 1-04.
Budget: 5 files to read, about 250 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — section "Domain: Event archive" (binding), and "Domain: Capture and event policy" only for what an archive line holds.
2. `tools/workflow/internal/keys/keys.go` — `Canonical`, `RowHash` (lines 22-61).
3. `tools/workflow/internal/store/store.go` lines 290-370 — how `writeAtomic` and the tenant directory are handled, to match file-mode conventions (0o600 files, 0o700 dirs).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A small package that appends hook bodies verbatim to `<tenant dir>/archive/<YYYY-MM>/<conversation_id>.jsonl.zst` and reads one conversation's lines back in time order, so the ledger can stop storing bodies without losing the only copy.

## Contract

Cited from DESIGN.md "Domain: Event archive":
- Layout `<tenant dir>/archive/<YYYY-MM>/<conversation_id>.jsonl.zst`, one file per conversation per UTC month of fact `ts`. Each line is `{"row_hash","received_at","fact":<canonical received fact JSON>}`.
- "Archiving is at-least-once ... a redelivered event can appear twice, and readers deduplicate by `row_hash`."
- "A store function reads one conversation's archive lines in time order. This design exposes no HTTP route for it."
- Non-goals: HTTP serving, search, retention, replication.

Settled by this brief (so you do not re-derive):
- Compression is zstd via `github.com/klauspost/compress/zstd` (add to go.mod; network access to the Go proxy works, Go is at `~/.local/go/bin`, put it on PATH). There is no zstd in the standard library and none in the module cache today.
- Appending writes one complete zstd frame per file per call; concatenated frames are a valid zstd stream and readers decode them as one. Never rewrite an existing file.
- API (unit 1-05 and a later transcript reader code to this; keep the names):
  ```go
  type Line struct {
      RowHash    string          `json:"row_hash"`
      ReceivedAt int64           `json:"received_at"` // UnixNano, same unit as facts.received_at
      Fact       json.RawMessage `json:"fact"`
  }
  type Entry struct { ConversationID string; TS float64; Line Line } // TS = fact ts, picks the month
  func Append(tenantDir string, entries []Entry) error // groups by file, one frame each, fsync before return
  func Read(tenantDir, conversationID string) ([]Line, error) // all months, deduplicated by RowHash (first wins), ordered by fact ts then arrival
  ```
- File name safety: a conversation ID is arbitrary text from a hook. Map it to a filename deterministically and injectively (percent-escape anything outside `[A-Za-z0-9._-]`, and escape a leading `.`), identically in Append and Read. It must not escape the archive directory.
- Appends in one process are serialised by a package-level mutex. Cross-process locking is out of scope (Phase 2 owns the tenant lock).
- `Read` of a conversation with no archive returns an empty slice and nil error.

### Keep untouched

Everything outside the owned paths. Do not add the package to any caller; unit 1-05 wires it.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/archive/` → pass. Tests cover: two Appends to one conversation produce a file that `zstd -dc` prints as lines in order; entries with ts in two UTC months land in two month directories (include a ts at 23:59:59 on the last day of a month); `Read` deduplicates a repeated `RowHash` and orders by ts; hostile IDs (`../x`, `a/b`, `.hidden`, empty-looking) stay inside `archive/` and round-trip through Read; 8 goroutines appending to one conversation produce a stream that decodes with no torn lines.
- `PATH=$HOME/.local/go/bin:$PATH go build ./... && go vet ./internal/archive/` from `tools/workflow` → clean.
- `git diff --stat` shows only owned paths.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
