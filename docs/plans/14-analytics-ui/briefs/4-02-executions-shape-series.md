# Brief: 4-02 — Executions shape filter and series

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/executions/+page.svelte`; `packages/workflow-analytics/src/lib/types.ts` (extend `Executions` with optional `bucket` and `series` only); `packages/workflow-analytics/tests/e2e/executions.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/4-02-executions-shape-series.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-01-quality-score-series (prior commit may touch `types.ts`; land after 4-01 or rebase).
Runs alongside: 4-03-conversations-cost-distribution, 4-04-conversation-window-timeline.
Budget: 12 files to read, about 220 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 4 `/executions` outcome; Domain: Analytics reads **`GET /v1/analytics/executions`** (`shape`, `series`, `counts`); Domain: Report interaction (`shape` is an executions page parameter, not a shared filter; zero-fill on count series).
2. `packages/workflow-analytics/src/routes/executions/+page.svelte` — sankey, client-side `filteredRows`, fetch key omission of `shape`.
3. `tools/workflow/internal/serve/analytics_executions_test.go` — `shape` filters rows only; `series` key order.
4. `packages/workflow-analytics/src/lib/charts/TimeChart.svelte` — `stacked`, `area`, `onbrush` (read only).
5. `packages/workflow-analytics/tests/e2e/executions.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Executions filters rows through the API `shape` parameter, keeps funnel counts as window totals, and adds a stacked time series of the three shapes with brush window selection.

## Contract

Phase 4 outcome:

- On `/executions`, clicking a sankey edge sets `shape` in the URL. The next page of rows matches that shape. The funnel counts stay the window totals. A stacked series of the three shapes over the window is on the page. Brushing that series sets the window and the series follows.

`GET /v1/analytics/executions` from DESIGN.md (binding):

- Accepts repeatable `shape` (`complete`, `unreported`, `started`; anything else 400 `{"error":"unknown shape <s>"}`). Repeatable values are OR'd. No `shape` means all rows. `shape` filters `rows` and the cursor only. `counts` stays the three window totals with `shape` ignored.
- An optional `bucket` of `day`, `week`, or `month` adds `series` of exactly three objects, `key` `complete`, `unreported`, `started`, in that order, each with sparse `points` of `{"t","n"}`. `shape` does not change `series`. The cursor binds `shape` and `bucket` the same way it already binds the other filters.

Report interaction: zero-fill applies to count series only (apply when mapping execution `series` to `TimeChart` points).

## Changes

- Include URL `shape` in the executions fetch (`view.paramsFor('rest', { shape: … })` with repeatable append, or parse comma list into repeated params). Remove client-only `filteredRows`; table shows API `rows`.
- Refetch when `shape` changes (fix `queryKey` / effect deps so shape is not untracked while shared filters are).
- Request `bucket` (same picker pattern as other pages) and render `series` with `TimeChart` (`stacked={true}`, `area={true}`, no series drill). Map keys `complete`, `unreported`, `started` in API order.
- Wire `onbrush` → `view.setWindow`. Sankey and link buttons keep setting `shape` via `view.setParam`; counts tiles still use `counts` from the response.
- `Pager` continues to pass the same `params` including `shape` so load-more pages match.

### Keep untouched

`SankeyChart.svelte`, `TimeChart.svelte`, backend, other routes.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/executions.spec.ts` → passes, including new tests: with `shape=complete` the first executions request includes `shape=complete`, tile counts still match `EXECUTION_COUNTS`, rows are only `complete`; sankey/link filter survives reload and paging (`limit=1` walk under `shape=complete`); stacked series chart visible (`data-testid` you add); brush sets custom `from`/`to` and the series request uses the narrowed window.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
