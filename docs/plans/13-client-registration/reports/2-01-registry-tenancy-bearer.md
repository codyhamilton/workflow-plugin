---
cursor:
  subagentId: "bc-e972358f-14b2-51cb-9aa9-ccd8fef7186e"
---

# Report: 2-01 — Registry, tenancy, and bearer authorization

**Status:** done

## What changed

- Expanded `TokenHashRecord` and registry CRUD: tenant creation, token issue/list/revoke, SHA-256 storage, constant-time `resolveBearer`, persist on mutations.
- Added `tokens.go`: session-only profile routes (`POST /v1/tenants`, `POST/GET /v1/tokens`, `GET /v1/admin/tokens`, `POST /v1/tokens/<id>/revoke`) with bearer rejected before `originGuard` on mutating routes.
- Extended `authorizeRequest` for registry bearer (scope, tenant query mismatch); ingest blocks `read` scope with `read-only token`; remote `tenantForKey` uses registry.
- Tests: tenant create, bearer ingest scopes, revoke/expiry, lists, admin revoke, policy non-revocation, restart load, session summary tenancy.

## Checks

**Before** (no tests matched `Token|Tenant|Bearer|Registry`; full package green):

```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	0.032s
```

**After:**

```
cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/serve/ -run 'Token|Tenant|Bearer|Registry' -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	0.062s

cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/serve/ -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	4.863s
```

## Deviations

- Token list responses are a JSON array of objects (not a wrapped `tokens` field); fields match the design bullets.

## Contract notes

- No contradiction between brief and cited DESIGN bullets.
