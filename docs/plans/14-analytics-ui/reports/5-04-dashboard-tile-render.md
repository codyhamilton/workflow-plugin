# Execution report: 5-04 — In-document dashboard tiles

**Status:** done

## What changed

- Added `packages/workflow-analytics/src/lib/dashboard-tile.ts` with `tileExtraParams`, builder URL round-trip helpers, and hooks split parsing.
- Extended `view.svelte.ts` with `paramsForTile(route, report, tileParams)` — clears chart API keys, merges `tileExtraParams`, leaves window/shared filters from the dashboard URL.
- Added `packages/workflow-analytics/src/lib/components/DashboardTile.svelte`: props `view: SavedView`, optional `testid` suffix; root `data-testid="dash-tile-chart"`; switch on `view.report` mounting in-document charts (full hooks/builder/usage; primary chart for other contract reports). Drill/brush use `view.drill` / `view.setWindow`.
- Added `packages/workflow-analytics/src/lib/dashboard-tile.test.ts`.

Did not touch `dashboards/+page.svelte` (5-05), SaveView, or report routes per brief.

## Done evidence

**Before (no test file):**
```
No test files found, exiting with code 1
filter: src/lib/dashboard-tile.test.ts
```

**After:**
```
✓ src/lib/dashboard-tile.test.ts (3 tests) 5ms
Test Files  1 passed (1)
```

Hook/builder tile mount on a dashboard grid is left to 5-06 e2e (this unit has no harness for mounted tiles until 5-05 wires `<DashboardTile />`).

## Deviations

- Hooks bar/treemap fetches use `view.paramsFor` with explicit `dim` per chart, not `paramsForTile`, because stored hooks `dim` is the time-series split (`norm_event` | `tool`), not bar dimensions. Time series uses saved split/bucket via `hooksSplitFromTileParams` and `tileParams.bucket`.
- Non–hooks/builder/usage reports render a single primary visualization each (not every control/table from the full route) to keep the component bounded; they are not blank.

## Contradictions (not resolved here)

- Brief cites hooks mapping stored `dim` to split; full `/hooks` also reads `split` from the URL, while saved views store `dim` per `chartParamsFromQuery` — tile code follows the stored `dim` contract, not URL `split`.
- `SaveView.svelte` still calls `store.saveView(name, url)` and references `v.url`, while `views.ts` (5-01) defines `saveView(name, report, params)` and `SavedView` without `url`. Dashboard save/import is broken until a sibling unit fixes SaveView; out of scope for 5-04.

## Known problems (out of scope)

- `dashboards/+page.svelte` still embeds iframes; 5-05 must render `<DashboardTile />`.
- SaveView/store API mismatch (symptom: save view fails at runtime; location: `SaveView.svelte` vs `views.ts`).
