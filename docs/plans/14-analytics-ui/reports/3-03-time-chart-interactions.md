Status: done

## What changed

- `TimeChart.svelte`: optional `filterDim?: DimKey` and `onseries?: (d: { key: string; shift: boolean }) => void`.
- ECharts `click` on `componentType` `series` or `legend` maps `seriesName` to the drill key; skips `all`, `__other__`, and `''`; passes native `shiftKey`. Ignores axis and other targets.
- When drill props are set, legend `selectedMode: false` is merged in `build` so legend click drills instead of toggling visibility; `cursorFor` shows pointer on drillable series/legend items.
- `onbrush`, brush init (`oninit` / `takeGlobalCursor`), and stacked series naming unchanged (one ECharts series per `TimeSeries.name`).

## Done evidence

Before (baseline, no TimeChart click props):

```
npm test -- src/lib/charts/options.test.ts
 ✓ src/lib/charts/options.test.ts (14 tests)
 Test Files  1 passed (1)
```

After:

```
npm test -- src/lib/charts/options.test.ts
 ✓ src/lib/charts/options.test.ts (14 tests)
 Test Files  1 passed (1)
```

No `timeOption` edits; no new `options.test.ts` cases. Click/brush wiring for routes is manual/component-level here; Playwright proof stays with units 3-04, 3-05, 3-07.

**Manual verification (not mounted in this unit):** with `filterDim` + `onseries` set, a series or legend click should call `onseries({ key: seriesName, shift })` for real keys; `all` / `__other__` / empty do not call; axis/plot clicks do not call; horizontal brush still invokes `onbrush`.

## Departures

None.

## Contradictions

None between this brief and `DESIGN.md` Report interaction.

## Problems outside scope

None observed.
