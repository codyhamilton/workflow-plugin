# Execution report: 5-02 — Save view as chart config

**Status:** done

## What changed

- **`SaveView.svelte`:** Save uses `reportFromPathname` + `chartParamsFromQuery` and `store.saveView(name, report, params)`. Removed URL/`embed` handling. Menu links use `viewHref(v)`. On non-report routes (`/dashboards`, `/settings`, `/conversation`, etc.), save input/button are disabled and an inline hint is shown; the store is not called.
- **`shell.spec.ts` (save-view tests only):** Updated reload test so saved overview link is `/` (no window/filter query). Added `save view stores chart params only` asserting `localStorage` shape on `/trends` with mixed window/filter/chart query.

## Check output

**Before** (`export E2E_PORT=4422`; `npx playwright test tests/e2e/shell.spec.ts -g save` from `packages/workflow-analytics`):

```
1 failed
  shell.spec.ts:144 › a saved view is listed and survives a reload
  Error: expect(locator).toBeVisible() failed — saveview-item 'weekly' not found
  (saveView still passed legacy url string; store API expects report + params)
```

**After** (same command):

```
2 passed
  a saved view is listed and survives a reload
  save view stores chart params only
```

## Departures

- Renamed new test from “saving a view…” to “save view stores chart params only” so Playwright `-g save` includes it (pattern did not match “saving”).
- Disabled save controls plus hint on non-storable routes (brief allows disable or inline message).

## Contradictions

- Prior e2e expected saved link `href` to include `range=7d`; Phase 5 / view store contract says `params` are chart-only and `viewHref` omits window/filters. Updated the reload test to expect `href="/"`.
- Brief example mentions `/conversation`; app route is `/conversations` (`reportFromPathname` follows `REPORT_IDS`). No code change needed beyond existing null report handling.

## Known problems

None found within done evidence scope.
