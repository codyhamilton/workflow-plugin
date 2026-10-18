# Brief: 2-01 — MCP command

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/client/yakka.py`, `plugins/yakka/client/test_mcp.py`, `plugins/yakka/client/test_drain.py`, `docs/plans/16-python-local-client/reports/2-01-mcp-command.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/16-python-local-client/reports/2-01-mcp-command.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phase 1 (units 1-01 through 1-03).
Runs alongside: 2-02.
Budget: 12 files to read, about 1,600 lines to change, 80 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Domain: Plugin client, the **`mcp`.** bullet (line 30); Assumption 5 (lines 95-100), Assumption 7 (lines 110-114), Assumption 11 (lines 137-142).
2. `packages/yakka/internal/mcp/mcp.go` — `Options`, `defaults`, `startDrain`, `Serve`, `handle`, `toolList`, `listChecks`, `search`.
3. `packages/yakka/internal/mcp/feedback.go` — `feedback`, `matcher`, `fetch`, `get`, `badConfigText`, `reasons`.
4. `packages/yakka/internal/mcp/mcp_test.go` — `TestShim` and its subtests (the in-process `serve()` helper uses httptest, not `yakka serve`). Port this file's expectations; do not port `packages/yakka/cmd/yakka/advisory_outcome_test.go`.
5. `packages/yakka/cmd/yakka/main.go` — the `mcp` case (lines 53-91) for how `cmd_mcp` wires stdin/stdout and `Version`.
6. `plugins/yakka/client/yakka.py` — `Load`, `Path`, `ErrPartialEnv`, `QueueDir`, `Running`, `WritePaths`, `RepoPath`, `RepoID`, `ContentHash`, `Kind`, `main`. Phase 1 carried item: `Running()` (lines 1226-1241) must close the lock file when `flock` returns busy.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Make `python3 plugins/yakka/client/yakka.py mcp` the stdio MCP shim from design 4, with parity locked by the ported `internal/mcp` tests.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> **`mcp`.** Local stdio JSON-RPC, not a remote URL. Tools remain `artifact_feedback`, `list_checks`, `search_artifacts`. `artifact_feedback` resolves `path`, accepts only `docs/plans/<plan>/DESIGN.md`, `docs/plans/<plan>/briefs/<name>.md`, and `docs/plans/<plan>/reports/<name>.md`, hashes the raw file with SHA-256, computes `repo_id` (normalised git remote, else `root:` plus the root commit), scans `queue/` and `rejected/`, may start `drain` and wait, then joins `GET /v1/artifacts` and compares hashes. The drain it starts is the same rule as the hook: `YAKKA_BIN` when that is set and executable, otherwise `python3` on this program's own script path, with argument `drain`. It does not start `python3` with no script, and it does not use `sys.executable` as the client. States, in the order the Go shim decides them: `queued`, `rejected`, `bad config`, `not delivered`, `stale`, `delivered`. A delivered result includes the screen, the scores, and the baseline comparison from `GET /v1/baselines`. `list_checks` and `search_artifacts` stay GETs of `/v1/checks` and `/v1/search`. A down service is a tool result, not an MCP error. The lock is the ported Go `internal/mcp` tests. Their `serve()` helper is an in-process httptest, not `yakka serve`, and those tests are part of this port.

> Yes, for both the hook and the shim, one rule. Set and executable, that program is exec'd with `drain`. Unset, both start `python3 plugins/yakka/client/yakka.py drain`. Neither starts a bare `python3`, and the shim does not treat `sys.executable` as the client.

> Where design 4's prose and the Go shim differ, the ported tests win.

Half-set env (`YAKKA_ENDPOINT` / `YAKKA_KEY` exactly one set): `mcp` follows the same `Load` refusal as `drain` and `status` only where the Go shim calls `clientconfig.Load` during tool handling; the ported tests cover config via file and full env pair. Do not change `Load` semantics from 1-01.

## Changes

Port `Serve`, the JSON-RPC loop, the three tools, and `artifact_feedback` state machine from `internal/mcp` into `yakka.py` (stdlib only). Reuse existing `Load`, `QueueDir`, `Running`, `WritePaths`, `RepoPath`, `RepoID`, `ContentHash`, and `Kind`; do not reimplement fact building or drain delivery.

`Options` mirrors Go: injectable `QueueDir`, `Wait`, `StartDrain`, `Getwd`, and `HTTP` client for tests. Defaults: queue dir from `QueueDir()`, wait 1.5s, `Getwd` is `os.getcwd`, HTTP timeout 3s. Default `StartDrain` detaches a child with `start_new_session=True`: if `YAKKA_BIN` is set and executable, `exec` that with argument `drain`; else `python3` with `[absolute path of this script, "drain"]`. Never `sys.executable` alone and never bare `python3` without the script path.

`cmd_mcp`: no arguments; read `plugins/yakka/bin/VERSION` (relative to the plugin root: parent of `client/`) for `Options.Version`; run `Serve` on `sys.stdin`/`sys.stdout` until EOF. Register `mcp` in `main`; keep `drain` as today.

Fix Phase 1 carry: in `Running()`, when non-blocking `flock` raises `BlockingIOError`, close the lock file before returning `True`.

`test_mcp.py` ports `mcp_test.go`'s `TestShim` subtests using the same in-process `serve()` pattern (httptest stub, injected `StartDrain` counter, git temp repo). Write failing tests before implementing the shim. Strings the Go tests assert (`want` / `dontWant` substrings) are part of the contract.

In `test_drain.py`, close the fake `HTTPServer` after each test that starts one (Phase 1 carry: `ResourceWarning` on open socket). Change only teardown; do not weaken drain assertions.

### Keep untouched

Do not edit Go sources. Do not edit hook configs, MCP JSON/TOML examples, or design 4 (2-02). Do not implement `login`, `status`, or `version`. Do not edit other `test_*.py` modules except `test_drain.py` teardown as above. Do not add `__init__.py` or third-party packages.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- From the repo root, `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'` → exit 0.
- The same command with a 3.10 interpreter → exit 0. Record the 3.10 version in the report.
- From `packages/yakka`, `go test ./internal/mcp -count=1` → exit 0 (Go reference; not the plugin gate).
- `python3 plugins/yakka/client/yakka.py mcp` with stdin closed immediately → exit 0 (EOF ends `Serve`).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
