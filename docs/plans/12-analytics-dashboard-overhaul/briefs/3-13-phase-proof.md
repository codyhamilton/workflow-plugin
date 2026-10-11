# Brief: 3-13 — Phase 3 outcome check: benchmark, routes, cost fixture and the existing Playwright suite

Consumer: a shell and Go worker (flash-tier) producing the evidence that closes Phase 3; the orchestrator reads its report.
Owned paths: `docs/plans/12-analytics-dashboard-overhaul/reports/3-13-phase-proof.md` only. No source changes; if something fails, report it, do not fix it. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-13-phase-proof.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-03, 3-11, 3-12, 3-14, 3-15 and 3-16 (3-11 found 243 misses, so the fix units ran).
Runs alongside: nothing.
Budget: 4 files to read, no code, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Phase 3 Outcome (binding, every bullet).
2. `docs/plans/12-analytics-dashboard-overhaul/reports/3-11-run-benchmark-on-copy.md` and, if present, `3-12-fix-misses-indexes-rollups.md`.
3. `packages/workflow-analytics/playwright.config.ts` and `tests/e2e/global-setup.ts` lines 1-20 — how the suite builds the binary and starts serve.
4. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — the `## Phase 3` section (units, carried placement).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Each bullet of the Phase 3 Outcome is checked once, with the command and the number, on the final code.

## Contract

Settled by this brief:
- Bullet 1 (benchmark): rerun the full benchmark on the compacted copy exactly as in 3-11, after the last Phase 3 code unit, so the result reflects the final code. Detach and poll as in 3-11. Every case under 500 ms p95 or the unit reports `blocked` naming the cases.
- Bullet 2 (`schema`, 400 on unsupported pairing) and bullet 3 (`ignored_filters` for a `kind` filter on `hook_events`): run the named Go tests from 3-06 and quote their pass lines.
- Bullet 4 (cost): run the 3-05 usage fixture test and quote the hand-computed value and the pass line; state that the Codex fixture charges fresh input only.
- Bullet 5 (Playwright): `cd packages/workflow-analytics && npm run test:e2e`. It builds the binary and bundle itself. If a browser is not installed, run `npx playwright install chromium` once; if that fails, report `blocked`. Pass count, fail count, and the names of any failures; a failure that expects the old count semantics is reported with the spec and line, not edited.
- Bullet 6 (Go tests for `query`, `conversation`, keyset past page one, `tz` of a sub-day fixture, top-N): `go test ./internal/store ./internal/serve ./internal/ingest ./internal/compact ./internal/archive` plus `go build ./...` and `go vet ./...`; map each named behaviour to its test name in a table.
- Carried items 1 to 5: for each, one line naming the test or code that closes it.
- Counts and timings only.

## Done evidence

- The report has a table: outcome bullet, command, result number, pass or fail. Every row passes, or the status is `blocked` or `done with concerns` naming the row.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go build ./... && go vet ./... && go test ./...` all exit 0 (quote the final lines).
- `cd packages/workflow-analytics && npm run test:e2e` exit code and the summary line quoted.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
