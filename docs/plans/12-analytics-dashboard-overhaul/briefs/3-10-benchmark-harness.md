# Brief: 3-10 — The env-gated benchmark over every route, preset and measure

Consumer: a Go worker (flash-tier); 3-11 runs it on the real compacted copy, and any maintainer can run it on any ledger.
Owned paths: `tools/workflow/internal/serve/analytics_bench_test.go` (new). It lives in `serve` rather than `store` because it drives HTTP routes and `store` cannot import `serve`; say so in the report. Touch nothing else. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-10-benchmark-harness.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-08, 3-09.
Runs alongside: nothing.
Budget: 5 files to read, about 300 lines to write, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads: **Performance bound** (binding) and the Phase 3 Outcome.
2. `tools/workflow/internal/serve/analytics_query.go` and `analytics_conversation.go` — the routes and parameters.
3. `tools/workflow/internal/serve/analytics_test.go` lines 1-120 — how a test builds a `Server` over a tenant dir and calls `Handler()`.
4. `tools/workflow/internal/store/store.go` lines 100-200 — `Open`, `Tenant.Dir`, what opening does to the files (migrate, WAL).
5. `tools/workflow/internal/compact/verify_test.go` — the env-gated style (`WORKFLOW_VERIFY_DIR`) this test mirrors.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A committed test that, given a tenant directory, times every route, preset and measure combination against 500 ms p95 and writes a table, without ever modifying the ledger it is pointed at.

## Contract

Design, cited: "A committed benchmark runs against a compacted copy of the local ledger. It covers every route, each preset (24h, 7d, 30d, 90d, all time), every measure with 0, 1 and 2 dimensions, and every bucket within the cap. Every case is under 500 ms p95. The benchmark is runnable against any ledger path."

Settled by this brief:
- `TestAnalyticsBench`, skipped unless env `WORKFLOW_BENCH_DIR` (a tenant directory containing `ledger.db`) is set. **Never mutate the source.** The test copies only `ledger.db` (and `ledger.db-wal`/`-shm` if present) into `t.TempDir()`, opens that copy as the tenant, and removes it at the end. It must not open `WORKFLOW_BENCH_DIR` itself (opening migrates and writes WAL files). It refuses a `WORKFLOW_BENCH_DIR` under `~/.local/share/workflow` unless `WORKFLOW_BENCH_ALLOW_LIVE=1` (the copy is still made; the guard is a reminder for 3-11, which never sets it).
- Env knobs: `WORKFLOW_BENCH_OUT` (path of the result table, default log only), `WORKFLOW_BENCH_RUNS` (timed runs per case, default 3, after one discarded warm-up), `WORKFLOW_BENCH_FILTER` (substring of a case name; only matching cases run, used by 3-12), `WORKFLOW_BENCH_P95_MS` (default 500).
- Windows: `to` is the copy's `max(ts)` (not now; the copy is old) and the presets are `24h`, `7d`, `30d`, `90d` back from it plus `all` (`all=1`). Cases:
  1. Every analytics route with each preset: `facets`, `summary`, `series` (metric `hook_events`, group `none`, bucket `day`), `scores` (kind `design`), `executions`, `conversations`, `explore`, `schema` (once), `conversation` for the three conversations with the most facts in the window (ids read from the copy).
  2. `query` for every measure from `GET /v1/analytics/schema` (read the matrix from the handler, do not hard-code): 0 dims, each single dim, each unordered pair of dims, all with `bucket=none`, for every preset.
  3. `query` with every bucket other than `none` that is within the 400 cap for the preset, for each measure with 0 dims and with its first dim.
- A case's time is wall time of `Handler().ServeHTTP` through to a fully read body, status must be 200 (a non-200 fails the case with the status). p95 of N runs by nearest rank (for N ≤ 20 this is the largest). The table has one line per case: `case`, `status`, `runs`, `p95_ms`, `rows`. The test fails listing every case over `WORKFLOW_BENCH_P95_MS`; it also logs the count of cases and the total elapsed.
- Counts and timings only in the output; never print a fact's content or id from the ledger (conversation ids in case names are replaced by `conv#1..3`).

## Done evidence

- Without the env var, `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/serve -run AnalyticsBench -v` shows the test skipped and `go test ./internal/serve` stays fast.
- A self-test `TestAnalyticsBenchSmoke` (not env-gated) builds a small synthetic tenant (a few hundred facts across harnesses, usage and artifact rows), sets the bench runner's inputs directly, and asserts: the case list contains every measure from `/schema` with 0, 1 and 2 dims; every route; five presets; every case returns 200; and a runner call with `WORKFLOW_BENCH_P95_MS=0` reports failures (the over-bound path works). It passes.
- A second self-test asserts the source `ledger.db` bytes and mtime are unchanged after a run on a tempdir fixture.
- `go vet ./internal/serve` and `gofmt -l internal/serve` print nothing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
