---
cursor:
  subagentId: "bc-16caa26d-1590-5dd5-a87e-8d0b23d46e38"
---

# Report: 3-01 — Aggregation boundary

**Status:** done

## What changed

- Added `packages/yakka-analytics/src/lib/aggregate.ts` with `aggregate(request, options?)`: resolves window via `resolveWindow` / default thirty-day span, loads in-window facets for `controls`, applies excludes through `apiParams`, and composes the existing `/v1` reads per `ask` (`trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, `executions`). Optional `options.fetcher` replaces `getJSON`; `options.now` pins time in tests.
- Added `packages/yakka-analytics/src/lib/aggregate.test.ts` covering each ask, meta propagation, `conversation_id` exclude, `rest-days` and `bucket-cap` clamp, default window, and tenant gating.
- Amended the **Data layer** bullet in `docs/design/07-analytics-site.md`.

## Checks

**Before**

- `npm test -- src/lib/aggregate.test.ts`: no test files (exit 1).

**After**

- `npm test -- src/lib/aggregate.test.ts`: 13 passed.
- `npm test` (package): 226 passed.
- `git diff --name-only` against parent: no paths under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

## Departures

None.

## Contradictions

None between this brief and DESIGN.md / design 7 cited sections.

## Problems

None.
