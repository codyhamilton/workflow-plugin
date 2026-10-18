---
cursor:
  subagentId: "bc-81addf24-d245-516f-b466-5717cf06c6c7"
---

# Execution report: 3-01 login, status, version

**Status:** `done with concerns`

## What changed

- `plugins/yakka/client/yakka.py`: `run_login` / `cmd_login` (loopback callback, device page, exchange, config write 0600), `run_status` / `cmd_status`, `cmd_version`, `main` dispatch for `login`, `status`, `version`, `--version`.
- `plugins/yakka/client/test_login.py`: ports `TestMissingEndpoint`, `TestLoginExchangeWritesConfig`, `TestDevicePageURL`, `TestEndpointFromExistingConfig`, `TestLoginCommandMissingEndpoint`.
- `plugins/yakka/client/test_status.py`: ports `TestStatus` and status half of `TestHalfSetEnvRefusal`.
- `plugins/yakka/client/test_drain.py`: `test_half_set_env_refusal_drain` no longer binds `127.0.0.1:8770`.

## Done evidence

**Before (pre-implementation):**

```
$ python3 plugins/yakka/client/yakka.py version
yakka: unknown command
exit:2
```

**After:**

```
$ python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'
Ran 50 tests in ~24s — OK

$ cd packages/yakka && go test ./internal/login -count=1
ok

$ go test ./cmd/yakka -run 'TestLoginCommandMissingEndpoint|TestStatus|TestHalfSetEnvRefusal' -count=1
ok

$ python3 plugins/yakka/client/yakka.py version
yakka 0.2.0 unknown
```

**Python 3.10 floor:** `python3.10` is not installed on this VM (`/usr/bin` has `python3` → 3.12 only; `apt-get install python3.10` failed: permission denied). Suite was not run under 3.10 here.

## Deviations

- Committed on branch `work/3-01` per orchestrator assignment, not `cursor/python-local-client` named in the brief’s Commits line.

## Contradictions

- Brief **Commits** says branch `cursor/python-local-client`; orchestrator assigned `work/3-01` and forbade checking out `cursor/python-local-client`. Followed orchestrator.

## Unfinished / known problems

- Re-run `python3.10 -m unittest discover …` when a 3.10 interpreter is available (design floor).
- Login unit test may emit `ResourceWarning` for an unclosed callback socket on 3.12; tests still pass.

## Turns / context

Not reported by harness.
