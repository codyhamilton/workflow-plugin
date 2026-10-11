---
# 5-17 — Phase 5 end-to-end proof and 1 s timing

Status: done with concerns

## What changed

- `packages/workflow-analytics/tests/e2e/phase5.spec.ts` (new, 291 lines) — one independent spec with seven tests, each `useServe(page, 'local')`, `test.use({ timezoneId: 'UTC' })`:
  1. small multiples: `cost_usd` × `model` × `harness`, bucket `day` → `builder-chart` `data-kind="multiples"`; panel count and panel `h4` titles derived from a live `/v1/analytics/query?measure=cost_usd&dim=harness` request, not a literal.
  2. heatmap: dims `hour_of_day`/`weekday`, bucket `none`, type `heatmap` → `data-kind="heatmap"`; table cells sum to the measure's API total over the same window.
  3. no unsupported pairing: loops every `/v1/analytics/schema` measure and asserts `builder-dim-1/-2` options equal the measure dims (+`none`) and `builder-chart-type` equals `allowedCharts(dims, bucket)` at 0, 1 and 2 dims.
  4. save `Cost split` via `saveview-*`, create `Ops` and add it via `dash-*`, reload → dashboard + tile persist; tile iframe shows `builder-chart`.
  5. export `Ops` (download → JSON), import into a fresh `browser.newContext()` via `dash-import-file`; dashboard + tile present and rendering.
  6. sankey: `exec-link-commit-report` leaves only `complete` rows; second click restores.
  7. timing: five interactions measured input→`expectSettled` (dashboard create-and-add to tile visible) each `< 1000 ms`; each value `console.log`ged.
- No `fixture.ts`/`helpers.ts` change: the append-only allowance was unused because the fixture already carries two harnesses with cost rows (`claude`, `opencode`), so no second-harness fact was needed.
- No tracked file outside the new spec was touched (`git diff --stat` empty; only the new spec and the pre-existing untracked `node_modules` show in `git status`).

## Evidence

BEFORE (before writing the spec):
```
E2E_PORT=4517 npm run test:e2e -- phase5.spec.ts
Error: No tests found.
Make sure that arguments are regular expressions matching test files.
```

AFTER — `E2E_PORT=4517 npm run test:e2e -- phase5.spec.ts`, three runs, `7 passed` each:
```
Run 1  builder-chart-type 25.8 ms | builder-measure 114.6 ms | dashboard-create-add 71.9 ms | executions-link 28.4 ms | builder-preset-7d 152.1 ms
Run 2  builder-chart-type 24.9 ms | builder-measure 115.8 ms | dashboard-create-add 73.0 ms | executions-link 31.1 ms | builder-preset-7d 150.6 ms
Run 3  builder-chart-type 25.2 ms | builder-measure 115.4 ms | dashboard-create-add 70.2 ms | executions-link 35.5 ms | builder-preset-7d 147.7 ms
```
- Full suite `E2E_PORT=4517 npm run test:e2e` → `125 passed` (1.5m).
- `npm test` → `161 passed` (15 files).
- `npm run build` → succeeded, wrote site to `build`.
- The 1 s assertion holds on the fixture only. The large-ledger figures are measured by the orchestrator against `/var/tmp/p4verify/data/local`.

## Deviations

1. Test 7(c) "dashboard create-and-add to `expectSettled`" is not possible: `/dashboards` has no `[data-ready]` element (tiles are iframes), so it is measured from the click to the `dash-tile` appearing instead.
2. Test 7(a)/(b)/(e) harden the settle wait beyond `interactions.spec.ts`'s exact code — awaiting the `data-kind` change, the changed `measure=...` response, or a differing query URL — so `expectSettled` cannot resolve on the stale pre-refetch chart. The measurement endpoints stay as the brief states (input → `expectSettled`).
3. `measureTotal` uses the builder's default 30 d window (`presetWindow('30d', …)`), not `all=1`, because the builder does not send `all=1` at bucket `none`. Verified in source and by review.

## Contradictions

- Test 6 (sankey link filter) duplicates `executions.spec.ts`'s existing coverage, while the brief also says "do not repeat, compose". It is included because the Changes list names it explicitly.
- DESIGN.md lists 5-17 as depending on 5-18/5-19/5-20, which do not appear in DESIGN's Phase 5 unit list (document gap; the units exist as reports).
- The brief's test-3 wording says the dim options equal "the measure's `dims`"; the contract prefixes a `none` option, so it is asserted as `['none', ...dims]`.

## Unfinished / known limitations

- None unfinished.
- The timing measurement has a sub-ms residual: for re-query cases a response can arrive one event-loop turn before Svelte applies it, so `expectSettled` could in principle observe the previous `ready=true`. The network round-trip is now inside the measurement, so the old gross under-measurement is gone, but the proof is not airtight.
- The small-multiples panel set is derived from an all-time API query while the builder uses its 30 d window; equal on this fixture, but a harness outside the window would diverge for a window reason, not a chart defect.
- `tests/e2e/phase5.spec.ts` imports `allowedCharts`/`presetWindow` from app source (new coupling in the e2e suite; safe today, imports are dependency-light).
---
