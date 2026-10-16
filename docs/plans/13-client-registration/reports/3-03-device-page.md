---
cursor:
  subagentId: "bc-6bc4797c-d3f9-5fea-96fb-7312b03e27d8"
---

# Report: 3-03 — Device page

**Status:** done

## What changed

- Added `/device` page: parses `state` and `redirect_uri`, blocks submit when invalid; lists owned tenants (empty selection when multiple); zero tenants → create-tenant form; grant and expiry have no defaults (expiry field starts empty); unauthenticated users link to `/oauth/login?return=…`; submit calls `POST /v1/device/authorize` and navigates to the redirect URL without showing `wk_` plaintext.
- Added `isValidLoopbackRedirectUri`, `authorizeDevice` in `api.ts` (manual redirect + opaque-redirect follow fallback).
- Unit tests for device helpers; Playwright `device.spec.ts` (mocked APIs).

## Checks

**Before** (`npm test`):

```
Test Files  15 passed (15)
     Tests  166 passed (166)
```

**After:**

```
cd packages/workflow-analytics && npm test
Test Files  15 passed (15)
     Tests  169 passed (169)

npx playwright test tests/e2e/device.spec.ts
  2 passed
```

## Deviations

- `authorizeDevice` uses `fetch` with `redirect: 'manual'` and reads `Location` when present; on opaque cross-origin 303 (`status` 0) it retries with `redirect: 'follow'` to obtain `response.url` before `window.location.assign`. Brief cited browser navigation after 303; this is the fetch workaround for opaque redirects to loopback URIs.
- Playwright authorize test mocks a **same-origin** 303 `Location` so the mock exposes `Location` (Playwright’s cross-origin 303 mock yields opaque redirect and blocked navigation). Real collector 303 to loopback is unchanged.

## Carried / contract notes

- **Carried item 1:** No `tenant` query added on analytics routes beyond `/` and `/profile` (unchanged).
- **Carried item 3:** `global-setup.ts` untouched; e2e mocks APIs like `session.spec.ts`.
- No contradiction between brief and DESIGN device-presentation bullets.

## Known problems

- None blocking this unit. Full loopback navigation is not exercised in Playwright against a cross-origin 303 mock (see deviation); manual verification against a running collector + `workflow login` (3-04) remains the integration check.
