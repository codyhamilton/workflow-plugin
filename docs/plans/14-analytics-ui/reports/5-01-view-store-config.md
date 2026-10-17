# Execution report: 5-01 — View and dashboard store config

**Status:** `done`

## What changed

- **`packages/workflow-analytics/src/lib/views.ts`:** Replaced URL-based `SavedView` with `{ report, params }` and `Dashboard.viewIds` with ordered `tiles: { viewId, w }`. Exported `REPORT_IDS`, `CHART_PARAM_KEYS`, `reportFromPathname`, `chartParamsFromQuery`, `viewHref`, and `ImportResult`. Implemented v2 export/import, v1 URL→config import with drop counts, 12-tile cap on add/import, builder short-key mapping (`m`/`d`/`b`/`c`), localStorage migration for legacy `url` / `viewIds`, and legacy-only URL validation (removed from `saveView`).
- **`packages/workflow-analytics/src/lib/views.test.ts`:** Rewrote coverage for the new API, migration, v1/v2 import, tile cap, and done-evidence cases from the brief.

## Checks (before / after)

Command: `npm test -- src/lib/views.test.ts` from `packages/workflow-analytics`.

**Before (legacy store, 20 tests):** all passed — no failing check existed for the new contract; tests still asserted v1 URL export and `viewIds`.

**After:** 28 passed (71ms). Done-evidence cases verified: `saveView` stores `{ report: 'usage', params: { measure: 'cost_usd' } }` without window/filters; 13th tile throws `ImportError`; 13-tile import → 12 tiles and `tilesDropped: 1`; v1 `/usage?range=7d&measure=cost_usd&repo_id=r1` → params `{ measure: 'cost_usd' }` only; `/settings?foo=1` → `viewsDropped: 1`, no view.

## Departures

None.

## Contradictions

None between this brief and the Dashboards block in `DESIGN.md`.

## Known problems outside done evidence

`importDashboard` now returns `ImportResult` instead of `Dashboard`; callers under `src/routes/dashboards/` still expect the old signature until units 5-04/5-05 (intentional parallel work, not fixed here).
