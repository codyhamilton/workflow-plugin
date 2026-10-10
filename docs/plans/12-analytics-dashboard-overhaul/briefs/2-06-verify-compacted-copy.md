# Brief: 2-06 — Verify the compacted copy against the Phase 2 outcome

Consumer: a Go and shell worker (flash-tier) producing the evidence that closes Phase 2; the orchestrator reads its report.
Owned paths: `tools/workflow/internal/compact/verify_test.go` (new), and `/var/tmp/workflow-compact-copy/` (read only, except the verify output file). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned repo path and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/2-06-verify-compacted-copy.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 2-05.
Runs alongside: nothing.
Budget: 5 files to read, about 150 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Phase 2 Outcome (binding) and Open Question 3.
2. `docs/plans/12-analytics-dashboard-overhaul/reports/2-05-kickoff-compaction-on-copy.md` — the handoff block: paths, PID, `precounts.txt`.
3. `tools/workflow/internal/archive/archive.go` — `Read`, `Line`, file layout (reading signatures is enough; you will stream files, not call `Read` per conversation).
4. `tools/workflow/internal/serve/serve.go` — `New`, `Handler`, `Config`, and how `health` computes `compaction` (2-01).
5. `tools/workflow/internal/ingest/policy.go` — `CollapseHash` is not needed here; read it only to see which events are `Remove`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The compacted copy is checked, with committed and re-runnable code, against every bullet of the Phase 2 outcome, and the real file size is recorded for Open Question 3.

## Contract

Phase 2 Outcome, cited: "It completes and reports before and after rows and bytes. `facts` has no removed-event rows. It has exactly one row per distinct delta part key. No hook fact carries a payload. The archive's distinct `row_hash` count equals the pre-compaction count of non-removed hook facts ... The file is under 1.5 GB ... `/v1/health` no longer reports `compaction: required`." The size is advisory (Open Question 3); every other bullet is a gate.

Settled by this brief:
- First wait for the compaction. `kill -0 $(cat /var/tmp/workflow-compact-copy/compact.pid)`; while it runs, sleep up to 5 minutes per check (foreground `sleep` is blocked in some harnesses; use a bounded `until` loop with a 280 s timeout per call) and note progress. If it has not finished after about 15 checks, stop and report `needs context` with the last progress line. If it exited non-zero, report `blocked` with the exit state and the last five log lines (counts only).
- `verify_test.go`: `TestVerifyCopy`, skipped unless env `WORKFLOW_VERIFY_DIR` (the tenant dir) is set. It reads `precounts.txt` from env `WORKFLOW_VERIFY_PRE` (path). It opens the database read-only (`mode=ro`, no migration) and asserts: (a) zero rows for the four removed OpenCode events; (b) the number of `message.part.delta` rows equals `delta_parts` plus `delta_total - delta_with_key` from the counts file (keyless deltas stay as keep rows), and no two rows share a collapse key (every delta row's `row_hash` is unique by the primary key; assert the count identity); (c) zero rows where `instr(raw,'"payload"') > 0` among `hook_event` rows; (d) the number of distinct `row_hash` values over every `archive/*/*.jsonl.zst` line, counted by streaming the files with the archive's decoding (use a `map[[16]byte]struct{}` keyed on the first 16 bytes of the hex-decoded hash to bound memory), equals `expected_archive_hashes`; (e) `serve.New` on a `Config` whose `Data` is the parent of the tenant dir, handler only (never call `Host`), returns `/v1/health` JSON with `"compaction":"complete"` for GET `/v1/health` (follow how the existing serve tests build a local-mode config); (f) the facts count by type matches `facts_total` minus the deleted removed rows and collapsed deltas; (g) the `compaction` meta value is `complete`. It logs counts and sizes only.
- Also record: the final `ledger.db` size in bytes, the `archive/` size, and elapsed compaction time from the log. State whether the 1.5 GB estimate held (advisory).
- If an assertion fails, do not fix code; report `done with concerns` or `blocked` with the numbers (counts only) and the likely cause.
- Counts only in the report. No row content, payload, header or path of any individual fact.

## Done evidence

- `cd tools/workflow && WORKFLOW_VERIFY_DIR=/var/tmp/workflow-compact-copy/data/local WORKFLOW_VERIFY_PRE=/var/tmp/workflow-compact-copy/precounts.txt PATH=$HOME/.local/go/bin:$PATH go test ./internal/compact/ -run VerifyCopy -v -timeout 30m` → pass, each of (a) to (g) logged as its own subtest line. Without the env vars the test skips (`go test ./internal/compact/` stays green and fast).
- The report lists before and after rows and bytes from `compact.log`, the final file size against 1.5 GB, and the verdict per outcome bullet.
- A clean-up note: `/var/tmp/workflow-compact-copy/` is about 12 GB; the report says it was left in place for Phase 3's benchmark (which runs against the compacted copy) and gives its path. Do not delete it.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
