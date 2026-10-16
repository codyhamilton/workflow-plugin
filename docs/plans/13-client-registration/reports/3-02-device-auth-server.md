---
cursor:
  subagentId: "bc-af18d6aa-058c-53ae-91b9-cc9448bcc01e"
---

# Report: 3-02 — Device authorization server

**Status:** done

## What changed

- **`POST /v1/device/authorize`** (remote only): session cookie, `Content-Type: application/json`, `Origin` = `WORKFLOW_PUBLIC_URL`. Body: `redirect_uri`, `state`, `tenant`, `scope`, `expires_at` (RFC3339, strictly future). Validates loopback `http`/`https` redirect; issues an ordinary registry token; stores a one-time device code (hash + plaintext until exchange); responds **303** to `redirect_uri` with `code` and `state` query params only (no `wk_` in URL or body).
- **`POST /v1/device/exchange`** (remote only): no session, no `Origin` requirement. Body: `code`, `state`, `redirect_uri` (must match authorize). Returns `{"endpoint":"<collector origin>","token":"<wk_…>"}` once; deletes code; repeat → **401** with no token. Device code is not a bearer.
- Registry: `device_codes` in `registry.json` with hashed code, token id, bound redirect/state, and plaintext until consumed.

## Checks

**Before** (`-run Device`, no tests yet):

```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	0.004s [no tests to run]
```

**After:**

```
cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/serve/ -run Device -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	0.018s

cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/serve/ -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	4.886s
```

## Deviations

None.

## Contract notes

No contradiction between brief and cited DESIGN bullets. Token plaintext is held in `registry.json` until exchange (mode 0600); required so exchange works across restart before the CLI redeems the code.
