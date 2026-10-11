# Brief: 3-11 — Run the benchmark on the compacted real copy and decide rollups

Consumer: a shell and Go worker (flash-tier) producing the evidence that answers Open Question 1; the orchestrator decides 3-12 from its report.
Owned paths: `docs/plans/12-analytics-dashboard-overhaul/reports/3-11-run-benchmark-on-copy.md` (the report, which carries the full result table). No source changes. `/var/tmp/workflow-compact-copy/` is read only (the benchmark copies `ledger.db` out of it); never touch `~/.local/share/workflow`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-11-run-benchmark-on-copy.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-10.
Runs alongside: nothing.
Budget: 3 files to read, no code, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Open Question 1 and the Performance bound.
2. `tools/workflow/internal/serve/analytics_bench_test.go` (3-10) — the env knobs and output format.
3. `docs/plans/12-analytics-dashboard-overhaul/reports/2-06-verify-compacted-copy.md` — the copy's path, size and state.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The benchmark has been run on the compacted real ledger copy and every case over 500 ms p95 is named, so rollups are built only for what misses.

## Contract

Settled by this brief:
- Check the copy first: `/var/tmp/workflow-compact-copy/data/local/ledger.db` exists; `sqlite3 -readonly ... "select count(*) from facts"` is about 450,510. If it is gone, report `blocked`; do not recompact.
- Run, from `tools/workflow`: `WORKFLOW_BENCH_DIR=/var/tmp/workflow-compact-copy/data/local WORKFLOW_BENCH_OUT=/var/tmp/workflow-compact-copy/bench-3-11.txt PATH=$HOME/.local/go/bin:$PATH go test ./internal/serve -run 'TestAnalyticsBench$' -v -timeout 40m`. Start it detached (`setsid`, log to `/var/tmp/workflow-compact-copy/bench-3-11.log`) and poll with bounded `until` loops of at most 280 s per call. The local disk has little free space: the benchmark copies a ~300 MB file; check `df /var/tmp` first (need 1 GiB free).
- If the run has not finished after about 40 minutes, stop, leave the log, and report `needs context` with the progress line and the cases done so far.
- Record in the report: the number of cases, total elapsed, the table of every case over 500 ms p95 (case name, p95 ms), and the worst ten cases overall. Also record the unpriced share with a read-only `sqlite3 -readonly` count on the copy: usage rows (`norm_event='usage'`) in total, and those with `cost_reported IS NULL` whose `model` (after stripping any `provider/` prefix) is not a key in `tools/transcript/pricing.json`; counts only. (Design note for the orchestrator: that table holds 7 Cursor models, so most local calls are expected to be unpriced.)
- Verdict, stated plainly: **No misses** (Open Question 1 answered "no rollup; 3-12 is not run") or **Misses** (list the measures, dimensions, buckets and presets; 3-12 runs).
- Counts and timings only; no fact content.

## Done evidence

- `/var/tmp/workflow-compact-copy/bench-3-11.txt` exists and has one line per case; the report quotes its case count, its worst ten lines and the list over 500 ms (or states none).
- The live ledger is untouched: `stat` of `~/.local/share/workflow` files before and after is unchanged in the report (mtime of `ledger.db` there, one line).
- `go test ./internal/serve` without env vars still passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
