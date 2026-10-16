# Brief: 3-08 — Builder scalar and heatmap drill

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/builder/+page.svelte`; `packages/workflow-analytics/src/lib/builder.ts`; `packages/workflow-analytics/src/lib/builder.test.ts`; `packages/workflow-analytics/src/lib/charts/BuilderChart.svelte`; `packages/workflow-analytics/src/lib/charts/Heatmap.svelte`; `packages/workflow-analytics/src/lib/charts/multi.ts` (`heatmapProps` only if cell keys needed for drill); `packages/workflow-analytics/tests/e2e/builder.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/3-08-builder-scalar-heatmap.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-01-filter-bar-ten-dims, 3-02-overview-kpi-links, 3-03-time-chart-interactions, 3-06-repos-cost-rank.
Budget: 12 files to read, about 200 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 3 builder outcome; Domain: Dashboards (single-number builder case); Decisions (heatmap cells on overview do not filter — builder outcome explicitly requires heatmap drill on filter dimensions); Domain: Report interaction (non-filter dims).
2. `packages/workflow-analytics/src/lib/builder.ts` — `allowedCharts`, zero-dimension configs.
3. `packages/workflow-analytics/src/lib/charts/BuilderChart.svelte` and `Heatmap.svelte`.
4. `packages/workflow-analytics/tests/e2e/builder.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The builder shows a window scalar when there are zero dimensions and `bucket=none`, and heatmaps drill shared filter dimensions while leaving weekday/hour cells inert.

## Contract

Phase 3 outcome:

- The builder heatmap drills a filter dimension. Zero dimensions with bucket `none` shows the scalar.

Domain: Dashboards:

- The single-number builder case (no dimension, bucket `none`) renders the scalar. It is a valid saved view.

Domain: Report interaction / Decisions:

- `hour_of_day`, `weekday`, and check names are not filters. Overview heatmap does not filter; builder heatmap drills only when the configured dimension is a `DimKey` filter key.

## Changes

- When `config.dims.length === 0`, `config.bucket === 'none'`, and the query returns a single aggregate row, render a prominent scalar (formatted per measure unit) instead of an empty chart state. Extend `allowedCharts(0, 'none')` to allow a `scalar` chart kind or treat it as the default when no chart kinds exist — persist in URL param `c` consistent with `builder.ts`.
- Heatmap: pass `onpick` from `BuilderChart` into `Heatmap`; on cell click, map cell to dimension keys from `resp.dims` and raw keys from `heatmapProps`; call `onpick(dim, key, shift)` only when `dim` is in `DIM_KEYS` and key is not `__other__` or empty. Do not drill for `weekday` or `hour_of_day`.
- Overview route heatmap is out of scope (different file).

### Keep untouched

Save view storage, other chart kinds, and backend.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- src/lib/builder.test.ts` from `packages/workflow-analytics` → passes after updating expectations for zero-dim `none` bucket.
- `npx playwright test tests/e2e/builder.spec.ts` from `packages/workflow-analytics` → passes, including new tests: `?m=hook_events&b=none` with no `d` shows scalar total matching API; heatmap with `d=model&d=harness` click adds a model chip; heatmap with `weekday`/`hour_of_day` does not add chips on cell click.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
