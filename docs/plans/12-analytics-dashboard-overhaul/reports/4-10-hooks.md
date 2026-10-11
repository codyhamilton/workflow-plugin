# 4-10 — Hooks: four bars, two linked treemaps, drill-down

Status: **done with concerns**

## What changed

- `packages/workflow-analytics/src/routes/hooks/+page.svelte` (rewritten): reads `view` only. Four `BarChart`s `hooks-harness|repo_id|event|tool` (`measure=hook_events`, `dim=<d>`, `bucket=none`, `top=20`) and two `Treemap`s `hooks-treemap-a` (`harness`→`norm_event`) and `hooks-treemap-b` (`norm_event`→`tool`). Six `getJSON` calls on one view change, gated on `view.facets`; charts mount only once all six requests settle. Bar click → `view.drill(dim, key, {shift})`; treemap leaf → a chip per path level (`__other__` paths ignored), the tail applied after the first navigation lands. The empty tool key is `label()`ed to `(none)` and drills with `''`. `kind` needs no handling: the client's notice covers `ignored_filters`.
- `packages/workflow-analytics/tests/e2e/hooks.spec.ts` (rewritten): 8 tests — per-bar table equals the recounted fixture (`HOOKS_BY_HARNESS|REPO|EVENT|TOOL`), six `/query` requests per load (`trackRequests`), include chip + narrowed `repo_id` bar, shift exclude chip + bar omits it, <1 s click→`expectSettled`, treemap A leaf adds two chips, `__other__` leaf inert via `page.route`, and `?range=7d` persisting Overview → Hooks.

## Check output

Before (brief step 1, old `hooks.spec.ts` run against the new page): **2 failed, 0 passed** — both error `getByTestId('hooks-event-PreToolUse')` (and `hooks-*-*`) element not found: the table view is now 4-04's `DataTable`, which allows no row-id prefix, so the old `hooks-<g>-<k>` / `hooks-<g>-row-<k>` ids are gone.

After (measured, `E2E_PORT=4410`):

- `npm test` → `Test Files 11 passed (11) / Tests 76 passed (76)`.
- `npm run build` → exit 0 (`✓ built`, `Wrote site to "build"`).
- `E2E_PORT=4410 npm run test:e2e -- hooks.spec.ts` → `8 passed (22.7s)`; the six-request test reports `6`.

## Deviations

1. **Two two-level treemaps, not one three-level tree.** `/query` caps `dim` at two, so the design's `harness → norm_event → tool` tree is A (`harness`→`norm_event`) + B (`norm_event`→`tool`). The brief asks for this and to report it.
2. **Spec uses a local `clickHarnessBar`, not `helpers.clickBar`.** See the bug below; the brief names `clickBar`, but it cannot select anything under 4-04's conditional `DataTable`.
3. **Charts mount only after all six requests settle** (a `loaded` flag). Without it, `BarChart` reports `data-ready` while still empty, so `expectSettled` passed before any request had fired (observed: `trackRequests` = 0, tables `{}`).
4. **Bar/table order is key-ascending**, not value-descending: `sortRows` sorts by `strings.Join(K,"\x00")`, so harness rows are `claude, cursor, opencode` and the shift test uses index 2.

## Contradictions

- The brief says `clickBar(page, 'hooks-harness', 0)` adds a chip, and cites 4-04's `DataTable` as the row-id source. `clickBar` (a) toggles the BarChart into table mode to read row count, then (b) clicks bar geometry — but BarChart's `{#if showTable} DataTable {:else} EChart` has already unmounted the chart, so the click has no mark to hit. Named, not silently worked around; the spec exercises the same select path via the ECharts mark instead.

## Known problems (not fixed here)

- **Bug: `helpers.ts` `clickBar` cannot click a `BarChart`.** Symptom: `clickBar` clicks toggle the harness chart to the table view, then the geometry click lands on the table header (index 0) and selects nothing; with the table pre-shown it is off by one, and for wider tables the band centres do not align with `<tr>`s. Location: `packages/workflow-analytics/tests/e2e/helpers.ts:58-73` (used by no spec until now). Root cause: the helper assumes the table is present *alongside* the chart while BarChart renders them as alternatives; the y geometry is the ECharts grid, not the table layout. Out of this unit's owned paths.

## Unfinished

None.
