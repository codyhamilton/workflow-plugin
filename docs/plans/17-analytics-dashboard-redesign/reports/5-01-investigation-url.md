---
cursor:
  subagentId: "bc-39407598-cacf-5946-9232-86617ad2eaeb"
---

# Report: 5-01 — Investigation URL codec

**Status:** done

## What changed

- Added `packages/yakka-analytics/src/lib/investigation/request-url.ts`: `isInvestigationQuery`, `parseInvestigationRequest`, `investigationRequestToSearch`, and `InvestigationUrlError`. Window uses `range` / `from` / `to` / `tz`; filters reuse `urlstate` dim keys and `x.<dim>` excludes; `ask` and variant fields use boundary names (`measure`, `bucket`, `dim`, `grain`, `kind`, `id`). For `ask=quality`, `kind` is the artifact kind, not a filter dim.
- Added `packages/yakka-analytics/src/lib/investigation/request-url.test.ts` with round-trip cases from the brief plus legacy-key non-write checks.
- `aggregate.ts`: `metaFieldsFrom` so `unionMeta` for conversations/executions only reads meta fields when present (behaviour unchanged).
- `aggregate.test.ts`: `ConversationDetail.totals` fixture matches `Totals`.

## Checks

**Before**

- `npm test -- src/lib/investigation/request-url.test.ts`: no test files (exit 1).
- `npx tsc --noEmit`: `aggregate.test.ts(155)` TS2353 (`hook_events` on `Totals`); `aggregate.ts(488,504)` TS2559 (`Conversations` / `Executions` vs `unionMeta`).

**After**

- `npm test -- src/lib/investigation/request-url.test.ts`: 17 passed.
- `npx tsc --noEmit`: no errors on `aggregate.ts`, `aggregate.test.ts`, or `request-url*`.
- `npm test` (package): 243 passed.

## Departures

None.

## Contradictions

`kind` is both a filter dimension and the quality `ask` field name in DESIGN.md. The codec treats `kind` as the quality ask parameter when `ask=quality` and does not map it into `filters.include.kind` on parse. A URL cannot simultaneously encode a quality artifact kind and an independent `kind` filter via the same key; the brief’s plain `kind` name is preserved.

## Problems

None.
