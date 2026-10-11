# Brief: 3-17 — Compaction rebuilds every rollup, and the conversations rollup is tested with buckets

Consumer: a Go worker (flash-tier); the orchestrator (phase proof 3-13).
Owned paths: `tools/workflow/internal/compact/` (compact.go and tests), `tools/workflow/internal/store/rollup.go` and `rollup_test.go`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-17-compact-rebuilds-all-rollups.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-14, 3-15 (3-15 may add a rollup of its own).
Runs alongside: nothing.
Budget: 6 files to read, about 200 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/reports/3-14-fix-conversations-misses.md` (Concerns C1 and M4) and `reports/3-15-fix-facets-summary-scores-misses.md` (any rollup it added).
2. `tools/workflow/internal/store/rollup.go` — every `Rebuild*`/`backfill*` helper.
3. `tools/workflow/internal/compact/compact.go` — the deferred `RebuildHookRollup` call from 3-16.

## Goal

After `compact.Run`, every rollup table in the store (`hook_events_hourly`, `conversations_hourly`, and any 3-15 added) equals its base-row aggregate, and the conversations rollup is proven equal on bucketed, two-dimension and non-UTC queries.

## Contract

- Add `RebuildConversationRollup` (and one for any rollup 3-15 added) mirroring `RebuildHookRollup` (one transaction, delete then refill), and call every rebuild from compact's existing deferred step. Prefer one exported `RebuildRollups` that calls each, so the next rollup has a single place to register.
- Add the missing test: `Query` of `conversations` with `bucket` day and week, two dims, and `tz=Australia/Sydney` equals the same query with the rollup path forced off (or equals a hand-computed count over the fixture).

## Done evidence

- A compact test where compaction changes conversations presence (removal of a remove-listed event that was a conversation's only row, and a `model` fill), asserting every rollup equals its base aggregate both ways after `Run`, and after a resumed run.
- The bucket/two-dim/tz test passes.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store ./internal/compact ./internal/serve` passes, plus `go vet` and `gofmt -l`.

## Report back

Under 1,000 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output, any deviation and why, any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

Do not spawn agents beyond read-only research helpers.
