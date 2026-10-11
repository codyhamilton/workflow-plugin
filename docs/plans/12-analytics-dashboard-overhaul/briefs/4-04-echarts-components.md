# Brief: 4-04 — ECharts components, theme tokens and the data-table toggle

Consumer: a Svelte 5 worker (flash-tier); 4-05 and every route unit use these components and the theme tokens.
Owned paths: `packages/workflow-analytics/package.json`, `package-lock.json`, `src/lib/theme.css` (new), and new files under `src/lib/charts/`: `EChart.svelte`, `options.ts`, `options.test.ts`, `theme.ts`, `theme.test.ts`, `BarChart.svelte`, `TimeChart.svelte`, `Heatmap.svelte`, `Treemap.svelte`, `Sparkline.svelte`, `DataTable.svelte`. Touch nothing else; leave `Bars.svelte`, `LineSeries.svelte` and `palette.ts` in place (old routes use them until 4-16).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-04-echarts-components.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 4-01, 4-02, 4-03.
Budget: 6 files to read, about 500 lines to write, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`. `npm install echarts` needs network; if it fails, report `blocked`. Pin the version the install resolves (npm shows 6.1.0 at refine time) and import only from `echarts/core` plus the charts and components you register (bar, line, heatmap, treemap; grid, tooltip, legend, brush, visualMap, aria; SVGRenderer) so the bundle stays small.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": ECharts, light and dark theme tokens following the system preference, a data-table toggle per chart, works down to 1024 px, drill-down rules (`__other__` is not clickable), brush-to-zoom.
2. `packages/workflow-analytics/src/lib/charts/Bars.svelte`, `LineSeries.svelte`, `palette.ts` — what the old charts take, so the new ones can replace them.
3. `packages/workflow-analytics/src/lib/series.ts` — `fillBuckets`.
4. `packages/workflow-analytics/package.json`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Four reusable ECharts components (bars, time series with brush, heatmap, treemap) plus a sparkline, each with light and dark rendering, a data-table view, and click, shift-click and brush events, replacing LayerChart.

## Contract

- Theme: tokens are CSS custom properties on `:root`, redefined under `@media (prefers-color-scheme: dark)`. Names: `--bg`, `--surface`, `--text`, `--muted`, `--border`, `--accent`, `--danger`, `--series-1` to `--series-8`. `theme.ts` reads them with `getComputedStyle` at render and builds the ECharts option colours from them, and re-renders when the media query changes. The charts never hard-code a colour.
- Every chart root element carries `data-testid={testid}`, `data-ready` (`"false"` until the ECharts `finished` event, then `"true"`; back to `"false"` on every new option) and `data-theme` (`light` or `dark`). Renderer is SVG so marks are DOM elements.
- Data-table toggle: a button `data-testid="{testid}-table-toggle"` switches between the chart and `DataTable` (`data-testid="{testid}-table"`, one `<tr>` per row, columns of the chart's data; a clickable row fires the same select event as its mark). Default is the chart.
- `BarChart` is horizontal: props `{testid, rows: {key: string, label?: string, value: number}[], unit?: string, selectable?: boolean, onselect?: (d: {key: string, shift: boolean}) => void}`. Fixed grid in px: `left 120, right 24, top 8, bottom 24`; category axis `inverse: true` (first row on top); one bar per row; height is `max(120, 28 × rows + 32)` px. The 4-03 helper `clickBar` computes bar centres from this geometry; do not change it. A row whose key is `__other__` is drawn but is not clickable (no `onselect`, no pointer cursor, and its table row is inert).
- `TimeChart`: props `{testid, series: {name: string, points: {t: string, v: number}[]}[], bucket: 'hour'|'day'|'week'|'month', stacked?: boolean, onbrush?: (d: {from: Date, to: Date}) => void}`. Time axis, line (or stacked bars when `stacked`), the ECharts `brush` component with `brushType: 'lineX'` activated on mount, so a horizontal drag fires `brushEnd` and calls `onbrush` with the brushed time range; clear the brush after the call.
- `Heatmap`: props `{testid, cells: {x: number, y: number, v: number}[], xLabels: string[], yLabels: string[]}` with a `visualMap`. Used for hour of day (0 to 23) by weekday (0 to 6; see `weekday` semantics in `tools/workflow/internal/store/query.go`).
- `Treemap`: props `{testid, root: {name: string, key?: string, value?: number, children?: …}[], onselect?: (d: {path: string[], shift: boolean}) => void}`; leaf click calls `onselect` with the names from root to leaf.
- `Sparkline`: props `{testid, points: {t: string, v: number}[]}`; 28 px high, no axes, no interaction.
- Shift state comes from the click event's `event.event.shiftKey`.
- 1 s budget: setting an option on a chart with 400 points must stay well under 100 ms; do not animate (`animation: false`).

## Changes

1. `npm install echarts`; commit the lockfile. Do not remove `layerchart` (4-16 does).
2. Write `theme.css` with the tokens above (light defaults, dark under the media query), and a short comment that the layout imports it.
3. `options.ts`: pure functions `barOption(props, tokens)`, `timeOption`, `heatmapOption`, `treemapOption` returning ECharts options, so the logic is testable without a DOM. `theme.ts`: `readTokens(el)` and `watchScheme(cb)`.
4. `EChart.svelte`: owns the `echarts.init(el, null, {renderer: 'svg'})` lifecycle, `ResizeObserver`, dispose on destroy, `data-ready`, and forwards `click` and `brushEnd` to props. The four chart components wrap it with their option builder and the toggle and table.
5. Components must render with an empty data array without throwing (show "No data").

### Keep untouched

`Bars.svelte`, `LineSeries.svelte`, `palette.ts` and the `layerchart` dependency.

## Done evidence

Write the failing `options.test.ts` first and report the output before and after.

- `npm test` → passes, with tests that: `barOption` orders categories first-row-first and sets the fixed grid; an `__other__` row yields no clickable flag; `timeOption` registers the brush with `lineX`; `heatmapOption` builds 24 × 7 cells with a visualMap range from the data; `readTokens` falls back to defaults when a variable is empty.
- `npm run build` → passes and `npm run check:bundle` passes (no secret reaches the bundle; the check is run by `scripts/e2e-build.mjs`, so run `E2E_KEY=k E2E_DUMMY_TOKEN=d npm run build && E2E_FORBIDDEN=k,d npm run check:bundle`).
- Add a temporary route `src/routes/_charts/+page.svelte` while working to eyeball the four components in light and dark with `npm run dev`, then delete it before committing: it is not an owned path.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
