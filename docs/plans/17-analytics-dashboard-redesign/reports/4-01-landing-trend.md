---
cursor:
  subagentId: "bc-75ed486e-12a4-5d7a-911f-c65391f908ff"
---

# Report: 4-01 — Landing trend view

**Status:** done with concerns

## What changed

- Replaced `packages/yakka-analytics/src/routes/+page.svelte` with two sequential `aggregate` `ask: trend` loads (`hook_events`, `cost_usd`, `bucket: day`, window `{ tz }` only, shared `now`) rendered via `TrendChart` and test ids `landing-trend-hook_events` / `landing-trend-cost_usd`.
- Replaced `tests/e2e/overview.spec.ts` with landing-trend assertions; updated the named tests in `session.spec.ts`, `explore.spec.ts`, and `hosted/hosted.spec.ts`.
- Amended `docs/design/07-analytics-site.md` route table row for `/` and the Drill-down KPI sentence.

## Checks

**Before**

- `npm run test:e2e -- tests/e2e/overview.spec.ts`: 2 failed — `landing-trend-hook_events` not found (old overview still mounted).
- `npm run test:e2e -- tests/e2e/overview.spec.ts` (after new spec, before page change): 2 failed — same missing test ids.

**After**

- `npm run test:e2e -- tests/e2e/overview.spec.ts`: 2 passed.
- `npm run test:e2e -- tests/e2e/overview.spec.ts tests/e2e/session.spec.ts tests/e2e/explore.spec.ts -g "landing|collector overview|session summary|overview does not"`: 5 passed.
- `npm test` (package): 226 passed.
- `src/routes/+page.svelte` has no `$lib/charts/`, `EChart`, or `getJSON(`.

Hosted `test:hosted` not run (brief: do not run the hosted config).

## Departures

- **`overview.spec.ts` / `explore.spec.ts` init scripts:** Added a second `addInitScript` that sets `yakka-analytics-base` to the real local serve URL. Without it, Playwright passes the `useServe` tuple in a way that stringifies to `http://127.0.0.1:<port>,,e2e-local-stay` and breaks fetches. `helpers.ts` is out of scope to fix.
- **`session.spec.ts` collector test:** Fulfills `analytics/facets` and `analytics/query` and waits for both landing charts so the page can render through `aggregate` (brief named tenant on `analytics/query` only, not `analytics/summary`).

## Contradictions

None between the brief and DESIGN.md / design 7 cited sections.

## Problems

- **`tests/e2e/helpers.ts` `useServe`:** Array argument to `addInitScript` is stored as `localStorage` base via implicit `Array#toString()`, producing invalid API URLs for local e2e unless tests override base (see departures). Other e2e files using only `useServe` may still fail in this environment (e.g. other `explore.spec.ts` cases, `session.spec.ts` profile redirect tests that still hit `analytics/summary`).
