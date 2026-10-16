# Report: 1-01 — Solarized shell

Status: `done`

## What changed

- `theme.css`: Solarized light/dark tokens on `:root` / `[data-theme='dark']`, shared accent, danger, series palette, and space scale variables.
- `theme.ts`: `DEFAULT_TOKENS` matches the light contract; `THEME_KEY`, preference read/write, `applyTheme` / `initTheme`, and `watchScheme` now also listens for `data-theme` mutations.
- `+layout.svelte`: inline head script for first-paint `data-theme`, client `initTheme`, System/Light/Dark controls (`data-testid` `theme-system` / `theme-light` / `theme-dark`), shell padding/gaps on the space scale, error panel on contract tokens only.
- Owned route/chart Svelte `<style>` blocks: hex and `var(..., #fallback)` replaced with theme variables.
- `theme.test.ts`: assertion that `DEFAULT_TOKENS` equals the light contract.
- `shell.spec.ts`: e2e coverage for system-dark tokens on `/` and `/settings`, Light without reload + reload persistence, and System following emulated OS scheme changes.

## Done evidence

### `npm test -- src/lib/charts/theme.test.ts` (packages/workflow-analytics)

Before (prior to solarized tokens; no `DEFAULT_TOKENS` contract test):

```
 ✓ src/lib/charts/theme.test.ts (6 tests)
 Test Files  1 passed (1)
```

After adding the contract test against old `DEFAULT_TOKENS` (would fail until token update): expected `#fdf6e3`, received `#ffffff`.

After implementation:

```
 ✓ src/lib/charts/theme.test.ts (7 tests)
 Test Files  1 passed (1)
```

### Hex scan — `<style>` blocks in `src/**/*.svelte`

Before: hex colours in owned files (e.g. `+layout.svelte` error panel, overview/executions tiles, chart wrappers with `#d1d5db` fallbacks, `FilterBar` `#fff`, etc.).

After (`rg '#[0-9a-fA-F]{3,8}' src --glob '*.svelte'` — matches are Svelte `#each` only, no colour literals):

```
(no colour hex matches)
```

### `npx playwright test tests/e2e/shell.spec.ts`

Before (new theme tests absent; existing suite):

```
 12 passed (prior run count before new tests)
```

After:

```
 13 passed (18.9s)
```

Includes passing: existing dark-scheme swap test; system dark solarized tokens on `/` and `/settings`; Light without reload and after reload; System following emulated scheme change.

## Departures

- **`+layout.svelte` inline head script**: Duplicates preference resolution so `data-theme` is set before hydration. `app.html` is outside owned paths; without an early script, Playwright (and users on system-dark) saw light tokens until the layout effect ran.

## Contradictions

- **Owned paths vs hex scan outcome**: Done evidence requires no hex in any `src/**/*.svelte` `<style>`, while the brief limits edits to listed owned paths. Non-owned Svelte files had no stylesheet hex in this tree; only owned files required edits. No silent resolution needed beyond that fact.

## Known problems

None identified within this brief's scope.
