# Brief: 1-01 — Client config, keys, and secrets

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/client/yakka.py`, `plugins/yakka/client/test_clientconfig.py`, `plugins/yakka/client/test_keys.py`, `plugins/yakka/client/test_secrets.py`, `docs/plans/16-python-local-client/reports/1-01-clientconfig-keys-secrets.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push.
Report: before committing, write `docs/plans/16-python-local-client/reports/1-01-clientconfig-keys-secrets.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 1-04.
Budget: 12 files to read, about 900 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Domain: Plugin client, the Contract bullets **Config.** and **Python floor.** (lines 25-28), and Assumption 7 (lines 110-114).
2. `packages/yakka/internal/clientconfig/clientconfig.go` and `clientconfig_test.go` — the resolution and the tests to port.
3. `packages/yakka/internal/keys/keys.go` and `keys_test.go` — the tests to port.
4. `packages/yakka/internal/secrets/secrets.go` and `secrets_test.go` — the tests to port.
5. `docs/design/01-event-model-and-ingest.md` — Keys (lines 28-48). Binding for what the key functions mean; the Go tests win where a string is asserted.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Port client config, key derivation, and the client scrub into the one Python program so a later unit can build facts and post them without re-deciding resolution.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> **Config.** Unchanged resolution. Both `YAKKA_ENDPOINT` and `YAKKA_KEY` set: those values, over the file. Exactly one set: `drain`, `mcp`, and `status` exit before any request and do not read the file. Neither set and `~/.config/yakka/client.toml` present (`YAKKA_CLIENT_CONFIG` overrides the path): `endpoint` and `key` from that file. Neither set and no file: `http://127.0.0.1:8770` with no bearer. The file format stays `name = "string"` lines, `#` and blanks skipped, unknown keys ignored. `login` writes `endpoint` and `key` at mode 0600.

> **Python floor.** 3.10. The program runs on Linux and macOS. Windows is out of scope.

> Port the existing Go client tests to stdlib `unittest`, run with `python3 -m unittest`. … Where design 4's prose and the Go shim differ, the ported tests win.

`login`'s write is Phase 3. This unit only loads config. The Go error text this load returns, which Phase 1's drain half prints, is:

```go
var ErrPartialEnv = errors.New("clientconfig: YAKKA_ENDPOINT and YAKKA_KEY must both be set or both unset")
```

Strings the ported tests assert are part of the contract. No third-party packages, including no TOML library and no third-party test runner.

## Changes

One script, `plugins/yakka/client/yakka.py`, importable as `yakka` when `plugins/yakka/client` is the unittest top-level. Do not add `__init__.py` or any other module. Python 3.10 syntax and the standard library only: no `tomllib`, and nothing that requires 3.11 or newer.

Port these Go names as Python callables of the same names, with the same fields the Go tests read (`Endpoint`, `Key`, `Local`, `Mode()`): `Path`, `Load`, `ErrPartialEnv`, `ContentHash`, `Canonical`, `RowHash`, `NormalizeRemote`, `RepoID`, `RepoPath`, `Kind`, `Scan`, `Redact`, `Patterns`. `Load` returns the config or raises `ErrPartialEnv` (or the malformed-file error the Go tests assert: the text contains `line 2`, `missing key`, or `missing endpoint`, and never the key or the bad line's value).

`ErrPartialEnv`'s message is the Go string above, so it contains `YAKKA_ENDPOINT` and does not contain the key.

Command dispatch, so later units extend one entry: `main(argv)` reads `argv[1]`. `drain` calls `cmd_drain`, which prints `yakka drain: not implemented` to stderr and returns 2. Any other command, including `mcp`, `login`, `status`, `version`, and `--version`, prints `yakka: unknown command` to stderr and returns 2. `if __name__ == "__main__"` exits with `main(sys.argv)`.

Tests, each porting the named Go functions and their asserted strings, and importing `yakka`:

- `test_clientconfig.py` — `TestLoad`, `TestMissingFile`, `TestDefaultPath`, `TestEnvOverridesFile`, `TestEnvRemoteNoFile`, `TestPartialEnv`, `TestMalformed`.
- `test_keys.py` — `TestNormalizeRemote`, `TestCanonicalRowHash`, `TestKind`, `TestRepoID`, `TestRepoPath`.
- `test_secrets.py` — `TestScanPatterns`, `TestScanLinesAndOrder`, `TestPlaceholdersDoNotHit`, `TestRepoDocsClean`, `TestEnvAssignmentProse`, `TestEnvAssignmentPositives`, `TestEnvAssignmentCorpus`.

Identify or write those failing tests before changing the port. `TestRepoDocsClean` reads this repo the way the Go test does; do not copy the tree into a fixture.

### Keep untouched

The Go packages stay, unmodified: `serve` still hosts the Go drain. Do not implement fact building, HTTP, the drain loop, `mcp`, `login`, `status`, or `version`. Do not write `client.toml` (Phase 3 `login`). Do not edit `plugins/yakka/script/spool.sh`, `docs/design/02-edge-capture.md`, or `packages/opencode-yakka-hooks`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- From the repo root, `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'` → exit 0. This interpreter may be newer than 3.10; do not use syntax it accepts and 3.10 rejects.
- From `packages/yakka`, `go test ./internal/clientconfig ./internal/keys ./internal/secrets -count=1` → exit 0. The Go tests are still the hosted client's.
- `python3 plugins/yakka/client/yakka.py drain` → exit 2, stderr `yakka drain: not implemented`.
- `python3 plugins/yakka/client/yakka.py mcp` → exit 2, stderr contains `unknown command`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
