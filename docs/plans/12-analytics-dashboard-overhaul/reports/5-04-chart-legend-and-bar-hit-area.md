# 5-04 Chart legend reservation and Hooks bar hit area

Status: done with concerns

## What changed

- `packages/workflow-analytics/src/lib/charts/options.ts`
  - `timeOption`: added `const showLegend = series.length > 1;` after the series map. Grid is now `top: showLegend ? 48 : 24`; legend is `{ show: showLegend, top: 0, textStyle: ... }`. With >1 series the legend sits in the 48px above the grid (top 0, ~24px tall) so it cannot overlap the plot; with <=1 series the legend is hidden and grid.top stays 24.
  - `barOption`: added a second `type: 'bar'` series that is a transparent full-band overlay. It uses `barWidth: '100%'`, `barGap: '-100%'`, `z: -1`, `itemStyle.color: 'transparent'`, `emphasis.disabled`, `tooltip.show: false`, and `data` of `{ value: max, key, clickable }` for every row, where `max` is the data max. The overlay therefore spans the whole grid row, so a click anywhere in the row (including the empty track right of a short bar) hits a bar whose `key` is the row key. `__other__` gets `clickable: false` in both series, so it stays inert. The primary series now also uses `barWidth: '100%' / barGap: '-100%'` so the two align. The click `params.data.key` payload is unchanged.

## BEFORE (pre-change) outputs

`npm test -- options`:
```
 Test Files  1 failed (1)
      Tests  2 failed | 10 passed (12)
```
Failures: "adds a full-width transparent overlay so the whole row is clickable", "keeps the __other__ overlay row inert". See concerns.

`E2E_PORT=4504 npm run test:e2e -- hooks.spec.ts`:
```
  1 failed
    tests/e2e/hooks.spec.ts:93:1 › clicking the empty track of a short bar drills that row
  8 passed (28.8s)
```

## AFTER (post-change) outputs

`npm test -- options`:
```
 Test Files  1 passed (1)
      Tests  12 passed (12)
```

`E2E_PORT=4504 npm run test:e2e -- hooks.spec.ts`:
```
  9 passed (20.3s)
```

`npm test`:
```
 Test Files  10 passed (10)
      Tests  78 passed (78)
```

`npm run build`:
```
✓ built in 6.43s
Wrote site to "build"
✔ done
```

## Deviations from the brief

- (a) Also set `xAxis.max` to the data max (`max > 0 ? max : undefined`). Without it ECharts pads the value axis and the overlay bar's `value = max` would not reach the right grid edge deterministically; with `xAxis.max = max` the overlay spans the full grid width. The brief's code block already specified this line; it is flagged here because the Goal text did not.
- (b) The Goal says the whole category band "including the label gutter" is clickable, but the series-based mechanism only covers the grid area (x from `grid.left` = 120 to `grid.right`). The y-axis label gutter (left 120px) is NOT clickable. Only the plot/track region became fully clickable. Stated plainly rather than worked around.

## Contradiction in the brief

The Goal ("whole Hooks bar row clickable, including the label gutter") contradicts the Changes bullet describing an overlay bar confined to the series/grid area. These cannot both hold with a series-based overlay; the label gutter is outside the grid and no series can cover it. Resolved in favour of the Changes bullet (grid-area band only); the gutter limitation is not fixed silently.

## Concerns / problems

- Two of the four new `timeOption` tests did NOT fail before the change, contrary to the brief's expectation that all four would fail. Reason: the pre-change legend had no `top`, so `(option.legend.top ?? 0) + 24 === 24`, and the pre-change `grid.top` was already 24; the inequality `24 >= 24` passed. The multi-series test only becomes meaningful with an explicit `legend.top`. The tests were added verbatim as specified, so this is a weak assertion rather than a product defect, but it means the "reserve space" change had no failing test guarding it before implementation.
- No other non-trivial bug was found outside this scope.

## Unfinished

None. All four AFTER commands pass. No follow-up work identified within the stated scope; the label-gutter clickability gap is the only named shortfall and is out of the achievable mechanism.
