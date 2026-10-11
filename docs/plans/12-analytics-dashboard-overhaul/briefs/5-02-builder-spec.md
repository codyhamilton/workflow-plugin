# Brief: 5-02 — Chart-builder config model

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/lib/builder.ts`, `packages/workflow-analytics/src/lib/builder.test.ts` (both new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-02-builder-spec.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-01, 5-03, 5-04, 5-11, 5-12, 5-14, 5-15, 5-16.
Budget: 4 files to read, about 220 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Chart builder", "The measure × dimension matrix" and "`GET /v1/analytics/query`" (bucket values, `top`).
2. `src/lib/types.ts` — `Schema`, `QueryResponse`, `QueryRow`.
3. `src/lib/buckets.ts` and `src/lib/params.ts` — `pickBucket` and `resolveWindow` (the builder reuses them; do not copy their rules).
4. `src/routes/+page.svelte` lines 100-140 — how Overview turns `weekday` and `hour_of_day` keys into heatmap cells (weekday is `strftime('%w')`, 0 = Sunday; hour 0-23).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The pure model behind the chart builder: the URL form of a chart configuration, which pairings and chart types are legal, and how the schema constrains them, so the builder route (5-07) never invents a rule.

## Contract

From DESIGN.md: "It is driven only by `/v1/analytics/schema`: any measure, up to two dimensions and a bucket. Chart types are line, stacked area, stacked/grouped bar, heatmap, treemap and small multiples, offered only where the shape fits. An unsupported pairing cannot be selected." And "The URL is the view: … every chart configuration (measure, dims, bucket, chart type, top) serialise into the query string."

Settled:

```ts
export type ChartKind = 'line' | 'area' | 'bar' | 'stackedbar' | 'heatmap' | 'treemap' | 'multiples';
export type Bucket = 'none' | 'hour' | 'day' | 'week' | 'month';
export interface BuilderConfig { measure: string; dims: string[]; bucket: Bucket; chart: ChartKind; top: number }
```

URL params (these names are the contract for 5-07 and 5-17): `m` measure, `d` repeated dimension (0 to 2, order matters), `b` bucket, `c` chart kind, `top` (1 to 100, default 20). Filter params are not touched (`urlstate.toSearch` keeps unknown params).

Chart-fit table (`allowedCharts(dims: number, bucket: Bucket)`), exactly:

| dims | bucket none | bucket not none |
|---|---|---|
| 0 | none (the builder shows a single number) | line, area, bar |
| 1 | bar, treemap | line, area, bar, stackedbar, heatmap (time on x, the dimension on y) |
| 2 | heatmap (dim 0 on x, dim 1 on y), treemap (two levels), bar (grouped), stackedbar | multiples (one panel per value of dim 1, one series per value of dim 0), line, area |

`dims` and series semantics: for two dimensions with a bucket the first dimension is the series and the second the panel.

## Changes

Write `builder.ts`:
- `parseConfig(q, schema)`: reads the params, then sanitises against the schema, never throwing. An unknown measure becomes the first schema measure; dims not in that measure's `dims` are dropped; a bucket not in `schema.buckets` becomes `none`; a chart kind not in `allowedCharts` becomes the first allowed kind (or `line` when there are none); `top` is clamped.
- `configToParams(cfg): URLSearchParams` (omits defaults: `b=none`, `top=20`) and `defaultConfig(schema)` (the first measure, no dims, `day`, `line`).
- `allowedDims(schema, measure, chosen: string[])`: the dims that may still be chosen for the next slot: members of the measure's `dims` not already chosen, empty when two are chosen. This is what the dimension selects render; a dimension outside the list can never be offered.
- `allowedBuckets(schema)` returns `schema.buckets`.
- `allowedCharts(dims, bucket)` as the table.
- `dimOrder(dim, keys)` sorts category keys: `hour_of_day` and `weekday` numerically, everything else by name; `weekdayLabel(k)` maps `'0'..'6'` to Sun..Sat.
- `isRangeOk(win, bucket, tz)`: true when `pickBucket` says the bucket is within the 400-bucket cap for the window; the route shows a notice when false (use the helpers already in `buckets.ts`).

Tests (`builder.test.ts`): every row of the table; a measure whose schema dims lack a requested dim is sanitised; round trip `configToParams` then `parseConfig` is the identity for a legal config; with a fixture schema (copy the shape from `tests/e2e` expectations: `cost_usd` takes `harness`, `repo_id`, `model`, `conversation_id`, `hour_of_day`, `weekday`; `rejections` takes only `stage`, `hour_of_day`, `weekday`), `allowedDims` never returns a dim outside the measure's list.

### Keep untouched

Every other file; no network, no DOM, no Svelte imports.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- builder` → fails before (no module), passes after.
- `npm test` → all existing suites still pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
