---
cursor:
  subagentId: "bc-6036ec88-b910-5827-8e9c-444f1d4e61a2"
---

# Report: 3-04 — workflow login CLI

**Status:** done

## What changed

- Added `internal/login`: loopback `/callback` listener, `state` check, browser to `{endpoint}/device?state=&redirect_uri=`, `POST /v1/device/exchange`, writes `client.toml` at `clientconfig.Path()` mode 0600; stderr success line only (no token).
- `workflow login [--endpoint URL]` in `main.go`; missing endpoint (no flag and no file endpoint) exits 1 without write.
- Tests: mock exchange + callback; integration with remote `serve`, simulated device authorize in `OpenBrowser`, `read_write` drain delivers, `read` ingest 403.

## Checks

**Before:**

```
cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/login/ ./cmd/workflow/ -run Login -count=1
stat .../internal/login: directory not found
FAIL
```

**After:**

```
cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/login/ ./cmd/workflow/ -run Login -count=1
ok  	.../internal/login	0.003s
ok  	.../cmd/workflow	3.927s
```

`grep` of `internal/login` and login paths in `main.go`: no `fmt.Print` of `wk_` on success paths.

## Deviations

- None.

## Contract notes

- Device page URL matches 3-03: `/device` with query `state` and `redirect_uri` (OAuth `return` is handled on the page, not by the CLI).
- No contradiction between brief and cited DESIGN bullets.

## Known problems

- None blocking this unit.
