# Brief: 5-08 — Dashboards route: grid, export, import

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/dashboards/+page.svelte` (new), `packages/workflow-analytics/tests/e2e/dashboards.spec.ts` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-08-dashboards-route.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-01, 5-06.
Runs alongside: 5-07, 5-09, 5-10, 5-14, 5-15, 5-16. The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 5 files to read, about 220 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Saved views and dashboards" and the Phase 5 outcome (survives a reload; export then import into a fresh browser profile).
2. `src/lib/views.ts` (5-01) — the store, `ImportError`, export format.
3. `src/routes/+layout.svelte` (5-06) — `embed=1` renders only the page; `saveview-*` ids.
4. `src/routes/settings/+page.svelte` — a small form page to match in style.
5. `tests/e2e/shell.spec.ts` and `helpers.ts` — spec style; Playwright `browser.newContext()` for a fresh profile.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A Dashboards page that lists dashboards, shows a dashboard as an ordered grid of its saved views, and exports and imports it as JSON.

## Contract

A tile is the saved view's url in an `<iframe>`: `src = <url> + (url has '?' ? '&' : '?') + 'embed=1'`, `loading="lazy"`, `title` the view name. This renders every kind of view (a builder chart, Hooks, Overview) with no per-view code, and works because the layout's embed mode (5-06) hides the chrome. The store guarantees every url is site-relative (5-01); still build the src with `new URL(url, location.origin)` and refuse a different origin.

Test ids (5-17 depends on them, keep exactly): `dash-name` (input) and `dash-create` (button); `dash-item` (each dashboard in the list, a button that selects it, text is the name); `dash-add-select` (select of saved views) and `dash-add` (button); `dash-tile` (each iframe wrapper), `dash-tile-up`, `dash-tile-down`, `dash-tile-remove` (per tile); `dash-delete`; `dash-export` (button that downloads `<name>.json` via a Blob and anchor click); `dash-import-file` (`<input type=file accept=application/json>`), `dash-import-text` (textarea) and `dash-import` (button importing the textarea); `dash-import-error` (the `ImportError` message, shown instead of throwing). The selected dashboard id is in the URL (`?d=<id>`) so a reload keeps it; the dashboards survive a reload through the store.

## Changes

Grid: CSS grid, two columns at 1024 px, fixed tile height (about 360 px). Cap at 12 tiles per dashboard with a visible notice ("each tile is a full page; more than 12 is slow") and no further adds. Keep the page reactive via `store.subscribe`. No filter chrome here (5-06 hides it); each tile carries its own range and filters in its url.

`dashboards.spec.ts` on the fixture: create a dashboard; save a view from `/hooks?range=7d` (use the 5-06 controls), add it; the tile iframe loads and shows the chart (`frameLocator`); reload keeps both; reorder two tiles; remove one; export (wait for the download, read the JSON, assert `version` 1, the view name and url); import that JSON into a second `browser.newContext()` and see the same dashboard and tiles; a malformed JSON shows `dash-import-error` and creates nothing.

### Keep untouched

`views.ts` and the layout (not yours): if something is missing there, report it, do not patch it.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm run test:e2e -- dashboards.spec.ts` → fails before (route missing), passes after.
- `npm test` and `npm run build` → pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
