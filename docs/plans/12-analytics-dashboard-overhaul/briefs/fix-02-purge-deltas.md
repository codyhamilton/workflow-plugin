# Brief: fix-02 — Offline rewrite deletes every `message.part.delta` fact and archive line

Consumer: a worker (flash-tier) writing Go in the archive, compact and CLI packages. Fixer unit after Phase 3: it closes no phase and its commit carries no `Workflow-Phase` trailer.
Owned paths: `tools/workflow/internal/archive/` (archive.go and tests), `tools/workflow/internal/compact/` (a new `purge.go`, `purge_test.go`; do not alter `Run`), `tools/workflow/cmd/workflow/ledger.go`, `tools/workflow/cmd/workflow/ledger_test.go` (or the existing CLI test file), the `usage` string in `tools/workflow/cmd/workflow/main.go`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, plain-summary title, no `Workflow-Phase` trailer. Stage only owned paths and the report. End the message with these two trailer lines: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_011T4Vh5cPS7acScndWmdobz`.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/fix-02-purge-deltas.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit. Your final message: the commit hash and a short summary.
Depends on: fix-01 (committed: delta is `Remove`, collapse deleted).
Runs alongside: nothing.
Budget: 8 files to read, about 350 lines to change, 60 tool turns. Past the budget, stop: write a handoff report, commit what passes, report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...`. Repo: `/home/codyh/workspace/workflow-plugin`, branch `plan/12-analytics-dashboard-overhaul`. Never touch `~/.local/share/workflow` or `/var/tmp/workflow-compact-copy/` itself; do not run against real data in this unit (the orchestrator's verifier does).

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` "Amendments after sign-off"; `IMPLEMENTATION.md` Phase 3 Carried item 12.
2. `docs/plans/12-analytics-dashboard-overhaul/reports/3-17-compact-rebuilds-all-rollups.md` and `reports/2-04-ledger-compact-command.md`.
3. `tools/workflow/internal/archive/archive.go` (`Append`, `readFile`, `linesOf`, `Repair`, `rewriteFile`).
4. `tools/workflow/internal/compact/compact.go` (`Run`, its deferred `RebuildRollups`, `metaValue`/`putMeta`), `cmd/workflow/ledger.go` (`compactTenant`, `vacuum`, `ledgerCounts`) and `internal/store/lock.go` (`OpenExclusive`).

## Goal

`workflow ledger purge-deltas --tenant-dir <dir>` removes every `message.part.delta` fact from `ledger.db` and every delta line from the archive, rebuilds all rollups, and vacuums. It is offline under the exclusive tenant lock, resumable and idempotent. A purged ledger has no delta anywhere, and a second run changes nothing.

## Contract (settled by this brief)

- Sibling subcommand, not a flag on `compact`: `ledger purge-deltas`. Same flags and exit codes as `ledger compact` (exit 1 locked, short of space, interrupted; 2 usage). It must not create a missing tenant dir: fail with exit 1 if `ledger.db` does not exist. Update `usage` strings (`main.go` and `ledger.go` dispatch) to list it.
- Archive: add `archive.Filter(tenantDir string, keep func(Line) bool) (FilterStats, error)` (name it as you like, exported, documented). It repairs nothing itself; call `archive.Repair` first from the caller. For each `archive/*/*.jsonl.zst` it decodes the file, and if any line is dropped, rewrites atomically (temp file in the same dir, fsync, rename; reuse `rewriteFile`) as one frame holding the surviving lines in order, duplicates kept; if no line survives, delete the file (and remove the month dir if it becomes empty). A file with no dropped line is left byte- and mtime-identical. A killed run leaves each file either old or new, never torn; the temp file is cleaned or ignored on the next run. Memory is bounded by one file's lines (one conversation-month); the biggest compressed file is small enough, but do not load all files at once. Take the package mutex as `Repair` does.
- A line is a delta if its `fact` JSON has `"event":"message.part.delta"` (decode only `harness`/`event` cheaply; do not require the payload to parse). The predicate belongs to the caller (`compact`), not `archive`.
- Ledger: `compact.PurgeDeltas(ctx, t *store.Tenant, o Options) (PurgeStats, error)` with `t` from `store.OpenExclusive`. Steps in order: `archive.Repair`; delete `facts` rows with `event='message.part.delta'` (and `harness='opencode'`) in batches of `o.Batch` (default 5000) by rowid, each batch its own transaction, so a kill leaves a consistent partial state; archive filter; `t.RebuildRollups(ctx)`; return counts (facts deleted, archive lines dropped, files rewritten, files deleted). Resumability needs no cursor: every step is idempotent and re-derivable from the data, and each step is safe to repeat after a kill between steps. Order the facts delete before the archive filter, and the rollup rebuild last, and say in a comment why a rerun converges. Run the rollup rebuild even when nothing was deleted (as `compact.Run` does). Respect `ctx` cancellation between batches and files.
- CLI: print `before:`/`after:` lines using `ledgerCounts`, plus the purge counts line, then `vacuum` (reuse it), then `PRAGMA wal_checkpoint(TRUNCATE)` as `vacuum` does. Run `compact.NeedBytes`-like space check is not required; require free space of at least the current `ledger.db` size (VACUUM copy) and refuse otherwise.
- Do not alter `compact.Run` or the `compaction` meta key.

## Done evidence

Write the failing tests first. Tests use temp tenants, never real data.

- `archive` test: a tenant with three conversation-months, one with only deltas (file deleted), one mixed (rewritten, survivors in order, duplicates kept), one with none (bytes and mtime unchanged); a second `Filter` call changes nothing; a file with a torn tail is handled after `Repair`.
- `compact` test: a ledger with `message.part.delta` and other facts in several conversations (hook rows plus a non-hook row), compacted state `complete`. After `PurgeDeltas`: zero delta rows, other rows byte-identical, every rollup equals its base aggregate in both EXCEPT directions (reuse the helper in `rollup_test.go`), archive lines for non-delta facts all still present by `row_hash`. A resumed run (cancel after the first batch via `AfterCommit`-style hook or context, then rerun) ends in the same state; a third run reports zero deleted. A delta whose conversation exists only through delta rows: the conversations rollup loses that conversation after purge.
- CLI test: `ledger purge-deltas` on a temp tenant exits 0 and prints before/after lines; on a missing dir exits 1 and creates nothing; while another process holds the lock it exits 1.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go build ./... && go vet ./... && go test ./...` passes; `go test -race ./internal/archive ./internal/compact` passes; `gofmt -l .` prints nothing.

## Report back

Under 1,000 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output, any deviation and why, any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

Do not spawn agents beyond read-only research helpers.
