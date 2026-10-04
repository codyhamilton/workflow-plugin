---
brief_id: 228
design_id: 209
---

# Brief: 5-04 — OpenCode plugin on the queue

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. 5-05's write-surface replay runs
this plugin's OpenCode fixtures against a temp `serve`.
Owned paths: `packages/opencode-workflow-hooks/src/index.ts`,
`packages/opencode-workflow-hooks/tests/test_hooks.mjs`,
`packages/opencode-workflow-hooks/README.md`,
`packages/opencode-workflow-hooks/opencode.json.example` (only if it references a retired path),
`docs/plans/09-workflow-binary/reports/5-04-opencode-plugin.md` (new). Touch nothing else; not the
`python/` soft-signal helpers, not `tools/`.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing. The kick names `bin/workflow`, which 5-02 adds; the tests stub it.
Runs alongside: 5-01, 5-02, 5-03 (disjoint paths).
Budget: 6 files to read, about 200 lines changed including tests, 35 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 5 (grep `### Phase 5`) and its Units
   decisions.
2. `docs/design/02-edge-capture.md` — Spool (from line 28: the file name, the queue directory, the
   envelope) and Per-harness install (line 191).
3. `docs/design/05-distribution.md` — Per-harness configs (lines 68-77) and the SessionStart
   prefetch (lines 43-46).
4. `tools/hooklog/spool.sh` — the queue branch: the envelope fields and the name format (grep
   `WORKFLOW_QUEUE`).
5. `packages/opencode-workflow-hooks/src/index.ts` — whole file (246 lines): `spoolDir`,
   `recordHooklog`, `submitArtifact`, `runPythonHook` and the `tool.execute.after` handler.
6. `packages/opencode-workflow-hooks/tests/test_hooks.mjs` — the `drain.py --once` helper (line 15)
   and how the plugin is loaded.
7. `packages/opencode-workflow-hooks/README.md` — lines 60-80 (the retired names).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, the OpenCode plugin writes the same queue files as `spool.sh --harness
opencode` would, kicks `bin/workflow drain`, warms the binary cache at load, and no longer calls
`artifact_submit.py`.

## Contract

Cited, binding (design 5, Per-harness configs): OpenCode "writes spool files with the design 2
name; kicks `bin/workflow drain`"; "All four drop the `artifact_submit.py` registration." (Wrapper):
"every harness's `SessionStart` hook also runs `bin/workflow --version` detached". DESIGN.md Phase
5 outcome: "replaying the write fixtures through each shipped hook config into a temp `serve`
produces an `artifact_version`".

Decisions made at refine (settled):

- **Queue file.** Directory `${WORKFLOW_QUEUE:-$HOME/.local/share/workflow/queue}` (created 0700).
  Name and envelope exactly as `spool.sh`'s queue branch writes them (conversation id sanitised the
  same way, `-<ts>-<pid>-<rand>.evt`, written to a temp name then renamed), with `harness:
  "opencode"`, the event name, and the payload. The conversation id is the event's `sessionID`; a
  record with none is dropped. The legacy `spoolDir()` (`WORKFLOW_HOOKLOG_SPOOL`/`DIR`) and its
  `${ts}-${pid}-${seq}.evt` name go.
- **Kick.** After a write, spawn `WORKFLOW_BIN drain` if set, else `bash <root>/bin/workflow drain`
  (root resolved from the package location, three levels up from `src/`), `detached: true`,
  `stdio: "ignore"`, `unref()`; at most once per 10 s per process; `WORKFLOW_HOOKLOG_KICK=0`
  disables it.
- **Prefetch.** At plugin load, spawn `bash <root>/bin/workflow --version` the same detached way,
  once, unless `WORKFLOW_HOOKLOG_KICK=0`. Never awaited.
- **Removed.** `submitArtifact`, `runPythonHook`'s artifact path and every
  `WORKFLOW_ARTIFACT_SUBMIT_CLI` and `artifact_submit.py` reference, in code and README. The batch
  flush soft signals (`python/batch_flush_cli.py`) stay.
- **Errors never reach OpenCode.** Every write and spawn is wrapped; a failure is swallowed.

## Changes

`src/index.ts` per the decisions. `tests/test_hooks.mjs`: drop `drain.py --once`; assert queue
files. README: the queue, the kick and `WORKFLOW_QUEUE`/`WORKFLOW_BIN`, without the retired names.

### Keep untouched

The events the plugin listens to and the payload it records for each, and the soft-signal flush.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

Fail first: rewrite the test's assertions to the queue first and quote the failure.

- `node --experimental-strip-types --test tests/test_hooks.mjs` (from the package) → passes, covering:
  1. a `tool.execute.after` write with a `sessionID` → one queue file whose name starts with the
     sanitised id and whose envelope has `harness: "opencode"` and the payload;
  2. the same file name shape as `spool.sh` produces for the same id (run `bash
     ../../tools/hooklog/spool.sh --harness opencode` with `WORKFLOW_HOOKLOG_KICK=0` into a second
     temp queue and compare the prefix and the envelope keys);
  3. no `sessionID` → no file;
  4. kick: `WORKFLOW_BIN` a stub script that appends its args to a temp file → `drain` recorded,
     and two writes within 10 s record one kick;
  5. prefetch: loading the plugin with the stub records `--version`;
  6. no `artifact_submit` spawn under any event.
- `grep -rn --exclude-dir=node_modules -E 'artifact_submit|WORKFLOW_ARTIFACT_SUBMIT_CLI|drain\.py|WORKFLOW_HOOKLOG_SPOOL' packages/opencode-workflow-hooks` → no output.

Safety: temp dirs only (`HOME`, `WORKFLOW_QUEUE`, `XDG_CACHE_HOME` temp; `WORKFLOW_BIN` a stub in
every test, so no real binary is built or run). Never touch `~/.local/share/workflow*`,
`~/.config/workflow`, `~/.cache/workflow` or the live queue. `TYPESAFE_API_KEY=` blank in every
child; never print it.

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 5: OpenCode plugin on the
queue` (the orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/5-04-opencode-plugin.md` (design 1, Execution report: what
was done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
