# Brief: 5-02 — Save view as chart config

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/lib/components/SaveView.svelte`; `packages/workflow-analytics/tests/e2e/shell.spec.ts` (save-view tests only — do not edit theme or nav tests). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/5-02-save-view-config.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-01-view-store-config.
Runs alongside: 5-03-remove-embed-chrome, 5-04-dashboard-tile-render (after 5-01 only).
Budget: 6 files to read, about 80 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 5 outcome first bullet; Domain: Dashboards view shape.
2. `packages/workflow-analytics/src/lib/views.ts` — `saveView`, `reportFromPathname`, `chartParamsFromQuery`, `viewHref` (after 5-01).
3. `packages/workflow-analytics/src/lib/components/SaveView.svelte`.
4. `packages/workflow-analytics/tests/e2e/shell.spec.ts` — existing save-view test (grep `saveview`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The save control persists the current report's chart configuration only, not the window or shared filters, and saved-view links open that report with those chart params.

## Contract

Phase 5 outcome:

- Saving a view on `/usage` stores a config with no window and no filter keys.

Domain: Dashboards:

- A view is `{"id","name","report","params"}`. `params` holds that report's chart controls only (`measure`, `dim`, `bucket`, `chart`, `top`, `kind`, `metric`, `group`, `grain`). It does not hold the window or the shared filters.

## Changes

- On save, call `reportFromPathname(page.url.pathname)` and `chartParamsFromQuery(report, page.url.searchParams)`; pass the result to `store.saveView(trimmed, report, params)`.
- Remove embed stripping (no `embed` param exists after 5-03; deleting unknown keys is fine).
- Saved-view menu links use `viewHref(v)` instead of `v.url`.
- If the pathname is not a storable report (`/dashboards`, `/settings`, `/conversation`), disable save or show a short inline message; do not call the store.

### Keep untouched

Filter bar, dashboard routes, and chart components.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- Extend `shell.spec.ts` (or add assertions to the existing save-view test): on `/trends?range=7d&repo_id=r1&metric=commits&group=harness&bucket=day`, save `trends-view`; read `localStorage` key `workflow-analytics-views:views` → parsed entry has `report: 'trends'`, `params` includes `metric`, `group`, and `bucket`, and has no `range`, `repo_id`, or `url`.
- `npx playwright test tests/e2e/shell.spec.ts -g save` from `packages/workflow-analytics` → passes (including prior save-view visibility test).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
