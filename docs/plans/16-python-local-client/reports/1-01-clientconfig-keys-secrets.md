# Execution report: 1-01 clientconfig, keys, secrets

**Status:** done

## What changed

- Added `plugins/yakka/client/yakka.py`: `clientconfig` (`Path`, `Load`, `Config`, `ErrPartialEnv`, `LocalEndpoint`), `keys` (`ContentHash`, `Canonical`, `RowHash`, `NormalizeRemote`, `RepoID`, `RepoPath`, `Kind`), `secrets` (`Scan`, `Redact`, `Patterns`, `Hit`), and `main`/`cmd_drain` stubs per brief.
- Ported Go tests to stdlib `unittest`: `test_clientconfig.py`, `test_keys.py`, `test_secrets.py` (with per-test env isolation for config tests and `git` cwd matching Go for `TestRepoDocsClean`).

## Done evidence

### Before (no client tree)

```
ImportError: Start directory is not importable: 'plugins/yakka/client'
```

(from `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'`)

### After

```
Ran 19 tests in 0.209s
OK
```

```
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/clientconfig	...
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/keys	...
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/secrets	...
```

```
$ python3 plugins/yakka/client/yakka.py drain
yakka drain: not implemented
exit 2

$ python3 plugins/yakka/client/yakka.py mcp
yakka: unknown command
exit 2
```

## Departures

None from the brief. `TestEnvAssignmentCorpus` walks `../../../docs/{plans,design}` from `plugins/yakka/client` (repo root), equivalent to Go’s four-level-up path from `internal/secrets`.

## Contradictions

None observed between this brief, `DESIGN.md`, and the cited Go tests.

## Problems

None known within done-evidence scope.

## Unfinished

Phase 3+ commands (`login`, `status`, `version`, fact build, HTTP, drain loop) remain for later units, as scoped.
