# Brief: 1-04 — Hook kick and design 2

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/script/spool.sh`, `plugins/yakka/script/test_kick.py`, `packages/opencode-yakka-hooks/src/index.ts`, `packages/opencode-yakka-hooks/tests/test_hooks.mjs`, `docs/design/02-edge-capture.md`, `docs/plans/16-python-local-client/reports/1-04-hook-kick.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push.
Report: before committing, write `docs/plans/16-python-local-client/reports/1-04-hook-kick.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 1-01, 1-02, 1-03.
Budget: 8 files to read, about 150 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Domain: Hook spool (lines 36-40), Assumption 5 (lines 95-100), Assumption 10 (lines 130-135), and the OpenCode sentences in Architectural Implications (line 59). Phase 1's Outcome (line 168) names this unit's evidence.
2. `plugins/yakka/script/spool.sh` — the header kick comment (lines 11-14) and `start_drain` (lines 58-66). The write path and `kick` stay.
3. `packages/opencode-yakka-hooks/src/index.ts` — `spawnBin` (lines 42-53), `kickDrain` (lines 58-64), and the load-time `spawnBin(["--version"])` (line 172).
4. `packages/opencode-yakka-hooks/tests/test_hooks.mjs` — `sandbox` (lines 18-37) and the kick test at line 139.
5. `docs/design/02-edge-capture.md` — the drain identity sentence (lines 43-45), **Start.** (lines 48-49), and **Changes from what exists** (lines 225-229).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

With `YAKKA_BIN` unset, the hook and the OpenCode drain kick start the Python drain and do not download or build, and design 2 names that process.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> Contract: the write path is unchanged (envelope line, raw payload, tmp-then-rename, conversation id required, exit 0). After a successful spool, unless `YAKKA_HOOKLOG_KICK=0`, it starts one detached drain. `YAKKA_BIN` set and executable: that program, with `drain`, as today. `YAKKA_BIN` unset: `python3 plugins/yakka/client/yakka.py drain`. No cache lookup, no download, no `go build` on this path. The flock probe (and the mkdir lock where `flock(1)` is absent) is unchanged, so the kick still returns without waiting for delivery.

> Yes, for both the hook and the shim, one rule. Set and executable, that program is exec'd with `drain`. Unset, both start `python3 plugins/yakka/client/yakka.py drain`. Neither starts a bare `python3`, and the shim does not treat `sys.executable` as the client. No download and no build on the unset path.

The shim's half of that rule is Phase 2. This unit is the hook and the OpenCode drain kick only.

> The OpenCode plugin kicks `plugins/yakka/bin/yakka drain` and a version prefetch. The kick moves with the hook. The prefetch goes away with SessionStart.

SessionStart and the OpenCode `--version` spawn go away in Phase 3. This unit does not remove them.

> `spool.sh` stays the hook. It still only writes the queue. It starts the Python drain instead of a downloaded or locally built binary, and drops that fallback on this path.

Design 2 today says the opposite of the contract, and those sentences are what this unit rewrites:

> `yakka drain`, part of the `yakka` binary ([design 3](03-remote-service.md#runtime)).

> Free means it starts `setsid plugins/yakka/bin/yakka drain` in the background.

> The drain is rewritten as `yakka drain` in Go (design 3); `drain.py` is removed once it lands.

After the edit, design 2 describes this drain: the plugin drain is `python3 plugins/yakka/client/yakka.py drain`, and `yakka serve` still hosts the Go drain. They exclude each other with the same `.drain.lock` flock. The delivery table, fact building, spool write path, and MCP section stay as written.

## Changes

`start_drain` in `plugins/yakka/script/spool.sh`: when `YAKKA_BIN` is set, keep `nohup "$YAKKA_BIN" drain`. When it is unset, `nohup python3 "$root/client/yakka.py" drain`, with `root` the plugin directory the script already computes (`dirname` of the script, parent). Not `bash "$root/bin/yakka"`. Not a bare `python3` with no script. Update the kick comment at lines 11-12 to that rule. Leave the write path, `kick`'s flock and mkdir lock, the cursor JSON replies, and `exit 0`.

`spawnBin` in `packages/opencode-yakka-hooks/src/index.ts`: when `YAKKA_BIN` is set, keep `spawn(bin, args)`. When it is unset and the argument list is `["drain"]`, `spawn("python3", [path.join(repoRoot(), "plugins/yakka/client/yakka.py"), "drain"])`. When it is unset and the arguments are anything else, keep today's `spawn("bash", [path.join(repoRoot(), "plugins/yakka/bin/yakka"), ...args])`, so the load-time `["--version"]` prefetch stays on the wrapper until Phase 3. Do not delete line 172. Update the comment that says `` `bin/yakka drain` ingests it `` so it names the Python drain.

Write the failing checks first. They must not need `plugins/yakka/client/yakka.py` to exist or to implement `drain`: put a fake `python3` on `PATH` that records its arguments and exits. The real script path is an argument, not a file the test runs.

`plugins/yakka/script/test_kick.py` (stdlib `unittest`):

- `YAKKA_BIN` unset, `YAKKA_HOOKLOG_KICK` not `0`, a payload with a conversation id: the detached command is `python3`, the script argument is `plugins/yakka/client/yakka.py` under the plugin root, and the next argument is `drain`. The recorded command is not `bin/yakka`, `go build`, or a download.
- `YAKKA_BIN` set to an executable stub: that stub is exec'd with `drain`, and `python3` is not.
- `YAKKA_BIN` set to a path that is not executable: no drain is started.
- `YAKKA_HOOKLOG_KICK=0`: no drain is started.
- The spool file is still one envelope line `{"ts","harness","event"}` plus the raw payload, named with the conversation id, and the script exits 0.
- `docs/design/02-edge-capture.md` contains the text `python3 plugins/yakka/client/yakka.py drain`, does not contain `setsid plugins/yakka/bin/yakka drain`, and its **Changes from what exists** section names `plugins/yakka/client/yakka.py` and still says `yakka serve` hosts the Go drain behind `.drain.lock`.

Add one case to `packages/opencode-yakka-hooks/tests/test_hooks.mjs`: with `YAKKA_BIN` unset, a drain kick's spawn is `python3` plus `plugins/yakka/client/yakka.py` and `drain`. Leave the existing `YAKKA_BIN` stub assertions, including `--version` on load, as they are.

### Keep untouched

`packages/hooklog/spool.sh` is a different file and not a Phase 1 surface. Do not edit it. Do not edit `plugins/yakka/bin/yakka`, hook JSON, `prefetch-version.sh`, or `plugins/yakka/client/`. Do not remove the `--version` prefetch. Do not change design 2's delivery table, **Building facts**, **Write surfaces**, or **MCP shim**.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `python3 -m unittest discover -s plugins/yakka/script -p 'test_kick.py'` → exit 0.
- `bash -n plugins/yakka/script/spool.sh` → exit 0, no output.
- From `packages/opencode-yakka-hooks`, `node --experimental-strip-types --test tests/test_hooks.mjs` → exit 0, including the existing prefetch assertion and the new unset-`YAKKA_BIN` drain assertion.
- The design assertions inside `test_kick.py` are the check that design 2 describes this drain.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
