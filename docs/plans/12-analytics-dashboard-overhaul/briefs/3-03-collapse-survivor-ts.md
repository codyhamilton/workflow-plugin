# Brief: 3-03 — One survivor-ts rule for ingest and compaction

Consumer: a Go worker (flash-tier); the orchestrator (closes carried item 5).
Owned paths: `tools/workflow/internal/compact/compact.go` and `compact_test.go`. Do not touch `ingest/`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-03-collapse-survivor-ts.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-01, 3-02, 3-04.
Budget: 4 files to read, about 80 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — Carried item 5.
2. `tools/workflow/internal/ingest/policy.go` and the collapse branch of `ingest.go` lines 225-275 — a later part of an already-stored key returns `duplicate` and changes nothing, so the stored `ts` is the first-arriving part's.
3. `tools/workflow/internal/compact/compact.go` lines 195-300 — `minInto`, `survivors`, the `'h'` op (the survivor's `ts` is set to the minimum over the part).
4. `tools/workflow/internal/compact/compact_test.go` — grep `ts` and the out-of-order delta test.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Compaction and live ingest choose the same `ts` for a collapsed part, so a part's time bucket does not depend on whether it was collapsed live or in history.

## Contract

Carried item 5: "compaction uses the minimum over the part, ingest keeps the first-arriving part's `ts`; they differ when parts arrive out of order. Pick one rule."

Decision (made here, not by you): the rule is **first-arriving**. Ingest is deployed and its duplicate answer must stay `duplicate`, so it cannot lower the stored `ts`; compaction changes to match. The survivor of a collapse group is the row with the lowest `rowid`, which is arrival order in an append-only ledger, and the survivor keeps its own `ts` (no minimum is taken).

Settled by this brief:
- Remove the minimum-ts update; the survivor row keeps its original `ts`. Resumption must still yield identical facts to an uninterrupted run (the existing interrupt test must stay green).
- First confirm with one read that the survivor is already the lowest-rowid row (the code at the survivor-selection point). If it is not, make it so and say so in the report. If the survivor logic is entangled with the `ts` update such that more than 80 lines change, stop and report `needs context`.
- Do not re-run anything against `/var/tmp/workflow-compact-copy/` and never touch the live ledger.

## Done evidence

- New test in `compact_test.go`: three delta rows of one part arrive with `ts` 30, 10, 20 in that rowid order; after `Run` the single survivor has `ts` 30 (the first-arriving), and a second `Run` is a no-op. The report cites the ingest line numbers that show the same rule (no ingest test is required).
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/compact ./internal/ingest` passes, including the interrupted-resume test. `go vet ./internal/compact` and `gofmt -l internal/compact` print nothing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
