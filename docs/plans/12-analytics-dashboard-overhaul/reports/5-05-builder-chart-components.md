# 5-05 — Builder chart components: grouped bar and small multiples

Status: **done**

## What changed

New files only, under `packages/workflow-analytics/src/lib/charts/`:

- `multi.ts` — pure transforms/option builders: `groupedBarProps` + `groupedBarOption`,
  `multiplesLayout` (panels + shared `yMax`, 12-panel cap with an "N more" fold), `panelOption`
  (applies shared max), `lineSeries`, `heatmapProps`, `treemapNodes`, `orderKeys` (via `dimOrder`,
  `__other__` forced last), `labelFor` (`weekdayLabel`).
- `multi.test.ts` — 7 unit tests, no DOM.
- `GroupedBar.svelte` — `bar`/`stackedbar`; EChart + data-table toggle (reuses `DataTable`);
  `__other__` drawn but never calls `onpick`.
- `SmallMultiples.svelte` — one EChart panel per second-dimension key, `data-testid="<testid>-panel"`,
  all sharing `yMax`; data-table toggle.
- `BuilderChart.svelte` — outer `data-testid={testid}` `data-kind={config.chart}`; maps chart kinds to
  the above; "No data" when `resp` is null/empty.

No existing file edited. Uses only chart types `EChart.svelte` registers (bar, line, heatmap, treemap).

## Check output

`npm test -- multi` BEFORE (code 1):

```
No test files found, exiting with code 1
filter: multi
```

AFTER (code 0):

```
✓ src/lib/charts/multi.test.ts (7 tests) 12ms
Test Files  1 passed (1)
Tests  7 passed (7)
```

Covers: grouped vs stacked series options; panel count = distinct second-dimension keys; shared y max
across panels; weekday keys `0`..`6` ordered and labelled Sun..Sat; `__other__` last and unclickable;
empty response yields no panels.

`npm test` AFTER: 13 files, 124 tests passed. `npm run build`: passed ("built in 7.92s", site written).
The three new `.svelte` files are not reachable from any route yet, so also compiled directly via
`svelte/compiler` + `vitePreprocess` — all three OK.

## Deviations from the brief

- The brief says builder services must not call `onpick` for `__other__`; the "No data" paragraph and
  the `data-kind`/`data-testid` requirements are implemented as written. I gave child components internal
  testids (`<testid>-chart`) so the outer `BuilderChart` div is the only holder of the contract testid.
  SmallMultiples panels keep `<testid>-panel`.
- `GroupedBar` category clicks pass `config.dims[0]` as the picked dimension; the brief's `onpick(dim,key)`
  does not say which of the two dims a bar segment filters, so I chose the category (x) dimension.
- Treemap leaves pass raw keys as node names (not weekday labels) so `onpick` receives a valid key.

## Contradictions between the brief and the contracts it cites

1. **area vs "stacked area".** The brief (line 37) says `area` maps to `TimeChart` with `stacked`, which
   the contracts implement as `timeOption(..., stacked: true)` -> series `type: 'bar'` on one stack. So
   the `area` chart kind renders stacked **bars**, not an area series. DESIGN.md "Charts and theme"
   describes "stacked area". `EChart.svelte` registers no area type and cannot be edited here (5-03 owns
   it). Left as-is; not resolved silently.
2. **single-dimension heatmap axis.** The brief says heatmap y = "second dimension (or first)" and
   `heatmap` is allowed for 1 dim + a bucket. With a single dimension, "or first" makes y equal to x, which
   is degenerate. I used y = time bucket for the 1-dim + bucket case. Recorded here.

## Non-trivial bug found outside the done evidence (not fixed)

- Symptom: `timeOption` (options.ts:94-105) has no area series type; any "area"/stacked request draws
  stacked bars. Location: `src/lib/charts/options.ts` `timeOption` (`type: stacked ? 'bar' : 'line'`).
  Root cause: the option builder predates the `area` chart kind and EChart registers no area series.
  Owner: 5-02/5-03; out of this unit's owned paths.
