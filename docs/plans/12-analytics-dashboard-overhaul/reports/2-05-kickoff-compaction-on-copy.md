# Report: 2-05 — Start compaction on a copy of the local ledger

Status: **done**

## What changed

- Created `/var/tmp/workflow-compact-copy/` (mode 0700) and `.../data/local/`, and copied the live
  ledger with SQLite's online backup only: `sqlite3 "file:$HOME/.local/share/workflow/serve/local/ledger.db?mode=ro" ".backup /var/tmp/workflow-compact-copy/data/local/ledger.db"`. No `cp`; the live ledger was only read.
- Wrote `/var/tmp/workflow-compact-copy/precounts.txt` (nine `key=value` lines, brief's definitions).
- Built the binary: `go build -o /var/tmp/workflow-compact-copy/workflow ./cmd/workflow`.
- Started `workflow ledger compact --tenant-dir /var/tmp/workflow-compact-copy/data/local` detached and
  `nice -n 10`; the log is `compact.log` and the PID is in `compact.pid`. No repo source touched; no
  `serve`/`drain` run against the copy.

## Done evidence

Live ledger copied read-only with `.backup` (exit 0, 37 s); copy is 11,618,521,088 bytes.

`precounts.txt` (verbatim):

```
facts_total=9273647
hook_total=9272034
removed_total=45836
delta_total=8792203
delta_with_key=8792203
delta_parts=14902
expected_surviving_hook_rows=448897
expected_archive_hashes=9226198
ledger_db_bytes=11618521088
```

Two minutes after the (surviving) start, `kill -0 $(cat /var/tmp/workflow-compact-copy/compact.pid)`
succeeded. `compact.log` (counts only):

```
before: rows=8695533 types=artifact_version:1258,commit:355,hook_event:8693920 ledger.db=12132405248 ledger.db-wal=0 archive=107092436
space: need 7705 MiB, have 18322 MiB
compact: scanned=250000 removed=1691 collapsed=236731 archived=248309 elapsed=19.373s
compact: scanned=500000 removed=2901 collapsed=477176 archived=497099 elapsed=39.366s
compact: scanned=750000 removed=4657 collapsed=713629 archived=745343 elapsed=1m4.848s
compact: scanned=1000000 removed=5969 collapsed=953146 archived=994031 elapsed=1m28.198s
compact: scanned=1250000 removed=7231 collapsed=1193043 archived=1242769 elapsed=1m51.885s
```

Time estimate: from lines `scanned=250000 @19.373s` and `scanned=1250000 @111.885s`,
1,000,000 rows / 92.512 s = 10,809 rows/s ≈ 648,570 rows/min. Remaining to `facts_total=9,273,647`
(from 1,250,000) is ≈8.02 M rows → ≈12.4 min of scanning, plus VACUUM. Against `hook_total=9,272,034`
→ ≈14.3 min. (2-03 measured 30,103 rows/s on a synthetic all-`Keep` ledger; this copy is delta-dense,
matching 2-03's stated lower-real-rate caveat.)

Live ledger before and after: mtime `2026-10-11 10:57:26.838584364`, size 11,618,439,168 — identical.
No `serve` growth observed.

## Handoff for 2-06

- Tenant/copy dir: `/var/tmp/workflow-compact-copy/data/local`
- Binary: `/var/tmp/workflow-compact-copy/workflow`
- Log: `/var/tmp/workflow-compact-copy/compact.log`
- PID file: `/var/tmp/workflow-compact-copy/compact.pid` (PID **4057490**, in its own session — survives
  the orchestrator's tool timeouts)
- Precounts: `/var/tmp/workflow-compact-copy/precounts.txt`
- Finished check: `kill -0 $(cat /var/tmp/workflow-compact-copy/compact.pid)` — success means still
  running; once it exits, `tail -n 5 /var/tmp/workflow-compact-copy/compact.log` should show the
  `after:` line and exit 0.

## Deviations from the brief

1. The first launch used the brief's literal command (`nohup nice ... &`); the harness sent SIGTERM at
   its 120 s tool timeout and the process interrupted cleanly (`interrupted; rerun the same command to
   resume`). Relaunched with `setsid --fork` so the process survives the tool's process-group signals.
   The resumed run is equivalent — compaction is resumable by design (2-03/2-04). Not silence-worthy;
   the brief's exact start command is not survivable under this tool wrapper.
2. The brief says "the five or six `precounts.txt` lines"; its own key list has nine, and nine were
   written and are quoted above. Treated as brief-internal wording, not a contract conflict.
3. `compact.log` existed from attempt 1 and was overwritten on relaunch.

## Contradiction between the brief and the contracts it cites

None found. The `ts` collapse-vs-ingest contradiction 2-03 flagged is not exercised here (this unit
only counts). `expected_archive_hashes = hook_total − removed_total` matches DESIGN Phase 2's
"distinct archive `row_hash` count equals the pre-compaction count of non-removed hook facts."

## Known problems

- Attempt 1's SIGTERM left the copy partially compacted; the current run resumed from `compact_cursor`
  on that same copy. The counts above were taken with no run in flight, so they are the true
  pre-compaction counts.
- None other.
