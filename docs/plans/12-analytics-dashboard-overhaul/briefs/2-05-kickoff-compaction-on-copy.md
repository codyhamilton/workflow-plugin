# Brief: 2-05 — Start compaction on a copy of the local ledger

Consumer: a shell-capable worker (flash-tier). It starts a long-running process and hands off; unit 2-06 verifies the result. It does not wait for the compaction to finish.
Owned paths: `/var/tmp/workflow-compact-copy/` (outside the repo; create it), and the report file below. Touch no repo source and never touch `~/.local/share/workflow/` except to read it through `sqlite3 .backup`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/2-05-kickoff-compaction-on-copy.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 2-04.
Runs alongside: nothing.
Budget: 3 files to read, no source changes, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Phase 2 Outcome (binding) and Open Question 3.
2. `docs/plans/12-analytics-dashboard-overhaul/reports/2-04-ledger-compact-command.md` — the command's flags and output.
3. `docs/plans/12-analytics-dashboard-overhaul/reports/2-03-compact-engine.md` — the throughput figure, for the time estimate.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A consistent copy of the local ledger exists with its pre-compaction counts recorded, and the compaction is running on it in the background, with enough written down for a fresh worker to verify it.

## Contract

Phase 2 Outcome: "`workflow ledger compact` is run against a copy of the local ledger." The live ledger is `~/.local/share/workflow/serve/local/ledger.db` (about 11.6 GB; a `serve` may be running against it). It must stay unmodified: copy it with SQLite's online backup, never `cp`, and never run `workflow serve` or `workflow drain` against the copy (hosted drain would read the user's real queue into it).

Settled by this brief:
- Layout, mode 0700: `/var/tmp/workflow-compact-copy/data/local/ledger.db` is the copy (the tenant dir is `.../data/local`). The disk holding `/var/tmp` had about 30 GB free on 2026-10-11 and `/home` had 8.9 GB, so use `/var/tmp` only. Check `df -h /var/tmp` first; if under 20 GB free, stop and report `blocked`.
- Copy: `sqlite3 "file:$HOME/.local/share/workflow/serve/local/ledger.db?mode=ro" ".backup /var/tmp/workflow-compact-copy/data/local/ledger.db"`. Do not copy `blobs/`, `pending/` or `legacy/`; the compaction does not need them.
- Pre-compaction counts, written to `/var/tmp/workflow-compact-copy/precounts.txt` as `key=value` lines and quoted (counts only) in the report. Run them on the copy with `sqlite3 -readonly`, one query each: `facts_total`; `hook_total` (`type='hook_event'`); `removed_total` (hook rows with `harness='opencode'` and `event` in `experimental.chat.system.transform`, `chat.params`, `chat.headers`, `shell.env`); `delta_total` (`event='message.part.delta'`); `delta_with_key` (those whose `json_extract(raw,'$.payload.event.properties.messageID')`, `.partID` and `.field` are all non-empty); `delta_parts` (distinct `conversation_id, messageID, partID, field` among `delta_with_key`); `expected_surviving_hook_rows` = `hook_total - removed_total - (delta_with_key - delta_parts)`; `expected_archive_hashes` = `hook_total - removed_total`; `ledger_db_bytes`. Queries over 7.6M rows take a minute or more each; run them with `timeout 1200`.
- Binary: `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go build -o /var/tmp/workflow-compact-copy/workflow ./cmd/workflow`.
- Start, detached and low priority: `nohup nice -n 10 /var/tmp/workflow-compact-copy/workflow ledger compact --tenant-dir /var/tmp/workflow-compact-copy/data/local > /var/tmp/workflow-compact-copy/compact.log 2>&1 &`, recording the PID in `/var/tmp/workflow-compact-copy/compact.pid`.
- Never put row content, payloads, header values or environment values in the report or any repo file. The log contains counts only; if you see anything else in it, stop the process and report `blocked`.

## Done evidence

- The five or six `precounts.txt` lines exist and the report quotes them.
- Two minutes after the start, `kill -0 $(cat .../compact.pid)` succeeds and `compact.log` shows the before-counts line, the free-space line and at least one progress line (or the process has already exited 0, in which case say so and give the after-counts line). Paste those log lines in the report (counts only).
- A time estimate for completion (rows scanned per minute from two progress lines, against `hook_total`).
- The live ledger's mtime and size are the same before and after your work, apart from normal growth by a running serve (state which you observed).
- The report ends with the handoff block for 2-06: exact paths, the PID, the command that shows whether it finished (`kill -0`, `tail -n 5 compact.log`), and the `precounts.txt` path.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here. If the compaction process fails to start or exits non-zero, report `blocked` with the exit code and the last five log lines.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
