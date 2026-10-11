# Report: 5-08 — Dashboards route: grid, export, import

Status: **done**

## What changed (against each part of the brief)

- `src/routes/dashboards/+page.svelte` (new). Lists dashboards (`dash-item` buttons, `aria-pressed` on the selected one), a create form (`dash-name` + `dash-create`), and for the selected dashboard an add control (`dash-add-select` of saved views + `dash-add`), a reorder/remove grid, `dash-delete`, `dash-export`, and an import section (`dash-import-file` file input, `dash-import-text` textarea, `dash-import` button, `dash-import-error`).
- Tiles: each `viewIds` entry renders a `dash-tile` wrapper holding `dash-tile-up`/`dash-tile-down`/`dash-tile-remove` and an `<iframe>` with `src = url + (url.includes('?') ? '&' : '?') + 'embed=1'`, `loading="lazy"`, `title` = view name. `tileSrc` validates with `new URL(v.url, location.origin)` and returns `''` (rendering a fallback, no iframe) when the origin differs.
- Grid: CSS grid, one column, two at `min-width: 1024px`; fixed tile height 360 px. Cap of `MAX_TILES = 12`: `dash-add` disabled and a `role="status"` notice ("Each tile is a full page; more than 12 is slow.") shown at the cap.
- Reactivity: `store.listDashboards()`/`listViews()` held in `$state`, refreshed by `store.subscribe` inside `$effect` (teardown unsubscribes). Selected id is `page.url.searchParams.get('d')`; `select()` writes it via `view.setParam('d', id)`, so a reload keeps it.
- Export: `store.exportDashboard(id)` → `Blob` → anchor click downloading `<name>.json`.
- Import: `store.importDashboard(text)` for both the file and textarea paths; `ImportError`/`Error` message is captured into `importError` and shown (never thrown).
- `tests/e2e/dashboards.spec.ts` (new). Two tests: build (save two views from `/hooks?range=7d` and `/hooks?range=30d` via the 5-06 controls, create `daily`, add both, assert the first tile's iframe shows `hooks-harness[data-ready=true]`, reload keeps dashboard + tiles, reorder swaps iframe titles, remove leaves one, export reads `version` 1 / `name` / the remaining view name + url, import into a second `browser.newContext()` sees the dashboard and tile); malformed JSON shows `dash-import-error` and creates nothing.

## Check output

Before (route temporarily absent, spec present; `E2E_PORT=4508 npm run test:e2e -- dashboards.spec.ts`):

```
Error: locator.fill: Test timeout of 30000ms exceeded.
  - waiting for getByTestId('dash-name')          dashboards.spec.ts:18
  - waiting for getByTestId('dash-import-text')   dashboards.spec.ts:83
2 failed (2 failed)
```

After (same command):

```
Running 2 tests using 1 worker
  ✓ tests/e2e/dashboards.spec.ts:5:1 › a dashboard is built, persists, reorders, exports and imports (1.8s)
  ✓ tests/e2e/dashboards.spec.ts:80:1 › a malformed import shows the error and creates nothing (167ms)
  2 passed (13.6s)
```

`npm test`: `Test Files 15 passed (15) / Tests 152 passed (152)`. `npm run build`: exit 0, `✓ built in 7.60s` / `Wrote site to "build" ✔ done` (only the pre-existing chunk-size warning).

## Deviations

1. **View selection via `view.setParam('d', …)`** (the shared URL mutator from `src/lib/view.svelte.ts`) rather than a page-local helper. It clones the current query and calls `goto`; it touches no other file and matches the app's one-URL-state convention.
2. **Reorder test uses two views** (`hooks-7d`, `hooks-30d`): the brief says "reorder two tiles", which needs two tiles; the two views are saved from the 5-06 control as required.
3. **One `dash-import-error` for both import paths.** The contract names a single `dash-import-error`; the file input and textarea share the message state.
4. **Tile controls live inside the `dash-tile` wrapper.** Keeps `dash-tile` a per-tile element; the contract lists per-tile ids but not their nesting.

## Contradictions

None material. The brief's "import that JSON … and see the same dashboard and tiles" is read as the exported set (one tile, after the remove step), which is what the export contains.

## Unfinished

None.

## Known problems

- The tile `<iframe>` for a url the store cannot have produced (off-origin) renders a fallback paragraph instead of an iframe; the store/import guard (`isValidViewUrl`) means this is unreachable in practice.
- No non-trivial bug found outside the done evidence.
