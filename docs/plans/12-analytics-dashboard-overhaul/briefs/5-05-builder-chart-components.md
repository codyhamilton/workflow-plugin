# Brief: 5-05 — Builder chart components: grouped bar and small multiples

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: new `packages/workflow-analytics/src/lib/charts/multi.ts`, `multi.test.ts`, `GroupedBar.svelte`, `SmallMultiples.svelte`, `BuilderChart.svelte`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-05-builder-chart-components.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-02.
Runs alongside: 5-01, 5-03, 5-04, 5-06, 5-09, 5-10, 5-11, 5-12, 5-14, 5-15, 5-16 (new files only; you import `options.ts` and the existing chart components, never edit them).
Budget: 6 files to read, about 300 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Chart builder" and "Charts and theme".
2. `src/lib/builder.ts` (5-02) — `BuilderConfig`, `ChartKind`, `dimOrder`, `weekdayLabel`. Use them; do not redefine.
3. `src/lib/charts/options.ts` — `timeOption`, `heatmapOption`, `treemapOption` input shapes; `src/lib/charts/TimeChart.svelte`, `Heatmap.svelte`, `Treemap.svelte`, `DataTable.svelte` — props.
4. `src/lib/charts/EChart.svelte` — props and the registered chart types (bar, line, heatmap, treemap, grid, legend, tooltip).
5. `src/lib/types.ts` — `QueryResponse`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

One component, `BuilderChart`, that renders any legal builder configuration from one `/query` response, so the builder route (5-07) and dashboards need no chart logic of their own.

## Contract

Settled interface:

```svelte
<!-- BuilderChart.svelte props -->
{ testid: string; config: BuilderConfig; resp: QueryResponse | null; onpick?: (dim: string, key: string, shift: boolean) => void; onbrush?: (d: {from: Date; to: Date}) => void }
```

It renders `data-testid={testid}` and `data-kind={config.chart}`. Mapping, by `config.chart`:
- `line`, `area`: `TimeChart` (area is `stacked`); series are the first dimension's keys, or one series named after the measure.
- `bar`, `stackedbar`: new `GroupedBar` (category = first dimension (or time bucket), series = second dimension), `stacked` for stackedbar.
- `heatmap`: existing `Heatmap` with x = first dimension (or time) and y = second dimension (or first), category order from `dimOrder`, `weekdayLabel` for weekday.
- `treemap`: existing `Treemap` (one level, or two levels from two dimensions).
- `multiples`: new `SmallMultiples`: one `TimeChart`-style panel per value of the second dimension, each with the first dimension's series, all panels sharing one y-axis max so they compare, each panel `data-testid="<testid>-panel"` (repeated) and titled with its key. At most 12 panels; the rest fold into one panel noting "N more" (the API already folds to `top`).
`__other__` keys are drawn but never call `onpick`. Every variant has the data-table toggle (reuse `DataTable`); an empty or null `resp` shows the text "No data".

## Changes

Pure option builders go in `multi.ts` (grouped/stacked bar option, small-multiples layout and shared-axis computation) and are unit-tested without a DOM. Components are thin. Use only chart types `EChart.svelte` already registers; if a variant truly needs another registration, report `blocked` (5-03 owns `EChart.svelte`) rather than edit it. Colours only from `Tokens`; a series keeps the same colour across all panels.

### Keep untouched

All existing chart files: this unit adds files only.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- multi` → tests fail before (no module) and pass after: grouped vs stacked series options; panel count equals distinct second-dimension keys; shared y max across panels; weekday keys `0`..`6` ordered and labelled; `__other__` last; an empty response yields no panels.
- `npm test` and `npm run build` → pass.
- No route uses the component yet; 5-07 does.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
