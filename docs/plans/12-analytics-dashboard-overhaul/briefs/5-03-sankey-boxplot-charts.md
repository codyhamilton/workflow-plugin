# Brief: 5-03 — Sankey and box-plot chart components

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/lib/charts/EChart.svelte`, new `src/lib/charts/sankey.ts`, `sankey.test.ts`, `SankeyChart.svelte`, `box.ts`, `box.test.ts`, `BoxChart.svelte` (all under `packages/workflow-analytics/`). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-03-sankey-boxplot-charts.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-01, 5-02, 5-04, 5-11, 5-12, 5-14, 5-16 (5-04 owns `options.ts` and `BarChart.svelte`; you must not edit them).
Budget: 5 files to read, about 260 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Charts and theme" (each chart has a data-table toggle, tokens, light and dark) and the Executions and Quality bullets under "Views".
2. `src/lib/charts/EChart.svelte` — the `echarts.use([...])` registration and its props (`build`, `onclick`, `ready`, `theme`).
3. `src/lib/charts/Treemap.svelte` and `src/lib/charts/options.ts` `treemapOption` — the pattern to copy (option builder in a pure file, component wraps `EChart` and `DataTable`, `data-testid`, `data-ready`).
4. `src/lib/charts/DataTable.svelte` and `src/lib/charts/theme.ts` — props and tokens.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Two chart components the later route units need and nothing else registers: a sankey (Executions, 5-09) and a horizontal box plot (Quality, 5-15).

## Contract

Settled interfaces (route units code against these):

```ts
// sankey.ts
export interface SankeyNode { name: string; label?: string }
export interface SankeyLink { source: string; target: string; value: number }
export function sankeyOption(p: { nodes: SankeyNode[]; links: SankeyLink[] }, t: Tokens): object
// SankeyChart.svelte props: { testid: string; nodes; links; onlink?: (l: SankeyLink) => void }
// box.ts
export interface BoxRow { name: string; min: number; p25: number; median: number; p75: number; max: number; marker?: number }
export function boxOption(p: { rows: BoxRow[] }, t: Tokens): object
// BoxChart.svelte props: { testid: string; rows: BoxRow[] }
```

`marker` is the baseline median drawn as a distinct mark on the same row ("distribution charts beside the baseline"). Both components follow the existing chart contract: `data-testid={testid}`, `data-ready`, `data-theme`, a data-table toggle with ids `<testid>-table-toggle` and `<testid>-table` (the sankey table lists `source`, `target`, `value`; the box table lists the five numbers and the marker), colours only from `Tokens`. `onlink` fires on a click of a sankey link (not a node).

## Changes

In `EChart.svelte` only add `SankeyChart` and `BoxplotChart` to the `echarts.use([...])` list (imports from `echarts/charts`), nothing else. Keep the tree-shaking style: no `import * from 'echarts'`. Option builders are pure and tested without a DOM: `sankeyOption` returns one `sankey` series with `emphasis: { focus: 'adjacency' }` and `lineStyle.color: 'gradient'` replaced by a token colour with opacity; `boxOption` returns a horizontal `boxplot` series (one category per row) and, when any row has a `marker`, a `scatter` series for the markers; add `ScatterChart` to the `echarts.use` list for that and say so in your report. Links with `value <= 0` are dropped before building.

### Keep untouched

Everything in `EChart.svelte` except the two registrations; `Treemap.svelte`, `Heatmap.svelte` and the other components.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- sankey box` → each builder has tests that fail before (no module) and pass after: nodes and links appear, zero links dropped, the marker appears only when set, every colour is a token.
- `npm test` → pass; `npm run build` → passes, and the built client chunks still contain no `layerchart` (it is already gone).
- No route uses the components yet; do not add a route to prove them.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
