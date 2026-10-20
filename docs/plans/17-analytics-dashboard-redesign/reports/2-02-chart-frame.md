---
cursor:
  subagentId: "bc-046de867-8a40-56a1-9a72-49daf92cef94"
---

# Report: 2-02 — Chart frame

**Status:** done

## What changed

- Added `packages/yakka-analytics/src/lib/analysis/chart-frame/` with analysis-token option builders (`options.ts`, `tokens.ts`), drill helpers (`drill.ts`), frame prop types (`types.ts`), ECharts host (`ChartHost.svelte`), and `ChartFrame` plus `TrendChart`, `BreakdownChart`, `DistributionChart`, `QualityChart` wrappers.
- Public entry `chart-frame/index.ts` exports components, types, token helpers, and option builders.
- Vitest harness `src/lib/analysis/chart-frame.test.ts`: one option test and one SSR render test per kind; asserts series colours come from analysis tokens and are not solarized hexes.
- No imports from `src/lib/charts/`; no fetch or page wiring.

## Checks

**Before**

- `npm test -- src/lib/analysis/chart-frame`: no test files (exit 1).
- `npm test` (package): 205 passed.

**After**

- `npm test -- src/lib/analysis/chart-frame`: 8 passed.
- `npm test` (package): 213 passed.

## Library choice

**Apache ECharts 6** (`echarts/core` + bar/line, brush, SVG renderer) inside `ChartHost.svelte`, separate from legacy `EChart.svelte` and `src/lib/charts/` option builders.

## Departures

None.

## Contradictions

None with DESIGN.md chart-frame contract (presentational frame, token colours, hover/brush/drill callbacks, no fetch).

## Problems

None.
