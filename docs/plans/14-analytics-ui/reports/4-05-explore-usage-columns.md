# Execution report: 4-05 — Explore model, cost, and norm event

**Status:** done

## What changed

- `packages/workflow-analytics/src/routes/explore/+page.svelte`: Added `norm_event`, `model`, and `cost_usd` to `COLUMNS`; `cost_usd` uses Perspective `float` in `SCHEMA`; `toRows` maps `cost_usd` to a finite number or `null` when missing/unparseable; other new fields follow existing string null → `''` behavior.
- `packages/workflow-analytics/tests/e2e/explore.spec.ts`: Added `tableColumnNames` helper and test asserting the Perspective table schema includes `model`, `cost_usd`, and `norm_event` after load.

## Check output

**Before (new test, page unchanged):** `npx playwright test tests/e2e/explore.spec.ts -g "model, cost_usd"` → 1 failed — expected `ArrayContaining ["model", "cost_usd", "norm_event"]`, received column list without those keys (timeout on poll).

**Before (existing suite, no new test):** 5 passed.

**After:** `export E2E_PORT=4412 && npx playwright test tests/e2e/explore.spec.ts` → 6 passed (~18s).

## Departures

None.

## Contradictions

None between this brief and DESIGN.md Phase 4 `/explore` outcome or `ExploreRow` API fields (`model`, `cost_usd`, `norm_event`).

## Known problems

None found in owned surfaces.

## Unfinished work

None.
