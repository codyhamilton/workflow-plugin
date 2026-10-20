---
cursor:
  subagentId: "bc-c88377a0-5486-5ab1-8067-7336c004a327"
---

# 5-05 Outcome gaps — execution report

**Status:** done

## What changed

- **Brush:** `ChartHost.svelte` arms ECharts `lineX` brush on mount/option apply (same pattern as `TimeChart.svelte`) and clears/re-arms after `brushEnd`, so `helpers.brush` drag commits via `onBrushEnd` and refetches.
- **Distribution:** `UsageTool.svelte` `distData` prefers the `all` row when it has bins; otherwise uses the first row with bins; measure comes from the request.
- **Quality gap:** `qualityOption` fills day/week/month bucket slots in `[from, to]` via `bucketStarts` / `instantKey`, inserting `null` medians for missing buckets.
- **E2E:** Removed `interactions.spec.ts` (old report UI). Added brush and distribution coverage to `investigation-shell.spec.ts` and `investigation-tools.spec.ts`.
- **Unit:** `chart-frame.test.ts` quality case asserts median series includes `null` for a missing day.

## Checks

### Before (parent `9425343`)

`npm test -- src/lib/analysis/chart-frame.test.ts` — 8 passed (quality test did not assert gap `null`).

`npx playwright test tests/e2e/investigation-shell.spec.ts tests/e2e/investigation-tools.spec.ts` — 9 passed (no brush or distribution scenarios).

`tests/e2e/interactions.spec.ts` — present; targets `/trends`, `/usage`, etc.

### After

`npm test -- src/lib/analysis/chart-frame.test.ts` — 8 passed (quality median gap assertion passes).

`npx playwright test tests/e2e/investigation-shell.spec.ts tests/e2e/investigation-tools.spec.ts` — 11 passed (brush + distribution included).

`tests/e2e/interactions.spec.ts` — deleted.

`npm test` (packages/yakka-analytics) — 248 passed.

`git diff --name-only` — no paths under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

## Departures

- Added two Playwright tests and strengthened the unit quality assertion. The brief’s done evidence required those scenarios; the Changes section only named product fixes, not new tests. Tests live only in owned spec files.

## Contract

No contradiction with DESIGN.md Phase 5 outcome clauses cited in the brief.
