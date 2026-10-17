# Execution report: 5-05 — Dashboard page grid and import notices

**Status:** done

## What changed

- Updated `packages/workflow-analytics/src/routes/dashboards/+page.svelte` only:
  - Removed `tileSrc`, iframes, and all `embed=1` / iframe copy.
  - Switched dashboard model from legacy `viewIds` to `selected.tiles` (`viewId`, `w`); move/remove/up/down still use store tile indices.
  - Renders each tile with `<DashboardTile view={…} />` inside `data-testid="dash-tile"`; `w === 2` spans both columns at `min-width: 1024px` via `.tile.span2 { grid-column: span 2 }`.
  - Cap notice copy: at most 12 tiles (not iframe performance); `atCap` from `selected.tiles.length`.
  - `importJson` uses `ImportResult`; when `tilesDropped` or `viewsDropped` > 0, shows `role="status"` notice with `data-testid="dash-import-drops"` and both counts.
  - Intro paragraph describes in-document tiles under one filter bar and window.

Did not touch store, `DashboardTile` internals, or e2e specs.

## Done evidence

**Gate (grep `iframe`|`embed` in `+page.svelte`) — before:**
```
6:	// Each tile is a full page in an iframe, so past this the dashboard gets slow.
36:	/** … frame it with `embed=1` … */
41:		return `${v.url}…embed=1`;
118:	<code>embed=1</code>, …
213:		<iframe class="frame" …></iframe>
```

**After:** no matches.

**`npm test -- src/lib/views.test.ts` — before:** 28 passed (63ms tests).

**After:** 28 passed (117ms tests).

Dashboard page is ready for **5-06** playable e2e; no e2e added here.

## Deviations

None.

## Contradictions (not resolved here)

- 5-04 report notes `SaveView.svelte` still calls `saveView(name, url)` while `views.ts` expects `saveView(name, report, params)` — saving views from the UI may still fail until a sibling unit aligns SaveView; this brief does not own SaveView.

## Known problems (out of scope)

None found in owned path during this unit.
