---
cursor:
  subagentId: "bc-7d3588c0-2b30-5368-b0b5-84fbbfb5fd98"
---

# Report: 1-01 — Session gate

**Status:** done

## What changed

- Added pure predicate `decideAfterMeFetch` / `shouldNavigateToProfile` in `packages/yakka-analytics/src/lib/session-gate.ts` and shared gate state in `session-gate.svelte.ts`.
- `+layout.svelte` runs one `fetchMe` per document load, blocks child routes until it settles, applies login redirect and 403→`/profile` navigation; removed the collector 401 sign-in link from the error panel.
- Overview (`+page.svelte`) reads tenant from the layout’s remembered me body instead of calling `fetchMe`.
- `/login` passes a safe `return` query through to `oauthLoginPath`.
- E2E: `useServe('local')` stores `e2e-local-stay`; new session-gate scenarios in `session.spec.ts`; settings redirect assertion updated.
- `docs/design/07-analytics-site.md` Site bullet documents the predicate.

## Checks

**Before (no `session-gate.ts` / test file):** `npm test -- src/lib/session-gate.test.ts` — no tests (file absent).

**After:**

- `npm test -- src/lib/session-gate.test.ts` — 10 passed.
- `npx playwright test tests/e2e/session.spec.ts tests/e2e/settings.spec.ts` — 11 passed.
- `npm test` (package) — 205 passed.

## Departures

None.

## Contradictions

None between brief and cited DESIGN.md contract.

## Problems

None observed within done evidence.
