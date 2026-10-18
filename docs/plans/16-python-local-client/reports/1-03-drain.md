# Execution report: 1-03 drain command

**Status:** done

## What changed

- Ported `packages/yakka/internal/drain` into `plugins/yakka/client/yakka.py`: `Run`, `Options` (including `afterRelease`), `HTTPSink`, `ConfigSink`, `QueueDir`, `EnsureDirs`, `Running`, `QueueStatus`, exit reasons, and `RunStandalone` wired through `cmd_drain`.
- Added `plugins/yakka/client/test_drain.py`, porting all `internal/drain` tests except `TestHostedRetriesLockAndWakes`, plus the drain half of `TestHalfSetEnvRefusal` (loopback `127.0.0.1:8770`, half-set env, Python script invocation).

## Done evidence

### Before (tests first, stub `cmd_drain`)

```
AttributeError: module 'yakka' has no attribute 'Options'
FAILED (errors=1)
```

```
$ python3 plugins/yakka/client/yakka.py drain
yakka drain: not implemented
exit 2
```

### After

```
$ python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'
Ran 42 tests in 12.405s
OK
```

```
$ python3.10 --version
Python 3.10.22

$ python3.10 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'
Ran 42 tests in 12.536s
OK
```

(Python 3.10 installed from deadsnakes PPA on the VM; not committed.)

```
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/clientconfig	...
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/keys	...
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/secrets	...
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/facts	...
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/drain	...
```

```
ok  	github.com/codyhamilton/yakka/packages/yakka/cmd/yakka	56.727s
```
(filtered `-run` list from the brief)

## Departures

None from the brief.

## Contradictions

None observed between this brief, `DESIGN.md`, design 2 delivery table, and the ported Go drain tests.

## Problems

None known within done-evidence scope.

## Unfinished

`status`, `mcp`, `login`, and `version` remain Phase 1 follow-on units. Hosted drain (`TestHostedRetriesLockAndWakes`) stays Go-only by design.
