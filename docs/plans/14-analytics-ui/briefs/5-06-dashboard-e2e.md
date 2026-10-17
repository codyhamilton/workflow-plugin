# Brief: 5-06 — Dashboard phase e2e proof

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/tests/e2e/dashboards.spec.ts`; `packages/workflow-analytics/tests/e2e/phase5.spec.ts` (dashboard-related tests only: tests 4, 5, and the dashboard-create-add segment of test 7 — do not edit builder sankey or perf sections unrelated to dashboards). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/5-06-dashboard-e2e.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-02-save-view-config, 5-05-dashboard-page-grid.
Runs alongside: 5-07-analytics-site-doc.
Budget: 10 files to read, about 250 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 5 outcome (all bullets).
2. `packages/workflow-analytics/tests/e2e/dashboards.spec.ts`.
3. `packages/workflow-analytics/tests/e2e/phase5.spec.ts` — dashboard tests.
4. `packages/workflow-analytics/tests/e2e/helpers.ts` — `expectSettled` (grep).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Playwright proves config saves, in-document tiles, shared dashboard window, twelve-tile import cap, and legacy URL import — without iframes.

## Contract

Phase 5 outcome:

- Saving a view on `/usage` stores a config with no window and no filter keys. Adding it to a dashboard renders it in the dashboard page, not an iframe. Changing the dashboard window changes the tile's numbers. A second tile on the same dashboard uses that same window.
- Import of a 13-tile document keeps 12 and states how many tiles were dropped.
- A previously stored URL whose path is `/usage` and whose query carries a measure becomes a config that keeps the measure and drops the window and filter keys. A stored entry whose path is not a report is dropped and counted in the notice.

Domain: Dashboards:

- Export and import are JSON of these objects. A stored URL becomes a view when its path is a known report. Known chart keys are copied into `params`. Window and filter keys on that URL are not copied. A stored entry whose path is not a known report is dropped, and the page states how many were dropped.

## Changes

- Rewrite `dashboards.spec.ts` to assert charts via `page.getByTestId('dash-tile')` descendants (no `frameLocator`, no `iframe`).
- Keep export/import flow; expect v2 export shape (`report`/`params`, not `url`) where the store now emits it.
- Add tests:
  - **Shared window:** two tiles from views saved on `/hooks?range=7d` and `/hooks?range=30d` — on `/dashboards?range=7d&d=…` both tiles' API requests (or visible chart state) use the dashboard 7d window, not the saved ranges.
  - **Window change:** on a dashboard with one hooks tile, click preset 30d → tile refetches (wait for `hooks-harness` `data-ready=true` again) and request URLs include the 30d window.
  - **13-tile import:** paste v2 JSON with 13 tiles → `dash-tile` count 12, `dash-import-drops` mentions 1 tile dropped.
  - **Legacy URL import:** v1 JSON with `/usage?range=7d&measure=cost_usd&repo_id=r1` and `/not-a-report?x=1` → one view, `viewsDropped` notice, stored view has `measure` only.
- Update `phase5.spec.ts` dashboard tests (4, 5, 7c) to use in-document `builder-chart` under `dash-tile`, not iframes. Optionally use `expectSettled` on the tile chart when stable.

### Keep untouched

`tests/e2e/fixture.ts`, unrelated phase5 builder/executions tests, and product source outside owned paths.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `E2E_PORT=4418 npx playwright test tests/e2e/dashboards.spec.ts tests/e2e/phase5.spec.ts -g "dashboard|builder view saved|exports and imports"` from `packages/workflow-analytics` → all selected tests pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
