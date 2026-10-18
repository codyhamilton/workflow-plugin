# Brief: 3-02 — Plugin entry wrapper

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/bin/yakka`, `tools/release/test_release.py`, `docs/plans/16-python-local-client/reports/3-02-bin-yakka-wrapper.md`. Touch nothing else.
Commits: Commit to branch `cursor/python-local-client` when done evidence passes, with a plain-summary title. Do not push. Do not open or update a pull request.
Report: before committing, write `docs/plans/16-python-local-client/reports/3-02-bin-yakka-wrapper.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phase 1 and Phase 2 (Python `drain` and `mcp` already on the script path).
Runs alongside: 3-01, 3-03, 3-04.
Budget: 10 files to read, about 400 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Domain: Distribution (lines 48-52), Assumption 4 (lines 88-93), Assumption 9 (lines 123-128); Phase 3 Outcome (line 198).
2. `plugins/yakka/bin/yakka` — today's cache, download, and build path (entire file).
3. `docs/design/05-distribution.md` — Wrapper section (lines 29-51) as the behavior to replace.
4. `tools/release/test_release.py` — `WrapperTests` and `LINE` regex (lines 17-175).
5. `plugins/yakka/script/spool.sh` — `start_drain` default path (grep `yakka.py`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Make `plugins/yakka/bin/yakka` the thin dispatcher that execs the Python plugin client for the five plugin commands and refuses `serve` / `ledger` without download or build.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> Contract: the client is `plugins/yakka/client/yakka.py`. `plugins/yakka/bin/yakka` no longer resolves a cached binary, downloads a release asset, or builds with Go. It execs `python3` on that script for `drain`, `mcp`, `login`, `status`, and `version` / `--version`. `serve` and `ledger` through this entry exit non-zero and do not download; operators run the Go binary from `packages/yakka`. `tools/release/build.sh` still builds that collector binary.

> `YAKKA_BIN`, if set (development).

Assumption 4: wrapper stops downloading and building; `SHA256SUMS` stays a collector-release artifact, not a hook input.

Preserve bash 3.2 compatibility and the existing `YAKKA_ROOT` export pattern at the top of the wrapper.

## Changes

Replace the cache/download/build body of `plugins/yakka/bin/yakka` with:

1. If `YAKKA_BIN` is set and executable, `exec` it with all arguments (unchanged).
2. Otherwise resolve `CLIENT="$ROOT/client/yakka.py"` and dispatch:
   - First argument `drain`, `mcp`, `login`, `status`, `version`, or `--version` → `exec python3 "$CLIENT" …` with remaining args passed through (`--version` maps to the script the same way Go does).
   - First argument `serve` or `ledger` (including subcommands) → print a clear stderr message that the collector is the Go binary under `packages/yakka`, exit non-zero, no network and no `go build`.
   - Missing or unknown command → usage or `unknown command` on stderr, exit 2 (match today's UX where reasonable).

Do not read `SHA256SUMS`, `RELEASE_URL`, or the cache directory on any path.

Rewrite `tools/release/test_release.py` `WrapperTests` to match the new contract: drop tests that require download, cache hit, concurrent build, stale lock, checksum mismatch, and no-go fallback for `--version`. Keep or adapt `test_8_bash32_lint`, `test_10_yakka_bin`, and add checks that `bin/yakka drain`/`mcp`/`version` exec Python on the script (e.g. stub `python3` or `YAKKA_BIN`). `BuildTests.test_7_build_sh` stays and must still pass unchanged.

`tools/release/build.sh` is not edited in this unit; only confirm `BuildTests` still passes.

### Keep untouched

Do not edit `plugins/yakka/client/yakka.py` (3-01). Do not edit hook configs, `SHA256SUMS`, or `build.sh`. Do not remove committed `SHA256SUMS`; it remains for the collector release.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `bash -n plugins/yakka/bin/yakka` → exit 0.
- `python3 tools/release/test_release.py WrapperTests` → exit 0.
- `python3 tools/release/test_release.py BuildTests.test_7_build_sh` → exit 0 (may take several minutes; npm required).
- With `YAKKA_BIN` unset, `plugins/yakka/bin/yakka serve` → non-zero exit, stderr mentions Go/collector, no files created under `~/.cache/yakka` from this invocation.
- With `YAKKA_BIN` unset, `plugins/yakka/bin/yakka drain` starts the same entry as `python3 plugins/yakka/client/yakka.py drain` (observe process argv or a one-line smoke with a stub endpoint).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
