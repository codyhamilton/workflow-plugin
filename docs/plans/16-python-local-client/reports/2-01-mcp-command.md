# Execution report: 2-01 MCP command

**Status:** done with concerns

## What changed

- Ported `internal/mcp` stdio JSON-RPC shim into `plugins/yakka/client/yakka.py`: `McpOptions`, `Serve`, `cmd_mcp`, three tools, and `artifact_feedback` state machine; default `StartDrain` uses `YAKKA_BIN` or `python3` + script path + `drain`.
- Registered `mcp` in `main`; version from `plugins/yakka/bin/VERSION`.
- Fixed `Running()` to close the lock file on busy `flock` (Phase 1 carry).
- Added `plugins/yakka/client/test_mcp.py` porting `TestShim` from `mcp_test.go`.
- `test_drain.py`: call `server_close()` after `shutdown()` on fake HTTP servers (teardown only).

## Checks

**Before (no `mcp` implementation):**

```
$ python3 plugins/yakka/client/yakka.py mcp < /dev/null
yakka: unknown command
exit:2

$ python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'
Ran 42 tests in ~35s — OK
```

**After:**

```
$ python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'
Ran 43 tests in ~23s — OK

$ cd packages/yakka && go test ./internal/mcp -count=1
ok  	github.com/codyhamilton/yakka/packages/yakka/internal/mcp	~1.4s

$ python3 plugins/yakka/client/yakka.py mcp < /dev/null
exit:0
```

**Python 3.10 floor:** `python3.10` is not installed on this VM (`/usr/bin/python3` is 3.12 only). The 3.10 gate was not run here.

## Departures

None from the brief. Test client sends MCP notifications with `send()` (no read), matching Go’s `Fprintln` on `c.in` rather than `raw()`.

## Contradictions

None between the brief and cited `DESIGN.md` / Go shim contracts.

## Problems (out of scope)

- `test_half_set_env_refusal_drain` can fail with `Address already in use` on `127.0.0.1:8770` when another process holds that port; reruns succeeded when the port was free.
