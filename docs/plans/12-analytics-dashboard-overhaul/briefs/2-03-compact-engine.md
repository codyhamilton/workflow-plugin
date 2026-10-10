# Brief: 2-03 — Compaction engine

Consumer: a Go worker (flash-tier; escalate to a Sonnet-tier on `blocked`) writing the batch engine that `workflow ledger compact` (2-04) calls.
Owned paths: `tools/workflow/internal/compact/` (new package: `compact.go`, `compact_test.go`), `tools/workflow/internal/store/plan.go` (new), `tools/workflow/internal/ingest/ingest.go` (only to add the exported `Envelope` wrapper described below). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/2-03-compact-engine.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 2-01, 2-02.
Runs alongside: nothing.
Budget: 8 files to read, about 400 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Ledger shape and compaction" (Stored hook facts, New columns, Compaction command) and "Domain: Capture and event policy" (policy table, collapse, norm_event) plus Phase 2 Outcome (binding).
2. `tools/workflow/internal/ingest/ingest.go` — `Ingest` (the loop from `for i, raw := range facts`) and `envelope`. Compaction must produce what this code produces for the same fact.
3. `tools/workflow/internal/ingest/policy.go` — `Policy`, `CollapseHash` (87 lines).
4. `tools/workflow/internal/ingest/normalise.go` and `extract.go` — `Derive(harness, event, payload)` and `Derived` fields (read the signatures and struct only).
5. `tools/workflow/internal/store/store.go` — `FactRow`, `Append` (columns and the `kind`/`plan` computation), plus 2-01's `OpenExclusive`, `Raw()`, `Meta`, `SetMeta` (read what 2-01 landed, not this brief's description of it).
6. `tools/workflow/internal/store/analytics.go` — `planOf` (lines 34-40).
7. `tools/workflow/internal/archive/archive.go` — `Append`, `Entry`, `Line`, and 2-02's `Repair`.
8. `tools/hooklog/tests/fixtures/ingest_policy.json` — shape only (`facts`, `expect`); `tools/workflow/internal/serve/ingest_policy_test.go` lines 55-80 shows how it is loaded.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A function that rewrites an existing ledger to the Phase 1 shape, in resumable batches, so that history and new ingest agree. It does not vacuum and it does not parse flags; 2-04 does.

## Contract

DESIGN "Compaction command", cited: "In one pass over existing hook facts it: 1. archives each body; 2. applies the policy table: `remove` rows are deleted with no archive line, and deltas are collapsed into one row per part using the collapse identity; 3. strips the payload and fills the new columns; 4. records completion in a store meta key." Phase 2 Outcome, cited: "`facts` has no removed-event rows. It has exactly one row per distinct delta part key. No hook fact carries a payload. The archive's distinct `row_hash` count equals the pre-compaction count of non-removed hook facts." and "Interrupting compaction and rerunning it ends in the same state."

Settled by this brief:
- Package `compact`. It cannot live in `internal/store` (the policy is in `internal/ingest`, which imports `store`). API: `func Run(ctx context.Context, t *store.Tenant, o Options) (Stats, error)`. `t` must come from `store.OpenExclusive` (`t.Raw()` is non-nil); otherwise `Run` returns an error.
- `Options`: `Batch int` (default 5000 rows), `Progress io.Writer` (one line per 50 batches: scanned, removed, collapsed, archived, elapsed; counts only, never row content), and test hooks `AfterArchive func(batch int) error` (called after `archive.Append`, before the SQL commit) and `AfterCommit func(batch int) error`. A non-nil hook error aborts `Run` with that error.
- `Stats`: `Scanned, Removed, Collapsed, Stripped, Archived, Backfilled int64`, plus `Complete bool`.
- Walk by `rowid` in ascending batches of `Batch`. The cursor is meta key `compact_cursor` (decimal rowid), updated in the same SQL transaction as the batch's row changes, so a crash leaves cursor and rows consistent. `Run` starts from the stored cursor (0 if absent). When the scan passes the last rowid it sets meta `compaction` to `complete` and returns `Complete: true`. If meta `compaction` is already `complete` and no row with a payload remains, `Run` returns quickly with zeros.
- Per `hook_event` row (decode `raw` with `UseNumber`, like ingest):
  - `Policy(harness, event, payload)` is `Remove`: delete the row, write no archive line.
  - Otherwise archive one `archive.Entry{ConversationID, TS: ts, Line{RowHash: <the row's existing row_hash>, ReceivedAt: <the row's received_at>, Fact: <the row's raw bytes as stored>}}` before touching SQL, one `archive.Append` per batch, so the archive holds the full received body verbatim. Historical `raw` is the canonical received fact (it is what ingest archived and hashed), so it is used as is.
  - `Collapse`: compute `CollapseHash`. If a row with that hash already exists (an earlier batch's survivor, or a post-Phase-1 ingest), delete this row and set the survivor's `ts` to the minimum of the two. Otherwise change this row's `row_hash` to the collapse hash and treat it as the survivor. The survivor's `ts` is the minimum `ts` over the part.
  - Survivors and `Keep` rows: replace `raw` with `ingest.Envelope(obj)` (stored form: no `id`, `content`, `payload`) and fill `norm_event`, `tool`, `model`, `tok_*`, `cost_reported` from `ingest.Derive(harness, event, payload)`, exactly as `ingest.Ingest` does. `row_hash` of `Keep` rows is unchanged. A delta lacking the collapse key is `Keep`.
- Per non-hook row (`artifact_version`, `commit`): leave `raw` as is and fill `kind` (`keys.Kind(path)`), `plan` (new exported `store.PlanOf(path)` in `store/plan.go`, a wrapper of `planOf`), `source` and `sha` (from the string keys `source` and `sha` of `raw`, empty if absent). This is required because Phase 3 reads these columns for the whole ledger; count it in `Backfilled`.
- Add `func Envelope(obj map[string]any) ([]byte, error)` to `internal/ingest/ingest.go` that returns `envelope(obj)`; change nothing else in that file.
- Do not use the writer queue for the batch transaction: use `t.Raw()`, one transaction per batch, `PRAGMA wal_checkpoint(TRUNCATE)` every 20 batches so the WAL stays bounded on a 10 GB ledger.
- Memory is bounded by the batch size. Never load the table.

### Keep untouched

`internal/ingest` behaviour for live ingest, `internal/archive` format, the migration list, `Tenant.Append`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

All in `tools/workflow/internal/compact/compact_test.go`, using the shared fixture `tools/hooklog/tests/fixtures/ingest_policy.json` to build a legacy ledger (insert each fact as an old-style row: `raw` = `keys.Canonical` of the fact including `payload`, `row_hash` = `keys.RowHash`, new columns at defaults, `type`/`event`/`ts` set; add three `artifact_version` and one `commit` row with `path`/`source`/`sha`).
- `Equivalence`: ingest the fixture into tenant A through `ingest.Ingest`; load it as legacy rows into tenant B and `Run`. Compare A and B `facts` by `row_hash`, `type`, `event`, `ts`, `raw`, `norm_event`, `tool`, `model`, `tok_*`, `cost_reported`, `kind`, `plan`, `source`, `sha` (not `received_at`): identical. The set of distinct archive `row_hash` values in B equals that of A's archive.
- `Outcome`: after `Run` on B, no row of a removed event, exactly one row per distinct part key, `instr(raw,'"payload"')=0` for every hook fact, and distinct archive `row_hash` count equals the pre-run count of non-removed hook rows.
- `Resume`: run with a hook that returns an error after batch k (once with `AfterArchive`, once with `AfterCommit`), with `Batch` of 3 so several batches exist; call `Run` again; the final `facts` rows and the set of distinct archive `row_hash` values equal an uninterrupted run's. Duplicated archive lines are allowed; `archive.Read` dedupes.
- `Repair`: a torn archive file present before `Run` does not make the second run fail (call `archive.Repair` first in `Run`, and test it).
- `Preexisting survivor`: a legacy delta whose collapse-hash row already exists is deleted and the survivor's `ts` becomes the minimum.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test -race ./internal/compact/ ./internal/ingest/ ./internal/store/ && go vet ./... && go build ./...` → pass; paste the summary lines.
- Report a rough throughput figure (rows per second) from a 50,000-row synthetic ledger run without `-race`, so 2-05 can estimate the real run.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
