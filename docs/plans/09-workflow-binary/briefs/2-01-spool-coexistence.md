---
brief_id: 215
design_id: 209
---

# Brief: 2-01 — `spool.sh`: conversation-ID names and the `WORKFLOW_BIN` kick

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Units 2-03 and 2-04 run the
real `spool.sh` in their tests and rely on the behaviour fixed here; phase 5 later flips its
default.
Owned paths: `tools/hooklog/spool.sh`, `tools/hooklog/tests/test_spool_queue.py` (new),
`tools/hooklog/tests/test_hooklog.py` (only `env_for` and assertions about spool file names),
`docs/plans/09-workflow-binary/reports/2-01-spool-coexistence.md`. Touch nothing else.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing.
Runs alongside: 2-02 (disjoint paths).
Budget: 6 files to read, about 60 lines of bash changed and 200 lines of tests, 40 tool turns. Past
the budget, stop: write a handoff under this brief's name in
`docs/plans/09-workflow-binary/IMPLEMENTATION.md` (done, not done, what you learned), commit, and
report `over budget`.

## Live machine warning

Cursor's live hooks run `tools/hooklog/spool.sh` from this checkout. Every save of this file takes
effect immediately on the maintainer's machine. Therefore:

- Make the edit in one write, and run `bash -n tools/hooklog/spool.sh` straight after it. If it
  fails, fix it before anything else.
- The default path (no `WORKFLOW_BIN`) must keep spooling into the legacy spool directory and
  kicking `drain.py --daemon` exactly as now. Only the file name changes on that path.
- Never run `spool.sh` or `drain.py` against the live spool
  (`~/.local/share/workflow-plugin/hooklog/spool`), the live archive, or
  `~/.local/share/workflow*`. Every test sets `WORKFLOW_HOOKLOG_DIR` or `WORKFLOW_HOOKLOG_SPOOL`
  (legacy path) or `WORKFLOW_QUEUE` (Go path) to a `mktemp -d` / `tempfile` directory, and
  `WORKFLOW_HOOKLOG_KICK=0` unless the test is about the kick.
- Tests must not inherit a `WORKFLOW_BIN` or `WORKFLOW_QUEUE` from the worker's environment: remove
  both in `env_for` and in your new test's environment builder unless the test sets them.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Assumption 5 (Assumption Ledger) and Phase 2
   (lines 163-178).
2. `docs/design/02-edge-capture.md` — Shape (lines 14-27), Spool (lines 28-40), Drain **Start**
   (lines 48-52), and the **macOS** paragraph at the end of Drain. Binding.
3. `docs/design/01-event-model-and-ingest.md` — Decision 4 (line 149). Binding.
4. `tools/hooklog/spool.sh` — all of it (55 lines); what you change.
5. `tools/hooklog/drain.py` — `drain_once` and `daemon` (lines 77-199): it globs `*.evt` and sorts
   by name; confirm the new names are still picked up.
6. `tools/hooklog/tests/test_hooklog.py` — `env_for`, `spool`, and the tests that spool.
7. `tools/hooklog/tests/fixtures/artifact_writes.json` — 11 real-shaped payloads, one per harness
   write surface, each with its conversation ID.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

Make spooled files name their conversation, and let a hook kick the Go drain instead of
`drain.py`, only when `WORKFLOW_BIN` is set, so phase 2 can be tested end to end while the live
default path keeps feeding the legacy service.

## Contract

Cited, binding: design 2 Spool: "File name starts with the conversation ID:
`<conversation_id>-<ts>-<pid>-<rand>.evt`", "The hook extracts the ID with a bounded text match on
the payload; a payload without one is not spooled", "`spool.sh` stays bash and does no parsing and no
network", "Never snapshots a file and never fails: exit 0 always". Design 2 Shape: one queue per
user, "`$WORKFLOW_QUEUE`, default `~/.local/share/workflow/queue`, with `tmp/` and `rejected/` inside
it". Design 2 Drain Start: "After its rename, a hook probes the lock non-blocking. Held means a drain
is running and the hook returns. Free means it starts `setsid bin/workflow drain` in the
background." DESIGN.md Assumption 5: "phase 2 changes `spool.sh` file naming and adds a kick of the
Go drain only when `WORKFLOW_BIN` is set; otherwise it kicks `drain.py` as now."

Decisions made at refine (settled; 2-03 and 2-04 build against them):

- **Path selection.** `WORKFLOW_BIN` set and non-empty selects the Go path wholesale: queue dir is
  `${WORKFLOW_QUEUE:-$HOME/.local/share/workflow/queue}`. Otherwise the queue dir is the existing
  legacy expression, unchanged (`WORKFLOW_HOOKLOG_SPOOL`, else `WORKFLOW_HOOKLOG_DIR`/default store
  plus `/spool`).
- **Conversation ID extraction.** After the tmp write, read at most the first 64 KiB of the tmp file
  with a bash builtin (`read -r -N 65536 … < file`, or equivalent) and match with `[[ =~ ]]`; no
  extra process. Keys in this preference order, first one that matches wins: `"session_id"`,
  `"conversation_id"`, `"sessionID"` (the order `hooklog.normalize` and the Go drain use). The
  pattern allows whitespace around `:` and takes a string value of 1 to 128 characters with no `"`
  or `\`. In the file name, replace every character outside `[A-Za-z0-9._-]` with `_`. The drain
  reads the real ID from the payload, never from the name.
- **No ID.** Go path: delete the tmp file; nothing is spooled; no kick. Legacy path: spool it
  anyway under the prefix `unknown` (design 1 decision 4 applies once phase 5 flips the default;
  until then the legacy drain still receives ID-less events such as OpenCode bus events, as today,
  and its test `test_unparseable_spool_file_is_quarantined` keeps passing).
- **Name.** `<id>-<ts>-<pid>-<rand>.evt`, where `ts`, `pid` and `rand` are what the script uses
  now. The envelope line is unchanged: `{"ts":…,"harness":"…","event":"…"}` then the raw payload.
  `drain.py` globs `*.evt`, so it still picks the files up; order within a conversation is kept.
- **Go kick.** Only on the Go path, only if `[ -x "$WORKFLOW_BIN" ]`. Same probe as now: if
  `flock` exists and `$dir/.drain.lock` exists, `flock -n` it; held means return. Free (or no lock
  file yet) means start `WORKFLOW_QUEUE="$dir" setsid "$WORKFLOW_BIN" drain` detached, stdin from
  `/dev/null`, output to `/dev/null`. Without `setsid` on `PATH`, start it with `nohup` in the
  background instead. Without `flock(1)` (macOS), kick unconditionally: the drain's own `flock(2)`
  with a short wait is the singleton, and extra starts exit (design 2 Start accepts extra starts).
  The design's hook-side `mkdir` lock is not built in this phase; name it in your report.
- **Legacy kick** is unchanged, including `WORKFLOW_HOOKLOG_KICK=0` and `WORKFLOW_HOOKLOG=off`, which
  apply to both paths.
- `--harness auto` stays accepted (phase 5 removes it). The Cursor stdout responses and `exit 0`
  are unchanged.

## Changes

`spool.sh`: path selection, ID extraction, name, no-ID rule, Go kick, header comment updated to
describe both paths. New `tests/test_spool_queue.py` (unittest, stdlib only) covering the done
evidence. In `test_hooklog.py`, `env_for` drops `WORKFLOW_BIN` and `WORKFLOW_QUEUE`; adjust any
assertion that depended on the old name shape.

### Keep untouched

`drain.py`, `hooklog.py`, `install-drain.sh`, the systemd units and every hook config: the live
legacy path depends on them, and phase 5 owns their retirement. The tmp-then-rename write and the
`umask 077`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.
Record the full test run's result before you change anything, so a pre-existing failure is not
blamed on you.

- `bash -n tools/hooklog/spool.sh` → no output, exit 0.
- `python3 -m unittest tools/hooklog/tests/test_spool_queue.py -v` → passes, with tests that show:
  - Legacy path: each of the 11 payloads in `fixtures/artifact_writes.json` spools one file whose
    name starts with that payload's ID followed by `-`; a payload with no ID spools one file
    starting `unknown-`; `drain.py --once` (with `WORKFLOW_QUALITY_URL=` and a temp
    `WORKFLOW_HOOKLOG_DIR`) consumes them all and archives under the right session.
  - Go path (`WORKFLOW_BIN` set to a temp stub script that appends its arguments and
    `$WORKFLOW_QUEUE` to a log and exits): files land in `$WORKFLOW_QUEUE`, not the legacy dir;
    an ID-less payload leaves no file in the queue or `tmp/`; the stub is invoked with `drain` and
    the queue path; with `.drain.lock` held by a `flock` subprocess the stub is not invoked; with
    `WORKFLOW_HOOKLOG_KICK=0` it is not invoked.
  - A payload with `"session_id" : "a/b c"` gets the name prefix `a_b_c`.
  - 20 concurrent spools (Go path, kick off) leave 20 distinct `.evt` files and an empty `tmp/`.
  - Every run exits 0, and the Cursor `preToolUse` response is still `{"permission": "allow"}`.
- `python3 -m unittest discover -s tools/hooklog/tests` → same pass/fail set as before your change,
  plus your new tests.

Safety: temp dirs only, as in the warning above. Never print `TYPESAFE_API_KEY` or any key.

Commit: title `[exec <execution_id>] Phase 2: spool.sh conversation names and Go kick` (the
orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/2-01-spool-coexistence.md` (design 1, Execution report: what
was done against this brief, verifiably; departures and why; unfinished work; known problems;
nothing derivable) and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
