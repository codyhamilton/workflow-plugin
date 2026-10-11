# Brief: 5-13 — Speed up the slowest Overview and Usage requests

Consumer: a Go worker (flash-tier).
Owned paths: `tools/workflow/internal/store/query.go`, `tools/workflow/internal/store/usage.go`, `tools/workflow/internal/store/analytics.go`, `tools/workflow/internal/store/rollup.go` and their `_test.go` files; the serve files `tools/workflow/internal/serve/analytics.go` and `analytics_query.go` only if 5-12's ranking says the time is in the handler. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-13-api-slowest-cases.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-12.
Runs alongside: every site unit (disjoint: Go only; the site units never touch `tools/`).
Budget: 8 files to read, about 200 lines to change, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/reports/5-12-page-request-set-profile.md` — the ranked table. You work only on what it ranks, in its order.
2. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Performance bound" (p95 under 500 ms) and "Rollups are conditional" (a rollup must equal base rows, edge hours read from base rows).
3. `tools/workflow/internal/store/rollup.go` and `rollup_test.go` — how rollups are built, kept current and tested against base rows.
4. `tools/workflow/internal/store/query.go` — the read path for the ranked requests.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Cut the three slowest page requests (by 5-12's ranking) so the Overview and Usage request sets settle faster on the large ledger, without changing any response shape or count.

## Contract

Target: each of the three slowest requests at or below 70% of its 5-12 p50 on `/var/tmp/p4verify/data/local`, and none of the benchmark's 2,063 cases regresses past 500 ms p95. Allowed levers, in this order: a missing or non-covering index; reading an existing rollup for more of the window; a new hourly rollup only if 3-12's rules are met (equals base rows in a store test, built at open, kept current in `Append`'s transaction, rebuilt by `RebuildRollups`, and `compact` still passes). Response shapes, the schema matrix and counts do not change.

## Changes

Re-measure each fix with 5-12's gated test and put before and after p50 and max per fixed request in the report. If a fix needs a new rollup, add it to the one `RebuildRollups` registration point (3-17) and extend its equality test in both EXCEPT directions. Stop after three requests or the budget, whichever comes first; the rest are carried.

### Keep untouched

Response JSON shapes, `facts` columns, `Append` semantics (idempotent, one transaction), and the existing rollups' equality tests.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `go vet ./...`, `go test -count=1 ./...` in `tools/workflow` → pass.
- `WORKFLOW_BENCH_DIR=/var/tmp/p4verify/data/local go test ./internal/serve -run TestAnalyticsPageSet -v -count=1` → the three named requests are at or below 70% of their before p50 (before and after in the report).
- The 3-10 benchmark on the same copy (`TestAnalyticsBench`, command in `reports/3-13-phase-proof.md`) → no case over 500 ms p95. It takes about 20 minutes: start it in the background and read its summary; if it cannot finish inside your budget, report `over budget` with the partial result rather than skip it.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
