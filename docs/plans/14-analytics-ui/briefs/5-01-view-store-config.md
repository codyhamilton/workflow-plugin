# Brief: 5-01 — View and dashboard store config

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/lib/views.ts`; `packages/workflow-analytics/src/lib/views.test.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/5-01-view-store-config.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-03-remove-embed-chrome, 5-07-analytics-site-doc.
Budget: 8 files to read, about 450 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Domain: Dashboards (full contract block).
2. `packages/workflow-analytics/src/lib/views.ts` and `views.test.ts` — today's URL model.
3. `packages/workflow-analytics/src/lib/urlstate.ts` — `FILTER_PARAMS` / shared filter keys (grep only).
4. `packages/workflow-analytics/src/lib/builder.ts` — `parseConfig` / `configToParams` URL keys `m`, `d`, `b`, `c`, `top` (grep only).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Replace the saved-view URL payload with report plus chart-only params, reshape dashboards to ordered tiles with column span, enforce the twelve-tile cap, and migrate legacy stored URLs on read and on import.

## Contract

Domain: Dashboards from `DESIGN.md`:

- Storage prefix stays `workflow-analytics-views`.
- A view is `{"id","name","report","params"}`. `report` is one of `overview`, `trends`, `usage`, `repos`, `hooks`, `quality`, `executions`, `conversations`, `explore`, `builder`. `params` holds that report's chart controls only (`measure`, `dim`, `bucket`, `chart`, `top`, `kind`, `metric`, `group`, `grain`). It does not hold the window or the shared filters.
- A dashboard is `{"id","name","tiles":[{"viewId","w"}]}`. The grid is two columns and `w` is the column span, `1` or `2`. At most 12 tiles. Add refuses a tile past 12. Import keeps the first 12 tiles of each dashboard, drops the rest, and states how many tiles were dropped.
- Export and import are JSON of these objects. A stored URL becomes a view when its path is a known report. Known chart keys are copied into `params`. Window and filter keys on that URL are not copied. A stored entry whose path is not a known report is dropped, and the page states how many were dropped.

Phase 5 outcome (migration slice):

- A previously stored URL whose path is `/usage` and whose query carries a measure becomes a config that keeps the measure and drops the window and filter keys. A stored entry whose path is not a report is dropped and counted in the notice.

## Changes

- Replace `SavedView.url` with `report` and `params: Record<string, string | string[]>`. Replace `Dashboard.viewIds` with `tiles: { viewId: string; w: 1 | 2 }[]`.
- Export `REPORT_IDS`, `CHART_PARAM_KEYS`, `reportFromPathname(path: string)`, `chartParamsFromQuery(report, searchParams)`, and `viewHref(view: SavedView)` (builds a navigable site path: report route plus chart params, no window or shared filters).
- Map pathname `/` → `overview`, `/trends` → `trends`, etc., per the contract report list. Unknown paths are not valid views.
- When copying chart keys from a legacy URL, map builder short keys (`m`, `d`, `b`, `c`) into the contract names (`measure`, `dim`, `bucket`, `chart`) inside `params`. Repeatable `dim` uses an array in `params`.
- `saveView(name, report, params)` validates `report` and that every key in `params` is in `CHART_PARAM_KEYS`. Same-name replace keeps id (today's behavior).
- `addToDashboard` refuses when `tiles.length >= 12` (throw `ImportError` with a clear message). New tiles default `w: 1`.
- `moveInDashboard` / `removeFromDashboard` operate on `tiles` order (same indices as today).
- `exportDashboard`: JSON with `version: 2`, dashboard `name`, embedded view definitions `{ name, report, params }` in tile order, each tile including `w`. No window or filter keys in export.
- `importDashboard`: accept `version: 1` (legacy `{ name, url }` views) via the URL→config rule; accept `version: 2`. Return type includes `{ dashboard, tilesDropped: number, viewsDropped: number }` so the UI can notice drops. Cap imported tiles at 12 (`tilesDropped = max(0, incoming − 12)`). Skip views whose path is not a known report (`viewsDropped` counts them).
- On store init, migrate in-memory arrays read from localStorage: entries with a `url` field become `{ report, params }`; dashboards with `viewIds` become `tiles` with `w: 1`.
- Drop `isValidViewUrl` / `MAX_URL_LENGTH` from the public save path; keep strict validation only on legacy import URLs.

### Keep untouched

Storage keys `VIEWS_KEY` and `DASHBOARDS_KEY`, `subscribe` / cross-tab behavior, `ImportError`, and delete-view cascade into dashboards.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- src/lib/views.test.ts` from `packages/workflow-analytics` → passes, including: save stores `{ report: 'usage', params: { measure: 'cost_usd' } }` with no `range`/`repo_id`; `addToDashboard` throws at 12 tiles; import of 13 tile entries keeps 12 and reports `tilesDropped: 1`; import v1 `{"version":1,"name":"x","views":[{"name":"u","url":"/usage?range=7d&measure=cost_usd&repo_id=r1"}]}` yields params `{ measure: 'cost_usd' }` only; unknown path `/settings?foo=1` increments `viewsDropped` and creates no view.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
