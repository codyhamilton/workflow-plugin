# Execution report: 1-02 fact building

**Status:** done

## What changed

- Added `File`, `Output`, `Build`, and `WritePaths` to `plugins/yakka/client/yakka.py`, porting `packages/yakka/internal/facts/facts.go` (write surfaces, coalescing, commit catch-up, secret scrub on worktree and committed blobs, git without shell).
- Added `plugins/yakka/client/test_facts.py`, porting the Go `facts` tests and fixture paths under `packages/hooklog/tests/fixtures/`. `assertIngest` runs Go `ingest.Ingest` via a short-lived `z_python_ingest_bridge_test.go` in `internal/facts` during the test only (not committed); subprocess `go` env clears leaked `HOME`/`GOPATH` from 1-01 config tests.

## Done evidence

### Before (tests first, no `Build`)

```
ERROR: test_facts (unittest.loader._FailedTest.test_facts)
AttributeError: module 'yakka' has no attribute 'File'
Ran 20 tests in 0.211s
FAILED (errors=1)
```

### After

```
Ran 27 tests in 0.962s
OK
```

```
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/facts	0.249s
```

```
$ python3 plugins/yakka/client/yakka.py drain
yakka drain: not implemented
exit 2
```

## Departures

None from the brief. Ingest validation matches Go via the ephemeral bridge test file, not a permanent Go edit.

## Contradictions

None observed between this brief, `DESIGN.md`, design 1–2, and the Go `facts` tests.

## Problems

None known within done-evidence scope.

## Unfinished

HTTP delivery, `Run`, and `cmd_drain` implementation remain for later units (1-03+), as scoped.
