# Report: 3-04 — Trends stacked area and series drill

**Status:** done

## What changed

- **`trends/+page.svelte`:** When `group !== 'none'`, `TimeChart` gets `filterDim={group}`, `onseries` → `view.drill` with `drillByName` mapping display names to raw `r.k` keys (guards `__other__` / empty). URL `chart=line|area` control (shown for multi-series splits); `stacked` + `area` when `chart=area` and multiple series. Brush → `view.setWindow` unchanged.
- **`tests/e2e/trends.spec.ts`:** Series-click drill (include + shift exclude) and stacked-area table assertions.

## Checks

**Before (baseline, no new tests):** `export E2E_PORT=4396 && npx playwright test tests/e2e/trends.spec.ts` → 7 passed.

**After:** same command → 9 passed (added drill + stacked area tests; brush test still passes).

## Departures

- **E2E series click:** Playwright hits ECharts SVG paths `0..6` on the chart, not legend text. With brush armed, legend clicks do not emit drill events; a single path click alone was unreliable in e2e. The test still exercises `TimeChart` `onseries` / `view.drill` end-to-end and asserts a `model=` chip (fixture resolves to the qwen model for this path sequence, not necessarily Sonnet).
- None from implementation scope (only owned files touched).

## Contradictions

- None between brief and `DESIGN.md` Phase 3 trends outcome.

## Known problems (outside done evidence)

- **TimeChart + ECharts:** Legend drill likely needs `legend.triggerEvent: true` (and possibly series trigger options) for reliable legend/series clicks in real UI; 3-03 noted manual verification only. Not fixed here (TimeChart out of scope).
