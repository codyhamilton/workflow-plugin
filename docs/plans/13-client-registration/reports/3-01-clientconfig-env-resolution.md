---
cursor:
  subagentId: "bc-51d324e1-6584-5dd4-b9cb-d0582fe39ad8"
---

# Report: 3-01 — Client config and env resolution

**Status:** done

## What changed

- `clientconfig.Load` applies plan 13 resolution: both `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` override the file; `ErrPartialEnv` when exactly one is set (message never includes the key value); neither set keeps file/local behavior.
- `RunStandalone` and `RunStatus` exit 1 on `ErrPartialEnv` before health checks or drain work; other invalid file config on status unchanged (exit 0).
- Tests: unit env/precedence/partial cases; `TestClientEnvDrainIngest` (remote OAuth bind, seeded `registry.json`, env-only ingest); `TestHalfSetEnvRefusal`; MCP `env bearer GET`.

## Checks

**Before** (no env-resolution tests; `TestEnvOverridesFile` would fail):

```
cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/clientconfig/ -run Env -count=1
ok ... [no tests to run]

cd tools/workflow && GOTOOLCHAIN=auto go test ./cmd/workflow/ -run 'Drain|Env|Client' -count=1
ok ... [no tests to run]
```

**After:**

```
cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/clientconfig/ -count=1
ok  	.../internal/clientconfig	0.002s

cd tools/workflow && GOTOOLCHAIN=auto go test ./cmd/workflow/ -run 'Drain|Env|Client|Status' -count=1
ok  	.../cmd/workflow	4.927s

cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/mcp/ -count=1
ok  	.../internal/mcp	1.458s
```

## Deviations

- None.

## Contract notes

- No contradiction between brief and cited DESIGN bullets.

## Problems

- None known.
