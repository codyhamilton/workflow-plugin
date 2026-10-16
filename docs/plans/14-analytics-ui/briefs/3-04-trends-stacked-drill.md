# Brief: 3-04 — Trends stacked area and series drill

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/trends/+page.svelte`; `packages/workflow-analytics/tests/e2e/trends.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/3-04-trends-stacked-drill.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-03-time-chart-interactions.
Runs alongside: 3-05-usage-distribution, 3-07-hooks-timeseries (after 3-03).
Budget: 8 files to read, about 120 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 3 outcome for `/trends`; Domain: Report interaction (series click, brush, zero-fill on count series).
2. `packages/workflow-analytics/src/routes/trends/+page.svelte` — metric/group/bucket controls and `buildSeries`.
3. `packages/workflow-analytics/src/lib/charts/TimeChart.svelte` — `filterDim`, `onseries`, `area`, `stacked`, `onbrush`.
4. `packages/workflow-analytics/tests/e2e/trends.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Trends supports drilling by the active group dimension via series click, and a control switches multi-key splits to a stacked area chart while keeping brush window selection.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Phase 3 — Model and volume reports:

- On `/trends`, clicking a series key sets that dimension as a filter. A control draws a multi-key split as a stacked area.

Domain: Report interaction (click/shift-click, non-clickable keys) and zero-fill on count series (`buildSeries` already zero-fills gaps).

## Changes

- When `group !== 'none'`, pass `filterDim={group}` and wire `onseries` to `view.drill(group as DimKey, key, { shift })` with guards for `__other__` and empty keys.
- Add a chart-style control (e.g. line vs stacked area) persisted in the URL (`chart=line` | `chart=area` or reuse an existing param pattern on this route). Stacked area uses `TimeChart` with `stacked={true}` and `area={true}`; default remains line when `group` is `none` or a single series.
- Keep existing brush → `view.setWindow`.
- Series names from `buildSeries` use `label()`; drill uses the raw key from the API row (`r.k`), not the display label — align click mapping so the filtered value matches `/query` keys (follow `GroupedBar` / treemap patterns).

### Keep untouched

Schema fetch, bucket cap logic, and `/query` param construction aside from optional `chart` param.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/trends.spec.ts` from `packages/workflow-analytics` → passes, including new tests: `?metric=cost_usd&group=model` then legend/series click adds `model=` chip; shift-click sets exclude mode; stacked area control renders stacked series (table view shows multiple series columns summing per bucket).
- Existing brush test in `trends.spec.ts` → still passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
