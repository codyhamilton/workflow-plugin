---
cursor:
  subagentId: "bc-28bcae36-d15a-597a-9807-6e16e673add6"
---

# Report: 1-02 — OAuth, session, and remote request auth

**Status:** done

## What changed

- Added `oauth.go`: GitHub authorize/callback/logout, injectable `Options.GitHubHTTPBase`, verified-email filter, admission at callback, dashboard redirect to `/`.
- Added `session.go`: `workflow_session` cookie, policy re-check middleware, `originGuard`, `authorizeRequest` for remote bearer vs session, `GET /v1/me`, `PUT /v1/admin/policy`, admin bypass and session eviction when policy denies.
- Updated `serve.go`: new routes, `withSession` wrapper, `localGuard` only when `Local()`, remote 401 message uses `WORKFLOW_PUBLIC_URL/login`.
- Tests: `TestOAuthSessionRemoteAuth`, `TestRemoteSessionIngestAndTenant`, `TestRemotePolicyAdmin`, `TestLoopbackUnchangedWithOAuthEnv` with mock GitHub.

## Checks

**Before** (no OAuth/session tests; full package already green):

```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	0.044s
```

**After:**

```
cd tools/workflow && go test ./internal/serve/ -run 'OAuth|Session|RemoteAuth|Policy' -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	0.065s

cd tools/workflow && go test ./internal/serve/ -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	4.768s
```

Mock GitHub login sets `workflow_session` and `GET /v1/me` returns `"admin":true` for verified `codyh@ctzns.net` (see `TestOAuthSessionRemoteAuth`).

## Deviations

- None from this brief.

## Contract notes

- Phase 1 remote bearer without a configured key always yields `{"error":"unauthorized"}`; registry token lookup is deferred to phase 2, as specified.
- No contradiction between brief and cited DESIGN bullets.
