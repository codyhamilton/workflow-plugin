# Brief: 3-01 — Login, status, and version

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/client/yakka.py`, `plugins/yakka/client/test_login.py`, `plugins/yakka/client/test_status.py`, `plugins/yakka/client/test_drain.py`, `docs/plans/16-python-local-client/reports/3-01-login-status-version.md`. Touch nothing else.
Commits: Commit to branch `cursor/python-local-client` when done evidence passes, with a plain-summary title. Do not push. Do not open or update a pull request.
Report: before committing, write `docs/plans/16-python-local-client/reports/3-01-login-status-version.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phase 1 (units 1-01 through 1-03) and Phase 2 (unit 2-01).
Runs alongside: 3-02, 3-03, 3-04.
Budget: 14 files to read, about 900 lines to change, 90 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Domain: Plugin client, **`login`.**, **`status`.**, **`version` / `--version`.** (lines 27-33); Assumption 8 (lines 116-121); Phase 3 Outcome (lines 198-199).
2. `packages/yakka/internal/login/login.go` — `Run`, `resolveEndpoint`, `devicePageURL`, `exchange`, `writeClientConfig`, `defaultOpenBrowser`.
3. `packages/yakka/internal/login/login_test.go` — port `TestMissingEndpoint`, `TestLoginExchangeWritesConfig`, `TestDevicePageURL`, `TestEndpointFromExistingConfig`.
4. `packages/yakka/cmd/yakka/login_test.go` — `TestLoginCommandMissingEndpoint` only (not `TestLoginDrainReadWriteAndReadOnly`).
5. `packages/yakka/internal/drain/cli.go` — `RunStatus` (lines 77-122).
6. `packages/yakka/cmd/yakka/drain_test.go` — `TestStatus` (lines 537-594) and the **status** half of `TestHalfSetEnvRefusal` (lines 506-522; drain half is already ported).
7. `packages/yakka/cmd/yakka/main.go` — `runLogin`, `version` / `--version` cases (lines 47-57, 63-78).
8. `plugins/yakka/client/yakka.py` — `Load`, `Path`, `ErrPartialEnv`, `QueueDir`, `QueueStatus`, `Running`, `main`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Implement `login`, `status`, and `version` / `--version` on the plugin Python client with parity locked by the ported Go tests named in Phase 3's outcome.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> **`login`.** Loopback `127.0.0.1:0/callback`. Device page is `https://yakka.build/device` when the collector host is `api.yakka.build`, otherwise `{collector}/device`. Then `POST {collector}/v1/device/exchange`, then the config file. No browser: the env pair, unchanged.

> **`login` writes `endpoint` and `key` at mode 0600.**

> **`status`.** The existing stdout lines (queue path, queued count, oldest age, rejected count, drain running or not, config mode, endpoint reachable or not) after `GET <endpoint>/v1/health`. Exit non-zero when the endpoint is unreachable and the queue is non-empty.

> **`version` / `--version`.** Stdout `yakka <version> <commit>\n`, exit 0. `<version>` is the text of `plugins/yakka/bin/VERSION`. `<commit>` is `YAKKA_COMMIT` when that is set, otherwise `unknown`.

> Exactly one set: `drain`, `mcp`, and `status` exit before any request and do not read the file.

> The lock is the ported Go client tests … `packages/yakka/internal/login`, `TestLoginCommandMissingEndpoint`, `TestStatus`, and the status half of `TestHalfSetEnvRefusal`. `TestLoginDrainReadWriteAndReadOnly` stays a Go test and still passes.

Strings the ported tests assert are part of the contract.

## Changes

Port `login.Run` into `yakka.py` (stdlib only): `--endpoint` flag via `argparse` or equivalent; `cmd_login` calls it. Reuse `Load`/`Path` only where the Go code does; login's missing-endpoint path does not use `Load` for the initial collector resolution (mirror `login.resolveEndpoint`).

Port `drain.RunStatus` into `cmd_status` using existing `QueueStatus`, `Running`, and `Load`. Match stdout line order and labels from `cli.go`. Health probe: `GET` with a short timeout; 2xx → `reachable`, else `unreachable`. Never print the bearer key.

`cmd_version`: read `plugins/yakka/bin/VERSION` relative to the plugin root (parent of `client/`); commit from `os.environ.get("YAKKA_COMMIT")` or `unknown`; print exactly one line `yakka %s %s\n` to stdout.

Register `login`, `status`, `version`, and `--version` in `main` (treat `--version` like Go: first arg).

`test_login.py` ports `login_test.go` cases listed above plus `TestLoginCommandMissingEndpoint` via subprocess on the script path.

`test_status.py` ports `TestStatus` and the status half of `TestHalfSetEnvRefusal` (subprocess `status` with half-set env; assert exit 1, no `127.0.0.1:8770` in output, message mentions `YAKKA_ENDPOINT`). Use httptest or `HTTPServer` for reachable/unreachable cases like the Go test.

Phase 2 carry: in `test_drain.py`, change `test_half_set_env_refusal_drain` so it does not bind a fixed `127.0.0.1:8770` listener (use an ephemeral port or skip the listener entirely and keep the assertion that drain makes no HTTP contact). Do not weaken drain refusal assertions.

### Keep untouched

Do not edit Go sources. Do not edit `plugins/yakka/bin/yakka`, hook configs, MCP JSON, design docs (3-04), or OpenCode prefetch (3-03). Do not change `drain` or `mcp` behavior beyond dispatch slots in `main`. Do not add third-party packages or `__init__.py`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- From the repo root, `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'` → exit 0.
- The same command with a 3.10 interpreter → exit 0. Record the 3.10 version in the report.
- From `packages/yakka`, `go test ./internal/login -count=1` → exit 0 (Go reference).
- From `packages/yakka`, `go test ./cmd/yakka -run 'TestLoginCommandMissingEndpoint|TestStatus|TestHalfSetEnvRefusal' -count=1` → exit 0.
- `python3 plugins/yakka/client/yakka.py version` → stdout matches `yakka <VERSION> unknown\n` when `YAKKA_COMMIT` is unset (`<VERSION>` is the trimmed contents of `plugins/yakka/bin/VERSION`).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
