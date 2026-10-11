# Brief: 3-12 — Conditional: fix benchmark misses with indexes, then hourly rollups

Consumer: a Go worker (flash-tier); the orchestrator (closes Open Question 1 and the Phase 3 bound).
Owned paths: `tools/workflow/internal/store/store.go` (a new migration only, appended), `tools/workflow/internal/store/rollup.go` (new), `rollup_test.go` (new), `tools/workflow/internal/store/query.go` and `usage.go` (only the read paths for the missed measures). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-12-fix-misses-indexes-rollups.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-11.
Runs alongside: nothing.
Budget: 6 files to read, about 400 lines to change, 60 tool turns. If more than 3 measures missed, stop after the first and report `needs context` so the orchestrator splits the rest into one unit per measure. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads: **Rollups are conditional** (binding) and Open Question 1.
2. `docs/plans/12-analytics-dashboard-overhaul/reports/3-11-run-benchmark-on-copy.md` — the list of missed cases. **If it says no case missed, this unit does nothing: write the report `not needed`, commit it and stop.**
3. `tools/workflow/internal/store/store.go` lines 28-90 (migrations) and the `Append` path (grep `func (t *Tenant) Append`).
4. `tools/workflow/internal/store/query.go` and `usage.go` — the measures that missed.
5. `tools/workflow/internal/serve/analytics_bench_test.go` — `WORKFLOW_BENCH_FILTER`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Every case 3-11 listed is under 500 ms p95 on the compacted copy, with the smallest change that does it, indexes first and a rollup only if an index cannot.

## Contract

Design, cited: "Performance comes first from the slimmed ledger, the columns and the indexes. An hourly rollup table is added only for measures that miss the bound. If one is added, a store test asserts that rollup aggregates equal base-row aggregates over a fixture, and windows that are not hour-aligned read their edge hours from base rows."

Settled by this brief:
- Step 1, indexes: for each missed case, read its `EXPLAIN QUERY PLAN` (via a throwaway test), add the narrowest covering index as a new migration appended to `migrations` (never edit earlier ones), rerun the missed cases with `WORKFLOW_BENCH_FILTER` on the real copy exactly as 3-11 did (the benchmark copies the ledger, so the migration runs on the copy; check `df /var/tmp`).
- Step 2, only for cases still over: an hourly rollup table keyed `(hour, harness, repo_id, norm_event, tool, model, kind, source, conversation_id…)` limited to the dimensions the missed measures need, filled by the same migration from base rows and kept current in `Append` in the same transaction as the fact insert (a collapsed duplicate that inserts no row adds nothing). Reads use it for the whole-hour part of a window and the base table for the two edge partial hours.
- Out of scope: the measure's results must not change; keep all earlier tests green.

## Done evidence

- Rerun on the copy of the missed cases only: every one is under 500 ms p95 (paste the before and after lines).
- If a rollup was added: a store test asserts rollup aggregates equal base-row aggregates over a fixture, including a window that starts and ends mid-hour, and an `Append` of a duplicate leaves both equal.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store ./internal/serve ./internal/compact` passes, plus `go vet` and `gofmt -l`.
- A full unfiltered rerun is not required here; 3-13 does the final check.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
