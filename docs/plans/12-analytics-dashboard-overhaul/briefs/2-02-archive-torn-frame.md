# Brief: 2-02 — Archive tolerates and repairs a torn last frame

Consumer: a Go worker (flash-tier) hardening the archive package that compaction (2-03) writes and reads.
Owned paths: `tools/workflow/internal/archive/archive.go`, `tools/workflow/internal/archive/archive_test.go`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/2-02-archive-torn-frame.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 2-01.
Budget: 3 files to read, about 150 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Event archive" (Layout, Delivery, Read access).
2. `tools/workflow/internal/archive/archive.go` — whole file (193 lines): `Append` writes one complete zstd frame per file per call and fsyncs; `Read` and `readFile` decode the concatenated frames.
3. `tools/workflow/internal/archive/archive_test.go` — existing helpers and tests, so new tests match their style.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A crash in the middle of an archive write must not make a conversation unreadable or make a compaction rerun fail. `Read` returns every complete line that survives, and a repair step restores the file so later appends are readable.

## Contract

DESIGN "Event archive": "Archiving is at-least-once ... readers deduplicate by `row_hash`." Phase 1's report 1-01 recorded the limit this unit removes: "a crash mid-write can leave a torn last frame, which makes `Read` error for that conversation instead of skipping it." Phase 2 Outcome: "Interrupting compaction and rerunning it ends in the same state."

Settled by this brief:
- A torn frame is a trailing partial zstd frame or a trailing partial JSON line, produced by a crash during `Append`. The on-disk format does not change (still concatenated zstd frames of JSON lines).
- `Read` returns all lines decoded before the damage and no error when the damage is a torn tail. Damage that is not at the tail (a complete JSON line that does not parse, corruption followed by good data) is still an error naming the file.
- New `Repair(tenantDir string) (Repaired, error)`, where `Repaired` reports the count of files it fixed and the count of lines dropped. For every file under `<tenantDir>/archive/*/` it decodes line by line; if the file ends in a torn tail it rewrites the file atomically (write a temp file in the same directory, fsync, rename over) as one fresh zstd frame holding exactly the good lines, in their original order, duplicates kept. A healthy file is not touched (mtime unchanged). Repair takes the package mutex.
- `Append` does not call `Repair` (it would decode every file on every call). The residual risk, an append that lands after a torn tail inside the same file, is for the report to state; `Repair` before compaction is how it is handled.

### Keep untouched

File naming, `Entry` and `Line` shapes, HTML escaping off, `Append`'s one-frame-per-file-per-call behaviour and fsync.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- A test that appends two entries, truncates the file by a few bytes (a torn frame), and asserts `Read` currently errors, then (after the change) returns the lines of the first complete frame with no error.
- A test where a second `Append` was written after a torn tail: `Read` returns the lines before the tear without error, `Repair` rewrites the file, and a `Read` afterwards returns the good lines of both frames that decode, in order. State in the test comment which lines of the post-tear frame are recoverable and which are not, matching what your implementation does.
- A test that `Repair` leaves a healthy file byte-identical and mtime-identical, and that after `Repair` a further `Append` and `Read` return old plus new lines.
- A test that mid-file corruption still returns an error from `Read`.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test -race ./internal/archive/ && go vet ./internal/archive/` → pass; paste the summary line.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
