---
cursor:
  subagentId: "bc-b19c04d2-9eec-5ba3-a43d-1504b60fb16d"
---

# Report: 2-03 — Profile UI, collector overview, and e2e setup

**Status:** done

## What changed

- `api.ts`: `apiPost`, tenant/token helpers (`createTenant`, `createToken`, `listTokens`, `listAdminTokens`, `revokeToken`); shared collector transport (credentials, no bearer).
- New `/profile`: create tenant and token (plaintext once + copy), list/revoke tokens, admin all-tokens table when `me.admin`.
- `+layout.svelte`: Profile nav link; profile page without filter chrome; no-tenant copy links to profile.
- `global-setup.ts`: drops `WORKFLOW_SERVE_KEYS`; remote-mode keyed serve with registry-seeded `wk_` bearer, CORS for preview; same `state.json` shape for specs.
- Vitest: collector `apiPost` / revoke / createToken transport.

## Checks

**Before** (keyed serve still used `WORKFLOW_SERVE_KEYS`):

```
cd packages/workflow-analytics && npm test
 Tests  163 passed (163)

cd packages/workflow-analytics && npx playwright test tests/e2e/session.spec.ts tests/e2e/settings.spec.ts --grep-invert @slow
Error: workflow serve exited early (1)   # global-setup keyed start
```

**After:**

```
cd packages/workflow-analytics && npm test
 Tests  166 passed (166)

cd packages/workflow-analytics && npx playwright test tests/e2e/session.spec.ts tests/e2e/settings.spec.ts --grep-invert @slow
  4 passed (11.0s)
```

Vitest still asserts collector `apiGet` omits `Authorization` and sets `credentials: 'include'`; added the same for `apiPost`.

## Deviations

- E2e keyed token is seeded by writing `registry.json` before remote `workflow serve` starts, not by a live OAuth login + `POST /v1/tokens`. `GitHubHTTPBase` is not available on the CLI serve path, so mock-GitHub session bootstrap from Node was not viable without touching `tools/workflow` (out of scope). Seeding matches 2-01 registry on-disk shape and exercises the same bearer ingest path `settings.spec.ts` needs.

## Contract notes

- Collector routes other than `/` still omit `?tenant=` (phase 1 carried item 2); unchanged by design for this unit.
- No contradiction between brief and cited DESIGN bullets.

## Follow-up for phase 3

- Wire `tenant` from `GET /v1/me` on remaining analytics routes in collector mode.
