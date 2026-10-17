# Brief: 5-05 — Dashboard page grid and import notices

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/dashboards/+page.svelte`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/5-05-dashboard-page-grid.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-01-view-store-config, 5-04-dashboard-tile-render, 5-03-remove-embed-chrome.
Runs alongside: nothing.
Budget: 6 files to read, about 200 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Domain: Dashboards grid and tile cap; Phase 5 import outcome.
2. `packages/workflow-analytics/src/routes/dashboards/+page.svelte`.
3. `packages/workflow-analytics/src/lib/components/DashboardTile.svelte`.
4. `packages/workflow-analytics/src/lib/views.ts` — `importDashboard` return shape, `addToDashboard` cap.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The dashboards route lists dashboards, lays out in-document tiles on a two-column grid with span `w`, enforces the twelve-tile cap on add, and surfaces import drop counts.

## Contract

Domain: Dashboards:

- A dashboard is `{"id","name","tiles":[{"viewId","w"}]}`. The grid is two columns and `w` is the column span, `1` or `2`. At most 12 tiles. Add refuses a tile past 12. Import keeps the first 12 tiles of each dashboard, drops the rest, and states how many tiles were dropped.

Phase 5 outcome:

- Adding it to a dashboard renders it in the dashboard page, not an iframe. Changing the dashboard window changes the tile's numbers. A second tile on the same dashboard uses that same window.
- Import of a 13-tile document keeps 12 and states how many tiles were dropped.

## Changes

- Remove `tileSrc`, iframes, and all `embed=1` copy.
- Render each tile with `<DashboardTile view={…} />` inside `data-testid="dash-tile"`.
- CSS grid: two columns at `min-width: 1024px`; tile with `w: 2` spans both columns (`grid-column: span 2`). Default height can stay ~360px or grow with content; charts must remain visible without nested scroll unless the full report already scrolls.
- `addToDashboard`: when the store refuses the 13th tile, show the existing cap notice (update copy to match contract: at most 12 tiles, not iframe performance).
- After `importDashboard`, if `tilesDropped > 0` or `viewsDropped > 0`, show a `role="status"` notice with both counts (`data-testid="dash-import-drops"`).
- Reorder/remove/move controls keep working on `tiles` indices.
- Update page intro text to describe in-document tiles under one filter bar.

### Keep untouched

Store implementation (5-01), `DashboardTile` internals (5-04), and e2e specs (5-06).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- Grep `packages/workflow-analytics/src/routes/dashboards/+page.svelte` for `iframe` and `embed` → no matches.
- 5-06 runs the playable e2e gate; for this unit report `npm test -- src/lib/views.test.ts` still passes if you touched nothing in views, and note dashboard page ready for 5-06.

If 5-06 is not yet run, add no e2e here; the grep check is the local gate for this brief.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
