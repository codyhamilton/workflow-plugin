---
cursor:
  subagentId: "bc-38ee4899-c7c2-51ca-a98b-2f813d017021"
---

# Report: 4-02 — Session 403 on the landing reads

**Status:** done

## What changed

In `packages/yakka-analytics/tests/e2e/session.spec.ts`, only the two `no such tenant` tests:

- Replaced `**/v1/analytics/summary*` mocks with `**/v1/analytics/**` returning 403 `{ error: 'no such tenant' }` (landing uses `facets` / `query` via `aggregate`, not `summary`).
- **Tenant present:** added `trackRequests` for `/v1/analytics/`, `expect.poll` until at least one analytics request, then assert URL ends at `/` and not `/profile`.

`GET /v1/me` bodies unchanged. No edits to app code or other tests.

## Checks

**Before** (`npx playwright test tests/e2e/session.spec.ts -g "no such tenant"`)

- `no tenant: summary 403 no such tenant sends to /profile` — failed: expected `/profile`, received `http://127.0.0.1:4391/` (mocked `summary` only; unmocked `GET /v1/analytics/facets` 404).
- `tenant present: summary 403 no such tenant does not send to /profile` — passed (incidentally; analytics 404 did not trigger profile redirect).

**After**

- `npx playwright test tests/e2e/session.spec.ts -g "no such tenant"` — 2 passed.
- `npx playwright test tests/e2e/session.spec.ts` — 10 passed.

## Departures

None.

## Contradictions

None between this brief and DESIGN.md session-gate contract or the cited `parseJsonResponse` / `shouldNavigateToProfile` behavior.

## Problems

None known.
