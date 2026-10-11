# Report: 2-06 — Verify the compacted copy against the Phase 2 outcome

Status: **done**

## What changed

- New `tools/workflow/internal/compact/verify_test.go`: `TestVerifyCopy`, one subtest per Phase 2 bullet (a)–(g). It skips unless `WORKFLOW_VERIFY_DIR` (tenant dir) and `WORKFLOW_VERIFY_PRE` (precounts path) are set, so `go test ./internal/compact/` stays green and fast.
- No production code changed.
- `/var/tmp/workflow-compact-copy/` left in place for Phase 3's benchmark (see Clean-up).

## Done evidence

Compaction (2-05, PID 4057490) finished; the log's final line is `after:` (success). Waited with the brief's bounded loop (2 checks: first still-running, second done). No other run touched the copy.

Command (pass, exit 0, 61.9 s):

    WORKFLOW_VERIFY_DIR=/var/tmp/workflow-compact-copy/data/local WORKFLOW_VERIFY_PRE=/var/tmp/workflow-compact-copy/precounts.txt go test ./internal/compact/ -run VerifyCopy -v -timeout 30m

Subtest results (counts only):

    --- PASS: TestVerifyCopy (61.82s)
        --- PASS: TestVerifyCopy/a_removed_events (0.22s)
        --- PASS: TestVerifyCopy/b_delta_rows (0.19s)
        --- PASS: TestVerifyCopy/c_no_payload (0.33s)
        --- PASS: TestVerifyCopy/d_archive_hashes (61.02s)
        --- PASS: TestVerifyCopy/e_serve_health (0.00s)
        --- PASS: TestVerifyCopy/f_facts_by_type (0.06s)
        --- PASS: TestVerifyCopy/g_meta (0.00s)
    ok  github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact  61.887s

    (a) removed opencode events remaining: 0
    (b) delta rows=14902 distinct=14902 want=14902
    (c) hook_event rows still carrying a payload: 0
    (d) archive files=5137 conversations=5136 distinct first-16-byte row hashes=9226198 want=9226198
    (e) GET /v1/health -> 200; health compaction="complete"
    (f) facts total=450510 want=450510; hook rows=448897 want=448897
        type artifact_version 1258; type commit 355; type hook_event 448897
    (g) meta compaction="complete"
    ledger.db bytes=295919616 (pre=11618521088); archive bytes=756356590

`go test ./internal/compact/` without the env vars passes (TestVerifyCopy skips); `gofmt` and `go vet` clean.

## Before and after (compact.log, counts and bytes only)

    before: rows=8695533 types=artifact_version:1258,commit:355,hook_event:8693920 ledger.db=12132405248 ledger.db-wal=0 archive=107092436
    after:  rows=450510 types=artifact_version:1258,commit:355,hook_event:448897 ledger.db=295919616 ledger.db-wal=0 archive=756356590 elapsed=12m52.556s

The `before:` line was emitted at the start of the resumed run (after 2-05 attempt 1 was SIGTERMed), so it is not the true pre-compaction state; its rows (8,695,533) and bytes (12,132,405,248) differ from `precounts.txt` (`facts_total=9,273,647`, `ledger_db_bytes=11,618,521,088`). The resumed run nonetheless ends exactly at the pre-compaction predictions (below).

## Verdict per Phase 2 outcome bullet

- Completes and reports before/after rows and bytes: PASS (log above).
- `facts` has no removed-event rows: PASS (a: 0).
- Exactly one row per distinct delta part key: PASS (b: 14,902 rows = 14,902 distinct = `delta_parts`; `delta_with_key == delta_total`, so no keyless deltas).
- No hook fact carries a payload: PASS (c: 0).
- Archive distinct `row_hash` = pre-compaction non-removed hook facts: PASS (d: 9,226,198 = `hook_total - removed_total`).
- File under 1.5 GB: PASS, advisory (282 MiB; see below).
- `/v1/health` no longer reports `compaction: required`: PASS (e: `"complete"`; g: meta `compaction=complete`).

The outcome's "interrupting compaction and rerunning it ends in the same state" is also incidentally confirmed: attempt 1 was interrupted and the resume ended at exactly the pre-compaction predictions.

## Open Question 3 — compacted size

- Final `ledger.db`: 295,919,616 B (282 MiB; WAL 0).
- `archive/`: 756,356,590 B (deduplicated `row_hash` read count 9,226,198; grew from 107,092,436 B because compaction archived surviving hooks that predated the archive feature).
- 1.5 GB estimate: held, with ~5.3x headroom. Advisory, per the brief.

## Departures from the brief

- None. The waiting loop, the read-only open, the subtest split and the evidence command all follow the brief. The brief says the copy is "about 12 GB"; after compaction it is ~1.0 GiB (`du -sb` = 1,071,480,543 B). That is a stale brief figure, not a departure.

## Known problems

- Unexplained byte mismatch: compact.log's `before:` ledger.db (12,132,405,248) does not equal the copy's pre-compaction size (`ledger_db_bytes` = 11,618,521,088), and is larger than it. The `before:` line comes from the resumed run, so it is not a valid pre-compaction figure; the discrepancy is not resolved here. The authoritative pre-compaction figures are in `precounts.txt`, and the after state matches them exactly.
- Informational: archive files=5,137 for conversations=5,136 — one conversation spans two UTC months.

## Unfinished work

- None for this brief. Phase 3's benchmark should run against the compacted copy.

## Clean-up

`/var/tmp/workflow-compact-copy/` (compacted tenant `data/local/`, binary, log, precounts) is left in place for Phase 3's benchmark, which runs against the compacted copy. Do not delete it.
