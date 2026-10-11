# Brief: 3-16 — Compaction keeps the hourly rollup exact

Consumer: a Go worker (flash-tier); the orchestrator (phase proof 3-13).
Owned paths: `tools/workflow/internal/compact/` (compact.go and tests), `tools/workflow/internal/store/rollup.go` and `rollup_test.go` (only a rebuild helper). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-16-compact-keeps-rollup-exact.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-12.
Runs alongside: 3-14 (it owns other paths).
Budget: 5 files to read, about 150 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/reports/3-12-fix-misses-indexes-rollups.md` — the rollup, and the Concern section.
2. `tools/workflow/internal/store/rollup.go` — `hookRollupUpsert`, `backfillHookRollup`.
3. `tools/workflow/internal/compact/compact.go` lines around the delete (about 276) and update (about 280-285) of `hook_event` rows.

Read ranges and grep; do not read a whole file to find one section.

## Goal

After `compact.Run`, `hook_events_hourly` equals the base-row hook_event aggregates exactly, whether or not compaction changed any row, and a resumed run also ends exact.

## Contract

Settled by this brief:
- The rollup is an aggregate of `facts` rows with `type='hook_event'` keyed `(hour, harness, repo_id, norm_event, event, tool, conversation_id)` as 3-12 built it.
- Compaction deletes and rewrites hook_event rows in batches. Simplest correct rule: when `compact.Run` finishes (including a run that resumes, and one that finds nothing to do), it rebuilds the rollup from base rows in one transaction (add an exported rebuild helper beside `backfillHookRollup` that deletes all rollup rows and refills). Do not maintain it per batch.
- `Append` and the rest of 3-12's behaviour do not change.

## Done evidence

- A compact test: build a small ledger with removable and collapsible hook_event rows, run `compact.Run`, and assert rollup rows equal base-row aggregates in both directions (EXCEPT both ways). A second test interrupts after the first batch, resumes, and asserts the same.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store ./internal/compact ./internal/serve` passes, plus `go vet` and `gofmt -l`.

## Report back

Under 1,000 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output, any deviation and why, any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

Do not spawn agents beyond read-only research helpers.
