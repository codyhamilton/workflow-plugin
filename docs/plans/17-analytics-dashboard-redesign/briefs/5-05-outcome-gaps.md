# Brief: 5-05 — Outcome gaps

Consumer: the phase 5 fixer.
Owned paths: `packages/yakka-analytics/src/lib/analysis/chart-frame/options.ts`, `packages/yakka-analytics/src/lib/analysis/chart-frame/ChartHost.svelte`, `packages/yakka-analytics/src/lib/analysis/chart-frame.test.ts`, `packages/yakka-analytics/src/lib/investigation/tools/UsageTool.svelte`, `packages/yakka-analytics/src/lib/investigation/InvestigationShell.svelte` (only if the brush commit path needs a change), `packages/yakka-analytics/tests/e2e/interactions.spec.ts` (delete or replace), `packages/yakka-analytics/tests/e2e/investigation-shell.spec.ts`, `packages/yakka-analytics/tests/e2e/investigation-tools.spec.ts`. The report path below is allowed. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to origin branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/5-05-outcome-gaps.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit. Test results, not a file list, model, or cost.
Depends on: `5-04` (already on this branch).
Runs alongside: nothing.
Budget: 12 files to read, about 250 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Phase 5 outcome, the brush sentence, the usage-and-cost sentence, and the quality sentence.
2. `packages/yakka-analytics/src/lib/analysis/chart-frame/options.ts` — `qualityOption` and the trend `brush` block.
3. `packages/yakka-analytics/src/lib/analysis/chart-frame/ChartHost.svelte` — the `brushEnd` listener.
4. `packages/yakka-analytics/src/lib/investigation/InvestigationShell.svelte` — `onBrushEnd`.
5. `packages/yakka-analytics/src/lib/investigation/tools/UsageTool.svelte` — `distData` and the distribution chart guard.
6. `packages/yakka-analytics/src/lib/types.ts` — `DistributionRow` and `DistributionBin`.
7. `packages/yakka-analytics/tests/e2e/helpers.ts` — `brush`.
8. `packages/yakka-analytics/tests/e2e/interactions.spec.ts` — the file this unit retires.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Three phase-5 outcome clauses that do not hold yet, and one owned e2e file that still expects the old reports.

## Contract

Cited from `DESIGN.md`, Phase 5 outcome. Settled.

> Brush on the time axis, a breakdown change, and a drill on a real filter dim each call the boundary again and the same graph updates.
>
> Usage and cost draw model against model over time and as a distribution, and an unpriced cost is not a zero.
>
> Quality draws one kind against the baseline, and a bucket with no point is a gap.

`5-04` owned `tests/e2e/interactions.spec.ts` and did not retire it. That file still drives the old report pages.

## Changes

**Brush.** `tests/e2e/helpers.ts` `brush` drags across a chart (mousedown, move, mouseup). On `investigation-trend-hook_events` that drag does not change the URL. The chart only listens for an ECharts `brushEnd`, and that event does not fire for the drag. A drag with `brush(page, 'investigation-trend-hook_events', 0.25, 0.75)` on `/?ask=trend&measure=hook_events&bucket=day&range=30d` must commit the window through the existing `onBrushEnd` path: the URL gains `from` and `to` (or `range=custom`) and another `analytics/query` is sent. Activate the line brush so that drag produces `brushEnd`, or map that drag onto the same commit. Do not add a control that exists only for the test.

**Distribution.** `distData` keeps bins only from the row whose `k` is `all`. The local fixture's distribution rows are not keyed `all`, so `/?ask=distribution&measure=cost_usd&grain=call&dim=model` shows the usage table and no `investigation-usage-distribution` chart. Use the `all` row when it has bins. Otherwise use the bins of the rows the boundary returned (a row that has bins). The distribution chart is visible for that URL.

**Quality gap.** `qualityOption` plots only timestamps that arrived. A missing day is omitted, so the median line joins the neighbors. `connectNulls` is already false. For bucket `day`, insert a null median at each day in `[from, to]` that has no point, in time order, so the series breaks. Do not draw that missing day as zero. Example that must pass: points at `2024-01-01T00:00:00Z` (median 0.4) and `2024-01-03T00:00:00Z` (median 0.6), `from` `2024-01-01T00:00:00Z`, `to` `2024-01-03T00:00:00Z`, bucket `day`, `tz` `UTC`. The median series data includes `null` between those two medians.

**interactions.spec.ts.** Delete it, or replace it with a test that does not open the old report UI. Do not edit `area.spec.ts`, `builder.spec.ts`, `executions.spec.ts`, `filter-bar.spec.ts`, `hooks.spec.ts`, or `settings.spec.ts`.

### Keep untouched

Landing on empty `/`. Drill, shift-exclude, and the ignored `conversation_id` notice. Saved analysis. Legacy route stubs and the shell nav. `src/lib/aggregate.ts`. `packages/yakka/internal/serve`. `packages/yakka/internal/store`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npm test -- src/lib/analysis/chart-frame.test.ts` → the quality case above passes (median data contains `null`).
- `cd packages/yakka-analytics && npx playwright test tests/e2e/investigation-shell.spec.ts tests/e2e/investigation-tools.spec.ts` → passes, including:
  - a drag via `brush` on `investigation-trend-hook_events` sets `from`/`to` or `range=custom` and sends `analytics/query`;
  - `investigation-usage-distribution` is visible for `/?ask=distribution&measure=cost_usd&grain=call&dim=model`.
- `tests/e2e/interactions.spec.ts` is absent, or `npx playwright test tests/e2e/interactions.spec.ts` passes without the old report pages.
- `cd packages/yakka-analytics && npm test` → passes.
- `git diff --name-only` against the parent commit has no path under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
