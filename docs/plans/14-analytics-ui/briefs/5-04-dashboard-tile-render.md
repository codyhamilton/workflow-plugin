# Brief: 5-04 — In-document dashboard tiles

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/lib/components/DashboardTile.svelte`; `packages/workflow-analytics/src/lib/dashboard-tile.ts`; `packages/workflow-analytics/src/lib/view.svelte.ts` (add tile param merge only); `packages/workflow-analytics/src/lib/dashboard-tile.test.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/5-04-dashboard-tile-render.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-01-view-store-config.
Runs alongside: 5-03-remove-embed-chrome (after 5-01).
Budget: 22 files to read, about 900 lines to change, 85 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Domain: Dashboards (rendering and filter/window sharing); Domain: Report interaction (drill, brush, zero-fill vs score gaps — tiles must match full reports).
2. `packages/workflow-analytics/src/lib/views.ts` — `SavedView`, `CHART_PARAM_KEYS`.
3. `packages/workflow-analytics/src/lib/view.svelte.ts` — `paramsFor`.
4. One primary chart per report route (grep `data-testid` and fetch patterns): `hooks/+page.svelte`, `usage/+page.svelte`, `builder/+page.svelte`, `trends/+page.svelte` (neighbouring pages set the bar for drill/brush wiring).
5. `packages/workflow-analytics/tests/e2e/hooks.spec.ts` — `hooks-harness` ready marker (tile done signal).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Render a saved view inside the dashboard document as the same chart content the full report would show, driven by the dashboard URL window and shared filters plus the tile's stored chart params.

## Contract

Domain: Dashboards:

- The dashboard page renders each tile as a component in the same document. There is no iframe and no `embed=1`. Every tile uses the dashboard URL's window and shared filters. Changing that window updates every tile.
- A view is `{"id","name","report","params"}`. `report` is one of `overview`, `trends`, `usage`, `repos`, `hooks`, `quality`, `executions`, `conversations`, `explore`, `builder`. `params` holds that report's chart controls only (`measure`, `dim`, `bucket`, `chart`, `top`, `kind`, `metric`, `group`, `grain`). It does not hold the window or the shared filters.
- The single-number builder case (no dimension, bucket `none`) renders the scalar. It is a valid saved view.

Decisions (`DESIGN.md`):

- **Dashboards are in-document components under one window.** … A saved view stores the chart only. There is no `embed=1`.

## Changes

- Add `dashboard-tile.ts` with pure helpers: `tileExtraParams(report, params)` → the `Record` passed into `view.paramsFor` / route-specific fetches (map stored names to what each report already reads, e.g. builder `measure`→`m`, `dim`→`d`, `bucket`→`b`, `chart`→`c`; trends `metric`, `group`, `chart`, `bucket`; hooks `split`, `bucket`; executions `shape`, `bucket`; quality `kind`, `bucket`; usage `measure`/`grain` when present).
- Extend `view.paramsFor` (or add `paramsForTile(route, tileParams)`) so tile chart params override URL chart keys but never override window or shared filters from `page.url`.
- `DashboardTile.svelte` props: `view: SavedView`, optional `testid` suffix. Switch on `view.report` and mount the same chart modules and data effects as the full route's primary visualization(s) for that report — not an iframe. Minimum coverage required by Phase 5 e2e (5-06): `hooks`, `builder`, `usage`. Implement the other contract reports in the same component switch so an added tile never renders blank.
- Wire drill and brush on tile charts through `view` mutators (same as full pages) so interactions change the dashboard URL and sibling tiles refetch.
- Set `data-testid` on the tile root as `dash-tile-chart` and preserve inner testids (`hooks-harness`, `builder-chart`, etc.) so Playwright can assert readiness without iframes.
- Unit-test `tileExtraParams` for at least builder short-key round-trip and a `/usage?measure=cost_usd` migration param map.

### Keep untouched

`packages/workflow-analytics/src/routes/dashboards/+page.svelte` (5-05), `SaveView.svelte`, backend routes, and full report routes (no requirement to refactor routes into shared modules unless needed — duplication inside `DashboardTile` is acceptable if bounded).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- src/lib/dashboard-tile.test.ts` from `packages/workflow-analytics` → passes.
- Manual or minimal Svelte harness is not required; 5-06 e2e proves render. For this unit alone: `npm test -- src/lib/dashboard-tile.test.ts` before/after is the gate; note in the report that hook/builder tile mount is verified in 5-06.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
