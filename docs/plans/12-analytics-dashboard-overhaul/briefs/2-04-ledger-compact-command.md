# Brief: 2-04 — `workflow ledger compact` command

Consumer: a Go worker (flash-tier) wiring the CLI around `compact.Run`; its consumer is the operator and unit 2-05.
Owned paths: `tools/workflow/cmd/workflow/ledger.go` (new), `tools/workflow/cmd/workflow/ledger_test.go` (new), `tools/workflow/cmd/workflow/main.go` (only the `ledger` case and the `usage` string), `tools/workflow/internal/compact/finish.go` (new), `tools/workflow/internal/compact/finish_test.go` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/2-04-ledger-compact-command.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 2-03 (and through it 2-01, 2-02).
Runs alongside: nothing.
Budget: 6 files to read, about 300 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Compaction command" paragraph under "Domain: Ledger shape and compaction" (binding) and the Phase 2 Outcome.
2. `tools/workflow/cmd/workflow/main.go` — whole file (161 lines): `run`, `usage`, and how `serve` and `drain` return exit codes.
3. `tools/workflow/internal/compact/compact.go` — `Run`, `Options`, `Stats` as 2-03 landed them (read the code, not this brief).
4. `tools/workflow/internal/store/store.go` — `OpenExclusive`, `ErrLocked`, `Raw()`, `Meta` from 2-01.
5. `tools/workflow/cmd/workflow/main_test.go` — how existing tests call `run` and capture output.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

An operator runs `workflow ledger compact --tenant-dir <dir>`; it refuses safely when it cannot finish, compacts, vacuums, and reports before and after rows and bytes.

## Contract

DESIGN, cited: "`workflow ledger compact --tenant-dir <dir>` is offline and resumable. It runs when it can take an exclusive lock on the tenant dir ... Then it runs `VACUUM`. Before it starts it prints the free space it needs and refuses if that space is not available. It reports rows and bytes before and after." Phase 2 Outcome: "It completes and reports before and after rows and bytes."

Settled by this brief:
- Arguments: `workflow ledger compact --tenant-dir <dir>` (required; no default, so nothing runs against the live ledger by accident). Any other shape prints usage and exits 2. Add `ledger` to `usage`.
- Steps, in order, each printing one line to stdout:
  1. `store.OpenExclusive(dir)`. `ErrLocked` prints its message and exits 1.
  2. Before: row counts (`facts` total and by `type`), bytes of `ledger.db`, `ledger.db-wal`, and the `archive/` directory (sum of file sizes).
  3. Free-space check in `compact/finish.go`: `NeedBytes(t)` = (sum of `length(raw)` over `hook_event` rows) / 3 for the archive, plus the estimated final database size (current `ledger.db` size minus the sum of `length(raw)` over `hook_event` rows, floored at 64 MiB), plus 256 MiB of WAL headroom. `FreeBytes(dir)` uses `syscall.Statfs` on the tenant dir, via a package variable so tests can fake it. Print both numbers in MiB. If free < need, exit 1 with "need X MiB, have Y MiB" and change nothing. If compaction is already `complete` (meta), skip the check and the run, and go straight to VACUUM.
  4. `compact.Run` with `Progress` to stdout. SIGINT or SIGTERM cancels its context; `Run` stops at a batch boundary and the command prints "interrupted; rerun the same command to resume" and exits 1.
  5. `VACUUM` on `t.Raw()`, then `PRAGMA wal_checkpoint(TRUNCATE)`.
  6. After: the same counts and bytes as step 2, plus the elapsed time. Exit 0.
- Output is counts and sizes only. Never print row content, payloads or paths of individual facts.
- A rerun on a completed ledger exits 0 after printing after-counts (VACUUM may still run).

### Keep untouched

`runServe`, `drain`, `status`, `mcp`, `version` cases and their tests.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./cmd/workflow/ -run Ledger -v` → pass. Tests build a small legacy ledger in `t.TempDir()` (reuse the approach in 2-03's tests; copy the helper rather than import test code) and cover: success path output contains before and after row counts and bytes and the after counts show no removed-event rows; missing `--tenant-dir` exits 2; a tenant held by another `OpenExclusive` handle exits 1 with the lock message and leaves the database unchanged; the faked free-space function below the estimate exits 1 and changes nothing; cancelling the context mid-run (use the `compact.Options` hook through a package-level test seam) exits 1 and a second invocation completes with the same final facts as an uninterrupted run; a rerun on a completed ledger exits 0.
- `go test ./internal/compact/ -run Finish` → `NeedBytes` and `FreeBytes` unit tests pass.
- `go build ./... && go vet ./... && go test ./...` from `tools/workflow` → pass; paste the summary lines.
- Build the binary (`go build -o <scratchpad>/workflow ./cmd/workflow`) and run it with no arguments and with `ledger` alone; paste the two usage outputs.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
