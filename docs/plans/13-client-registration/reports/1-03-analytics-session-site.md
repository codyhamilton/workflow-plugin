---
cursor:
  subagentId: "bc-ef477d40-4c3f-5490-a7c2-cca9f1854711"
---

# Report: 1-03 — Analytics site session mode

**Status:** done with concerns

## What changed

- `api.ts`: `isCollectorMode()`, `fetchMe()`, collector fetches use `credentials: 'include'` and never send `Authorization` (stored key ignored when base is empty).
- `+page.svelte`: loads `GET /v1/me` per navigation in collector mode; appends `tenant` to overview summary/query requests when the session owns a tenant.
- `+layout.svelte`: collector-specific 401 → `/login`; 403 `no such tenant` copy; hides filter chrome on `/login`.
- New `/login` route with GitHub sign-in link and `error=denied` message.
- Vitest: collector transport and `fetchMe`; Playwright `session.spec.ts` (login + tenant on summary).

## Checks

**Before** (pre-change baseline; added failing collector transport assertions first):

```
cd packages/workflow-analytics && npm test
 Test Files  15 passed (15)
      Tests  161 passed (161)

cd packages/workflow-analytics && npm test -- src/lib/api.test.ts
 Tests  2 failed | 4 passed (6)   # credentials include + ignore key in collector mode
```

**After:**

```
cd packages/workflow-analytics && npm test
 Test Files  15 passed (15)
      Tests  163 passed (163)

cd packages/workflow-analytics && npm run test:e2e -- --grep 'session|login'
Error: workflow serve exited early (1)   # global-setup could not start e2e serves
```

Vitest confirms empty-base `apiGet('analytics/summary')` uses `credentials: 'include'` and no `authorization` header.

## Deviations

- None from this brief.

## Contract notes

- Overview-only `tenant` wiring matches the brief’s owned paths; other routes still omit `tenant` in collector mode until a follow-up unit wires them.
- No contradiction between brief and cited DESIGN bullets.
