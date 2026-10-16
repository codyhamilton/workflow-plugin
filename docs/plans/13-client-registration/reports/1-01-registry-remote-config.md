---
cursor:
  subagentId: "bc-66dd8617-81f7-5e0f-abe7-b78919aadd3c"
---

# Report: 1-01 — Registry and remote mode config

**Status:** done

## What changed

- Added `registry.go`: `registry.json` under `WORKFLOW_SERVE_DATA` (policy, sessions, reserved `owners` / `token_hashes`), load/save, policy get/set, session CRUD.
- Extended `Config` with OAuth/public URL fields; `Local()` / `Remote()` per brief; `ConfigFromEnv` refuses non-empty `WORKFLOW_SERVE_KEYS`, loopback → local (OAuth ignored), non-loopback → requires OAuth trio + valid `WORKFLOW_PUBLIC_URL`.
- `New` opens the registry and persists `registry.json` when `Remote()`; `Close` flushes dirty registry state.
- Tests: `TestRegistry`, `TestRemoteConfig`, updated `TestLocalModeConfig` / `TestCORSConfig`; `TestServeOutcome` now checks OAuth refusal, `WORKFLOW_SERVE_KEYS` refusal on loopback, and loopback local ingest (JSON `Content-Type` required under `localGuard`).

## Checks

**Before** (no `TestRegistry` / `TestRemoteConfig` yet; `TestServeOutcome` still keyed via env):

```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	0.003s
PASS ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/cmd/workflow	0.526s
```

**After:**

```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	0.004s
PASS ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/cmd/workflow	0.453s
```

## Deviations

- `WORKFLOW_SERVE_KEYS` refusal is implemented in `ConfigFromEnv` only (not duplicated in `runServe`); startup still exits before listen with an error naming `WORKFLOW_SERVE_KEYS`.
- `New` panics on registry open/persist failure (same package tests use writable temp dirs).

## Contract notes

- Wildcard non-loopback bind without OAuth now errors on missing `GITHUB_OAUTH_*` / `WORKFLOW_PUBLIC_URL` instead of the old “empty keys” message — matches DESIGN remote/local split.
- No contradiction between brief and DESIGN cited bullets.
