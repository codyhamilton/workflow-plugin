# Brief: 5-12 — Profile the page request sets on the large ledger

Consumer: a Go worker (flash-tier).
Owned paths: new `tools/workflow/internal/serve/analytics_pageset_test.go`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-12-page-request-set-profile.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-01 to 5-11, 5-14 to 5-16 (it owns one new Go test file; no site path).
Budget: 5 files to read, about 150 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — "Phase 3 verification", "Carried" items 1 and 2 (Phase 3) and "Carried (Phase 4)" item 1.
2. `tools/workflow/internal/serve/analytics_bench_test.go` — how `TestAnalyticsBench` copies only `ledger.db` from `WORKFLOW_BENCH_DIR` to a temp dir, opens it, and times requests (reuse its helpers `do`, harness constructor and percentile code; do not edit the file).
3. `packages/workflow-analytics/src/routes/+page.svelte` and `src/routes/usage/+page.svelte` — the exact request sets (paths and params) Overview and Usage send for the 7d, 30d, 90d and All time presets (All time on `/query` is `all=1`; on other routes a 399-day window).
4. `tools/workflow/internal/store/analytics.go` and `query.go` — only the entry points of the slowest calls, for the EXPLAIN.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A committed, env-gated test that times exactly what the Overview and Usage pages request on each preset against the large ledger, and ranks the slowest calls with their query plans, so 5-13 fixes measured cases, not guesses.

## Contract

Target ledger: `WORKFLOW_BENCH_DIR=/var/tmp/p4verify/data/local` (the purged compacted copy, 318 MB; the test copies `ledger.db` to a temp dir and never writes the source, as 3-10 does). Phase 4 found the slowest API call per page at 0.45 to 0.62 s against a 500 ms budget.

The test is skipped unless `WORKFLOW_BENCH_DIR` is set. When set it runs each page's request set (all requests of one page load, issued with the site's concurrency of 4, repeated 5 times per preset, first run discarded) and writes `TestAnalyticsPageSet`'s results as `t.Logf` lines and, when `WORKFLOW_PAGESET_OUT` names a file, as JSON: per request the path, params, p50 and max latency, and for the slowest 8 distinct requests the `EXPLAIN QUERY PLAN` rows.

## Changes

Include also a non-gated smoke test on the small fixture ledger the bench helpers already build, asserting the request list is non-empty and every request returns 200, so the file cannot rot. Run the gated test once on the large copy and put the ranked table (request, p50, max, plan summary) in your report; name the three slowest requests and, for each, whether the time is in the query, the rollup read or the base-row edge hours (use the plan). Do not fix anything here.

### Keep untouched

`analytics_bench_test.go` and every non-test file.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `go vet ./...` and `go test ./internal/serve` (in `tools/workflow`) → pass (the gated test skips).
- `WORKFLOW_BENCH_DIR=/var/tmp/p4verify/data/local go test ./internal/serve -run TestAnalyticsPageSet -v -count=1` → completes in under 10 minutes and the report holds the ranked table of the slowest requests.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
