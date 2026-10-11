# Brief: 5-06 — Shell: save-view control, nav, embed mode, notices that persist

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/+layout.svelte`, new `src/lib/components/SaveView.svelte`, `src/lib/state.svelte.ts`, `src/lib/components/Notices.svelte`, `tests/e2e/shell.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-06-shell-saved-views-embed-notices.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-01.
Runs alongside: 5-02, 5-03, 5-04, 5-05, 5-10, 5-11, 5-12, 5-14, 5-15, 5-16 (nobody else edits the layout). The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 6 files to read, about 200 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Saved views and dashboards", "The URL is the view", and the Phase 5 outcome.
2. `src/lib/views.ts` (5-01) — the store API (`store.saveView`, `store.listViews`, `subscribe`).
3. `src/routes/+layout.svelte` — the nav list, `chrome`, `navHref`, and the effect that calls `clearError`/`clearNotices`.
4. `src/lib/state.svelte.ts`, `src/lib/components/Notices.svelte`, `src/lib/query.ts` lines 140-170 (where `setNotice` is called, including on a cache hit).
5. `tests/e2e/shell.spec.ts` — helpers and test ids.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The shell lets anyone save the current page as a named view and reach it again, links to the new Builder and Dashboards routes, hides its chrome in embed mode, and no longer erases the `partial` and `ignored_filters` notices it was meant to show.

## Contract

- Saved view = the current `pathname + search` stored under a name (`store.saveView`). The stored url never contains `embed=1`.
- Test ids (5-17 and 5-08 depend on them, keep exactly): `saveview-name` (input), `saveview-save` (button), `saveview-menu-toggle` (button opening the list), `saveview-item` (each saved view, a link to its url), `saveview-delete` (per item).
- Embed mode: when the page query has `embed=1` the layout renders only `{@render children()}` (no header, nav, FilterBar, chips or save control); the filter state still comes from the URL so the page behaves as normal. The dashboards route (5-08) uses this for its iframes.
- Nav gains `/builder` ("Builder") after Trends and `/dashboards` ("Dashboards") before Settings. `chrome` (FilterBar, chips, notices) stays off on `/settings` and `/conversation` and is also off on `/dashboards`; the save control shows on every route except `/settings`, `/conversation` and `/dashboards`.
- Carried (Phase 4) item 8, notices self-clear: the layout effect that calls `clearNotices` on every `pathname`/`search` change runs after a child's request has already set a notice (a cache hit sets it synchronously), so a notice shows for a frame and is gone. Fix so a notice set by a request for the current view survives until that view changes again: for example key notices to the request slot and clear a slot's notice when that slot starts a new request (in `state.svelte.ts`/`query.ts` terms), not on navigation. `query.ts` belongs to 5-11, so fix it from the layout and `state.svelte.ts` side only; if that is impossible, report `blocked` and name the exact line in `query.ts`.

## Changes

Keep `FilterBar`, `FilterChips`, `view.svelte.ts` and the existing nav behaviour untouched. `SaveView.svelte` uses `store` from `views.ts` and a reactive copy refreshed by `subscribe`. Add tests to `shell.spec.ts`: save the current view and see it listed, reload and see it still listed, `?embed=1` shows no `header`, `/dashboards` and `/builder` links exist; and a regression for the notices: with the fixture, a `hook_events` Trends query filtered by `kind` shows `notice-ignored` and it is still present 500 ms later.

### Keep untouched

`navHref` behaviour (filters kept in every link but Settings), the error panel, `clearError`, and every existing test id.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm run test:e2e -- shell.spec.ts` → the new notice-persistence test fails before (reproduce the self-clear first) and passes after; all other shell tests pass.
- `npm test` and `npm run build` → pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
