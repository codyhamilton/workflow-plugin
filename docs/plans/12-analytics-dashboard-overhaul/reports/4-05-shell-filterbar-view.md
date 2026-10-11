# 4-05 — Layout shell, FilterBar with presets and chips, and the `view` module routes share

Status: **done with concerns**

Concern: one existing spec (`overview.spec.ts:38`) fails on facets timing; see "Failure for the route units". It is not fixable inside this unit's owned paths.

## What changed

- `src/lib/view.svelte.ts` (new): one `view` object. `state` = `parseUrlState(page.url.searchParams)`; `tz`; `facets` loaded via `getJSON('facets','analytics/facets', …)` for the `rest` window in a module-level `$effect.root`, remapped `repos→repo_id, harnesses→harness, kinds→kind, plans→plan, events→event, models→model, norm_events→norm_event, tools[].name→tool`; `paramsFor(route, extra?)` → `apiParams`+`extra`, null on `pending`/`empty`; `empty`, `clamped`; mutators `setPreset/setWindow/drill/setInclude/removeChip/setParam`, each one `goto(..., {noScroll, keepFocus})` keeping route params via `toSearch(state, page.url.searchParams)`; a no-op guard so a repeated navigation adds no history.
- `src/lib/components/FilterBar.svelte`: preset group `preset-<id>` with `aria-pressed`; always-shown `filter-from`/`filter-to` applied as a `custom` window on change; multi-selects `filter-repo_id|harness|kind|plan|model` from `view.facets` (selected values kept visible), selection → `view.drill`, deselection → `view.removeChip`; all old test ids kept.
- `src/lib/components/FilterChips.svelte` (new): one chip per `chips(state)` entry, `chip-<key>-<value>`, `data-mode`, leading "not " on excludes, remove button `chip-remove-<key>-<value>` → `view.removeChip`; a `conversation_id` exclude chip is labelled "not applied".
- `src/lib/components/Notices.svelte` (new): `notice-ignored` per ignored filter name from `notices`, `notice-partial` when any slot is partial, `notice-clamped` when `view.clamped`, `notice-empty` when `view.empty`.
- `src/routes/+layout.svelte`: imports `$lib/theme.css`; nav adds Usage & cost `/usage` in the brief order and keeps the current search string on every link except Settings; FilterBar+chips+notices render everywhere except `/settings` and `/conversation`; `clearNotices()` added to the existing route/search `clearError()` effect; token-based body/header/main with wrapping nav; error panel markup, text and colours unchanged.
- `tests/e2e/shell.spec.ts` (new): 6 tests — preset survives navigation+reload, custom from/to, chip removal, 1024×768 no horizontal scroll, dark scheme swaps `--bg`, burst of five preset clicks → facets ≤ 2.

## Check output

Before (recorded baseline, not re-run: 4-01/4-02/4-04 reports): `npm test` 11 files / 76 tests pass; e2e 26 passed (4-03).

After (measured):

- `npm test` → `Test Files 11 passed (11) / Tests 76 passed (76)`.
- `npm run build` → exit 0 (`✓ built in 7.58s`, `Wrote site to "build"`).
- `E2E_PORT=4395 npm run test:e2e -- shell.spec.ts` → `6 passed (13.5s)`.
- `E2E_PORT=4396 npm run test:e2e` (full, 32 tests) → `31 passed`, `1 failed`.

## Failure for the route units

- `tests/e2e/overview.spec.ts:38` ("no filter control offers an empty option") reads `filter-repo_id` options right after the summary numbers render and gets 0. The old FilterBar fetched facets with un-debounced `apiGet`; the shell now loads them through `getJSON`, which the 4-01 client debounces 250 ms, so the selects are still empty at check time. The spec belongs to 4-06; once overview loads its summary through `getJSON` too, summary and facets settle together. Not fixable in 4-05 without editing the spec or `query.ts`, both out of owned paths.

## Deviations

1. `view.svelte.ts` uses getters over reactive `page`/`$state` plus a module-level `$effect.root`, not module-level `$derived` — same contract, avoids the module-scope `$derived` edge.
2. A facets failure sets `facets = null` and does **not** `setError`: the keyed-401 settings flow drives the layout's single error panel, and a background facets 401 must not overwrite it.
3. Multi-selects apply additions via `view.drill` (brief §2) and removals via `view.removeChip`; `view.setInclude` (one-navigation replace) is exported for route units.
4. Nav uses `var(--...)` tokens; the error panel keeps its original colours.

## Contradictions

- Brief §1 makes `empty`/`clamped` view fields while §2's date inputs are "shown always"; for `All time` (and any `all` window) there is no `from`/`to`, so the inputs show empty and the clamped notice covers the clamp. Named, not resolved silently.

## Known problems

- The red e2e spec above.
- If facets fail (401/network) the filter selects stay empty with no notice; the route's error panel is the only signal.

## Unfinished

None. No bug outside the done evidence was found.
