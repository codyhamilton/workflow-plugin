---
brief_id: 227
design_id: 209
---

# Brief: 5-03 — Spool default flip and drain retirement

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. 5-05 replays every shipped hook
config through the `spool.sh` this unit leaves.
Owned paths: `tools/hooklog/spool.sh`, `tools/hooklog/tests/test_spool_queue.py`,
`tools/hooklog/tests/test_hooklog.py`; deletions of `tools/hooklog/drain.py`,
`tools/hooklog/install-drain.sh`, `tools/hooklog/workflow-hooklog-drain.service`,
`tools/hooklog/workflow-hooklog-drain.timer`;
`docs/plans/09-workflow-binary/reports/5-03-spool-flip-retire.md` (new). Touch nothing else; in
particular not `tools/hooklog/hooklog.py` (a legacy library `tools/quality` imports), the hook
configs, `tools/hooklog/README.md`, `test_surfaces.py` or `test_artifact_submit_surfaces.py` (5-05
owns those; they fail between this commit and 5-05's, which is expected), or `tools/workflow/`.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing. The kick names `bin/workflow`, which 5-02 adds; the tests stub the kick.
Runs alongside: 5-01, 5-02, 5-04 (disjoint paths).
Budget: 7 files to read, about 250 lines changed including tests, 40 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 5 (grep `### Phase 5`) and its Units
   decisions.
2. `docs/design/02-edge-capture.md` — Spool (from line 28), macOS (line 118), Changes from what
   exists (line 206).
3. `docs/design/05-distribution.md` — Retired (lines 79-85).
4. `tools/hooklog/spool.sh` — whole file (101 lines).
5. `tools/hooklog/tests/test_spool_queue.py` (153 lines; `DRAIN` at line 14, `unknown-` at line
   66, the `WORKFLOW_BIN` tests from line 105) and `test_hooklog.py` (197 lines; `drain()` at
   lines 32-40, delivery tests at lines 78-127, `TestAutoHarness` at line 183).
6. `tools/workflow/cmd/workflow/drain_test.go` — grep `spool.sh` and `WORKFLOW_BIN`: how the Go
   tests call the script (they must keep passing).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, every hook writes to the design 2 queue and kicks `workflow drain` by
default, the legacy spool path and its Python drain are gone, and the hook side runs under bash 3.2
without `flock`.

## Contract

Cited, binding (design 2, macOS): "No flock(1). The hook-side probe falls back to a mkdir lock with
a PID check; the drain uses flock(2)". (Design 5, Retired): "The systemd drain timer and service,
and `install-drain.sh`. `tools/hooklog/drain.py`, once `workflow drain` replaces it." DESIGN.md
Phase 5 outcome: "no shipped config references … `--harness auto` …; `drain.py`, the systemd timer
and service are gone."

Decisions made at refine (settled):

- **The flip.** The queue path (today's `WORKFLOW_BIN`-set branch) becomes the only path: files to
  `${WORKFLOW_QUEUE:-$HOME/.local/share/workflow/queue}` with the design 2 name; a payload with no
  conversation id is dropped (no `unknown-` file). The legacy branch (`WORKFLOW_HOOKLOG_SPOOL`,
  `WORKFLOW_HOOKLOG_DIR`, `unknown-` naming, the `drain.py --daemon` kick) is deleted.
- **The kick target.** `$WORKFLOW_BIN drain` when `WORKFLOW_BIN` is set (development and the Go
  tests), else `bash "<root>/bin/workflow" drain` with root two levels above the script
  (`$(cd "$(dirname "$0")/../.." && pwd -P)`). Detached as today; never in the foreground.
- **Harness.** `--harness` is required to be one of the named harnesses; missing or `auto` → exit 0
  having spooled nothing (and Cursor still gets its permissive response). The `auto` detection code
  is deleted.
- **Kick lock.** With `flock` on `PATH` and `WORKFLOW_SPOOL_NOFLOCK` unset: today's `flock -n`
  probe. Otherwise the mkdir fallback on `<queue>/.kick.d`: `mkdir` succeeds → start the drain with
  `nohup … >/dev/null 2>&1 &`, write `$!` to `.kick.d/pid`; `mkdir` fails and `pid` names a live
  process (`kill -0`) → return; `pid` names a dead process → remove the directory and retake once;
  no `pid` file → return, unless the directory is older than one minute (`find … -maxdepth 0 -mmin
  +1`), then remove and retake once. `WORKFLOW_SPOOL_NOFLOCK=1` forces the fallback on Linux for
  tests. The drain's own lock is unchanged (flock(2) in Go).
- **bash 3.2.** Replace `read -r -N 65536` with `head -c 65536`; replace `EPOCHREALTIME` with `date
  +%s.%N`, falling back to `date +%s` when the result is not numeric (macOS prints `N`). No other
  bash 4 features. Checked statically; no bash 3.2 is available here.
- **Switches kept.** `WORKFLOW_HOOKLOG=off` and `WORKFLOW_HOOKLOG_KICK=0`.
- **Tests.** Delete tests whose only subject is `drain.py` delivery or `unknown-` naming (with
  their `DRAIN` helpers); keep and retarget spool-behaviour tests to the queue; keep the
  `hooklog.py` library tests (`TestAutoHarness` and friends) calling the library directly.

## Changes

`spool.sh` per the decisions. `test_spool_queue.py`: drop `DRAIN` and `test_no_id_is_unknown`,
retarget `test_fixture_payloads_named_by_id_and_drain` to assert the queue file names only, add the
tests below. `test_hooklog.py`: drop `drain()`/`DRAIN` and the delivery tests; keep what tests
`hooklog.py` functions or spool behaviour against the queue. Delete the four retired files.

### Keep untouched

The Cursor permissive responses at the end of `spool.sh` (byte-identical output), the file-name
sanitising and key preference, and `tools/hooklog/hooklog.py`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

Fail first: add the tests for the default path and the mkdir fallback first and quote their
failures.

- `python3 -m unittest discover -s tools/hooklog/tests -p 'test_spool_queue.py' -v` → passes, and
  `python3 -m unittest discover -s tools/hooklog/tests -p 'test_hooklog.py' -v` → passes; together
  covering:
  1. **default is the queue**: no `WORKFLOW_BIN`, `WORKFLOW_QUEUE` temp, `--harness claude` → one
     `<conversation>-…evt` file in the queue; nothing under a temp `WORKFLOW_HOOKLOG_DIR`.
  2. **no id dropped**: no file at all.
  3. **auto and missing harness**: nothing spooled, exit 0; Cursor's response unchanged.
  4. **default kick target**: with `WORKFLOW_BIN` unset and a temp copy of the repo's `tools/hooklog`
     and a stub `bin/workflow` beside it (records its args), one kick runs `drain`.
  5. **mkdir fallback**: `WORKFLOW_SPOOL_NOFLOCK=1`, a stub drain that sleeps 2 s → ten concurrent
     hooks start exactly one drain; a `.kick.d` with a dead pid is retaken; a `.kick.d` without a
     pid younger than a minute blocks the kick.
  6. **bash 3.2 lint**: grep of `spool.sh` for `read -r -N`, `read -N`, `EPOCHREALTIME`,
     `mapfile`, `,,}`, `[[ -v` finds nothing.
- `ls tools/hooklog/drain.py tools/hooklog/install-drain.sh tools/hooklog/workflow-hooklog-drain.*` → exits 2, every name missing.
- From `tools/workflow`: `PATH=$HOME/.local/go/bin:$PATH go test -count=1 ./...` → passes (the Go
  tests drive `spool.sh --harness <h>` with `WORKFLOW_BIN`).
- `grep -rln -E 'drain\.py|install-drain|workflow-hooklog-drain' tools/hooklog --include='*.sh' --include='*.py'` → only `tools/hooklog/tests/test_surfaces.py` and `test_artifact_submit_surfaces.py` (5-05's).

Live effect, record in the report: Cursor runs `hooks/cursor.json` → `spool.sh` from this checkout,
so on commit Cursor's events go to `~/.local/share/workflow/queue` and each kick starts
`bin/workflow drain`, which exits while no `client.toml` exists. Do not create `client.toml`, start
`serve` or kick a real drain to "check" this.

Safety: temp dirs only (`HOME`, `WORKFLOW_QUEUE`, `XDG_CACHE_HOME` temp in every child). Never touch
`~/.local/share/workflow*`, `~/.config/workflow`, `~/.cache/workflow`, `~/.config/systemd`, the live
queue or the legacy service; never run `systemctl` except `--user cat`/`status` reads.
`TYPESAFE_API_KEY=` blank in every child; never print it.

Commit: stage only your owned paths (use `git rm` for the deletions). Title `[exec
<execution_id>] Phase 5: spool default flip and drain retirement` (the orchestrator supplies the id;
if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/5-03-spool-flip-retire.md` (design 1, Execution report: what
was done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), listing each deleted test and why, and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
