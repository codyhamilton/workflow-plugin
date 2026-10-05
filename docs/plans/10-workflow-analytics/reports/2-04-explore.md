# Report: 2-04 explore pivot (Perspective)

Status: done.

## Done against the brief

- `packages/workflow-analytics/src/routes/explore/+page.svelte`: on mount it dynamically imports `@perspective-dev/client`, `viewer`, `viewer-datagrid` and the viewer themes CSS, initialises the server and viewer WASM (`?url` imports of `@perspective-dev/server/dist/wasm/perspective-server.wasm` and `viewer/dist/wasm/perspective-viewer.wasm`), creates a table with an explicit schema (14 columns; all `string` except `ts`, `datetime`, parsed from RFC3339), and loads it into `<perspective-viewer>` (datagrid default). One `GET /v1/analytics/explore` with the shared filter; a filter change calls `table.replace` with the new rows, no reload. Missing fields become `''`.
- `data-testid="explore-count"` shows the loaded row count; `data-testid="explore-truncated"` banner appears only when `truncated` is true, stating the slice is capped at the returned count, newest first, and to narrow the window or filters.
- Viewer fills the width at `min-height: 36rem`, `height: 70vh`; no custom pivot UI.
- `tests/e2e/explore.spec.ts` (4 tests): viewer present, count and `getTable().size()` equal 17 (fixture hook events + artifact versions + commits + rejections), no truncated banner; `repo_id=r1` gives 12 (table size too) and survives reload; a `page.route` stub of three rows with `truncated: true` shows the banner and count 3; loading `/` makes no request containing `perspective` or ending `.wasm`.
- `vite.config.ts` unchanged: 2-01's config already builds and runs Perspective.

## Check output

- Before (spec written first, no route): `npm run test:e2e -- explore.spec.ts` gave 3 failed, 1 passed (the overview no-Perspective test passes trivially without the route; the other three failed with elements not found).
- After: 4 passed. `npm run build` ok; `E2E_FORBIDDEN=e2e-dummy-xyz npm run check:bundle` gives `check-bundle: ok (79 files, 1 forbidden values)`. Whole `npm run test:e2e`: 26 passed.

## Departures

None. The brief's rubric of "explore-count equals fact count plus rejection count" is computed from `SUMMARY_ALL` (no new fixture export, since `fixture.ts` is off-limits).

## Problems and notes

- The `repo_id=r1` count (12) excludes the one precheck rejection because of the phase-1 store quirk already reported in 2-01 (rejections drop out of any repo or harness filter). The spec asserts that behavior via `SUMMARY_R1`.
- `@perspective-dev/server` is imported by path but is not a direct dependency in `package.json`; it resolves as a transitive dependency of `client`. If a later install changes that, add it explicitly (not done here: `package.json` is not owned by this unit).
- The build prints a Vite warning about an unused `d3-shape` import from LayerChart; not from this unit.

## Unfinished

Nothing.
