# 4-16 — Retire LayerChart and the old filter model; cross-route interaction tests

Status: `done with concerns`.

## What changed

**Old chart stack and filter model retired.**
- Deleted `src/lib/charts/Bars.svelte`, `src/lib/charts/LineSeries.svelte`, `src/lib/charts/palette.ts` (only the two deleted charts imported palette).
- Deleted `src/lib/series.ts` and `src/lib/series.test.ts` (only `LineSeries.svelte` imported `fillBuckets`).
- `npm uninstall layerchart` from `packages/workflow-analytics`; `grep -n layerchart package.json package-lock.json` → no output.
- Kept `src/lib/filters.ts` + `filters.test.ts`: still imported by unowned `src/routes/quality/+page.svelte`, `src/lib/components/FilterBar.svelte`, `src/lib/types.ts`, `src/lib/urlstate.ts`. After removal, `grep -rn "layerchart|\$lib/filters|\$lib/series|charts/Bars|charts/LineSeries|charts/palette" src tests` returns only the two `$lib/filters` imports above.

**`helpers.ts` `clickBar` fixed (Amendment).** Rewritten to match `clickHarnessBar` in `hooks.spec.ts`: read the row count from `<testid>-table`, toggle back to the chart, wait for `.echart svg`, then click the band centre. Signature unchanged.

**`tests/e2e/interactions.spec.ts` (new, 8 tests), one per Phase 4 outcome bullet:**
1. `7d` on Overview → Hooks nav → `range=7d`, `preset-7d` pressed.
2. `brush(page,'trends-chart',0.25,0.75)` → `from`/`to` present, `range` absent, table shows fewer buckets.
3. `clickBar(page,'hooks-harness',0)` → `chip-harness-claude` include; `{shift:true}` → exclude.
4. `/conversations` `c5` link → `/conversation?id=c5` totals equal `USAGE_C5`.
5. `/usage` cost-by-model + no `$0` on the unpriced-only window (`/usage?harness=claude`).
6. preset click, harness drill, brush each settle under 1,000 ms (`performance.now()`).
7. five preset clicks inside 250 ms → one `/analytics/query` on `/trends`; `/repos` = 4 requests with two repos and 4 with forty (a `page.route` inventing rows).
8. `[data-testid$="-table-toggle"]` on `/`, `/trends`, `/usage`, `/repos`, `/hooks`: every chart `data-ready="true"` and every toggle reveals a `-table` with ≥1 row, light and dark (`emulateMedia`).

## Done evidence

| Check | Before | After |
|---|---|---|
| `grep -n layerchart package.json package-lock.json` | `package.json:38`, lockfile dep + `node_modules/layerchart` | no output |
| `npm test` (vitest) | 11 files / 74 tests | 10 files / 73 tests (`series.test.ts` removed), pass |
| `npm run build` | pass | pass |
| `npm run test:e2e` | 76 pass, 2 fail | **84 pass, 0 fail (1.5m)** |
| `npm run check:bundle` | pass | `check-bundle: ok (66 files, 0 forbidden values)`; also runs inside `e2e-build.mjs` before the suite |

`interactions.spec.ts` 8/8 pass; `/settings`, the non-JSON error path, Perspective (Explore only), `scripts/check-bundle.mjs` and the static build are untouched.

## Departures from the brief

1. **Edited `tests/e2e/usage.spec.ts` (not an owned path).** See contradiction 1. Changed `SONNET_BAR` from `1` to `0` and its comment. One line plus comment; no other change.
2. The brush test polls the table row count instead of using `expectSettled` after the brush: `expectSettled` passes on the stale `data-ready="true"` before the refetch lands (the 4-07 note), which read the pre-brush count. Behaviour asserted is still "the table toggle shows fewer buckets".

## Contradictions named

1. **Amendment vs. "keep the existing suite passing" / owned paths.** The Amendment mandates `clickBar` click the real ECharts band centre (0-based; hooks index 0 = `claude`). `usage.spec.ts`'s `SONNET_BAR = 1` was calibrated to the *old, broken* helper (its comment said "index is row + 1"), where clicking happened over the table. The fixed helper made bar 1 the unpriced opus bar → no chip. `usage.spec.ts` is not owned. Resolved by the minimal `SONNET_BAR = 1 → 0` edit, since a green suite and the mandated fix cannot both hold otherwise.
2. **Bullet 5 wording.** "no element on a window with only unpriced calls contains `$0`" is asserted via `/usage?harness=claude` (the unpriced-only window from 4-08), not a bespoke window; matches the existing `usage.spec.ts` precedent.

## Known problems / unfinished

- **None for this unit.** All 8 bullets are asserted and green.
- Carried from earlier units, out of scope here, not fixed: `notice-ignored`/`notice-partial` self-clear (4-05 `+layout.svelte` / `state.svelte.ts`); `query.ts` supersede path can drop a shared in-flight entry for same-key joiners (4-09); `costLabel` can emit `$0.00` for a priced-but-zero call when `unpriced < calls` (4-06/usage) — not reachable in the fixture.
