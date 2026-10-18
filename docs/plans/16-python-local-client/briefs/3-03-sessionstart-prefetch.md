# Brief: 3-03 — SessionStart prefetch removal

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/hooks/hooks.json`, `plugins/yakka/hooks/codex.json`, `plugins/yakka/hooks/cursor.json`, `plugins/yakka/script/prefetch-version.sh`, `packages/hooklog/cursor-hooks.example.json`, `packages/hooklog/tests/test_surfaces.py`, `packages/opencode-yakka-hooks/src/index.ts`, `packages/opencode-yakka-hooks/tests/test_hooks.mjs`, `docs/plans/16-python-local-client/reports/3-03-sessionstart-prefetch.md`. Touch nothing else.
Commits: Commit to branch `cursor/python-local-client` when done evidence passes, with a plain-summary title. Do not push. Do not open or update a pull request.
Report: before committing, write `docs/plans/16-python-local-client/reports/3-03-sessionstart-prefetch.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-01, 3-02, 3-04.
Budget: 12 files to read, about 200 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Domain: Distribution (SessionStart sentences, lines 48-52), Assumption 6 (lines 102-107); Phase 3 Outcome (line 198).
2. `plugins/yakka/hooks/hooks.json`, `codex.json`, `cursor.json` — `SessionStart` hook groups.
3. `plugins/yakka/script/prefetch-version.sh` — current prefetch command.
4. `packages/hooklog/cursor-hooks.example.json` — `sessionStart` hooks.
5. `packages/hooklog/tests/test_surfaces.py` — `is_prefetch`, `prefetch_seen`, stub `--version` assertion (lines 19-78).
6. `packages/opencode-yakka-hooks/src/index.ts` — load-time `spawnBin(["--version"])` (grep).
7. `packages/opencode-yakka-hooks/tests/test_hooks.mjs` — prefetch expectations (grep `--version`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Remove SessionStart and OpenCode load-time `version` prefetch so harnesses no longer warm a binary cache; gates in `test_surfaces.py` and `test_hooks.mjs` match.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> SessionStart no longer runs the client to fill a binary cache: the Claude and Codex SessionStart `--version` commands, Cursor's `prefetch-version.sh` kick, the Cursor example at `packages/hooklog/cursor-hooks.example.json`, and the OpenCode `--version` spawn go away. `version` remains a command a person can run.

> `packages/hooklog/tests/test_surfaces.py` no longer expects a prefetch or a `--version` stub call, and `packages/opencode-yakka-hooks/tests/test_hooks.mjs` no longer expects `--version` on load.

> The OpenCode drain kick stays.

Phase 3 Outcome: `prefetch_seen == 0`; Cursor example SessionStart is only the spool.

Assumption 6: after this change, those tests must not require prefetch.

## Changes

- `hooks.json` and `codex.json`: remove the second `SessionStart` hook that nohups `bin/yakka --version`; leave the spool hook only.
- `cursor.json`: remove the `prefetch-version.sh` hook entry; `sessionStart` should only run `./script/spool.sh --harness cursor --event sessionStart`.
- Delete `plugins/yakka/script/prefetch-version.sh` (no remaining references).
- `cursor-hooks.example.json`: remove the second `sessionStart` command that nohups `bin/yakka --version`.
- `test_surfaces.py`: expect `prefetch_seen == 0`; remove the `stub.calls` `--version` assertion block (lines 74-78). Keep capture smoke for all events.
- `index.ts`: remove the load-time `spawnBin(["--version"])` call; keep `kickDrain` / `["drain"]` behavior from Phase 1.
- `test_hooks.mjs`: update tests so load does not expect `--version`; keep drain kick tests including `YAKKA_BIN` unset spawning the Python drain path from Phase 1.

### Keep untouched

Do not edit `plugins/yakka/bin/yakka` (3-02), `yakka.py`, or design docs (3-04). Do not change spool write paths or MCP registrations. README churn is optional; not required for done evidence.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- From the repo root, `python3 -m unittest packages.hooklog.tests.test_surfaces` or `python3 packages/hooklog/tests/test_surfaces.py` → exit 0 (all tests).
- In `packages/opencode-yakka-hooks`, `node --experimental-strip-types --test tests/test_hooks.mjs` → exit 0.
- `grep -r prefetch-version plugins/yakka packages/hooklog` → no matches in hook commands (script file deleted).
- `python3 -m json.tool plugins/yakka/hooks/cursor.json` → exit 0; `sessionStart` has exactly one command and it references `spool.sh`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
