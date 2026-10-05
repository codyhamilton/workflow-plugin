# Report: 2-01 site shell, API client, filters, overview and settings

Status: done with concerns (one phase-1 quirk, below).

## Done against the brief

- `packages/workflow-analytics/`: SvelteKit 2 + Svelte 5 SPA built with `adapter-static` (`fallback: 'index.html'`, `ssr = false`, `prerender = false`, output `build/`), committed `package-lock.json`, package-local `.gitignore`, `"private": true`, MIT.
- `src/lib/api.ts` (`apiGet(path, params)`, `ApiError`; reads `localStorage` per call; `Authorization` only when a key is set), `types.ts` (all seven analytics routes and `/v1/baselines`), `filters.ts` (`parseFilter`, `filterParams`, `mergeQuery`, date helpers), `format.ts` (`label(key)`), `state.svelte.ts` (the shared fetch error).
- `FilterBar.svelte` in the root layout on every route but `/settings`: date inputs, multi-selects fed by `/facets` for the window, `""` hidden. `+layout.svelte`: nine nav links, an error panel (`data-testid="error-panel"`) with a `/settings` hint on 401 or a network error. `/` overview tiles with `data-testid="summary-<field>"`; `/settings` form (`settings-base`, `settings-key`, `settings-save`). No placeholder routes were created.
- E2E harness: `playwright.config.ts`, `tests/e2e/{global-setup,fixture,helpers}.ts`, specs `overview`, `settings`, `fixture`; `scripts/check-bundle.mjs`, `scripts/e2e-build.mjs`.

## Check output

- Before (tests written first): `npm test` failed (4 files, no tests: missing modules, e2e specs collected); `npm run test:e2e` failed (`Could not resolve entry module "index.html"`, no site yet).
- After: `npm ci && npm run build` writes `build/index.html`; `E2E_FORBIDDEN=... npm run check:bundle` prints `check-bundle: ok (21 files, 2 forbidden values)`, and fails (exit 1) when the forbidden value is a string the bundle does contain. `npm test`: 2 files, 7 tests pass. `npm run test:e2e`: 6 passed (fixture 1, overview 4, settings 1). `git status --porcelain` shows only `packages/workflow-analytics/` and the report as untracked, no `node_modules`, `build/`, `.svelte-kit/` or test output.
- `fixture.spec.ts` compares the fixture's executions, conversations and per-day / per-repo / per-harness / per-event / per-tool hook numbers with the live serve's answers, so 2-02..2-04 can trust those exports.

## Departures

1. The build and the bundle check run in the `webServer` command (`scripts/e2e-build.mjs`, then `vite preview`), not in global setup: Playwright starts `webServer` before `globalSetup`, and the preview needs `build/`. Same order the brief asks for (build, check, then preview). The key and a dummy token are generated in `playwright.config.ts` and passed to the build and the keyed serve through the environment.
2. Global setup clears `TYPESAFE_API_KEY` for both serves. With it set (as in this shell) serve sends the fixture to the real screening service and verdicts become `pass`; cleared, every verdict is `unscreened`, which the fixture's `screens` numbers assume.
3. Versions pinned to match "SvelteKit 2": `@sveltejs/kit@2.70.3` and `adapter-static@3.0.10`, with `vite@7.3.6`, `@sveltejs/vite-plugin-svelte@6.2.4`, `vitest@3.2.7`, `typescript@5.9.3`; latest majors of these exist (kit 3, vite 8, vitest 5, typescript 7) and were not used.
4. `vite.config.ts` restricts vitest to `src/**/*.test.ts` so it does not collect the Playwright specs.

## Contradictions and phase-1 quirk

- No contradiction between the brief and the contracts it cites. One phase-1 quirk: the store's `rejWhere` compares `repo_id` and `harness` against `''` for rejection rows, so any repo or harness filter drops precheck rejections to 0 (`SUMMARY_R1['rejections-precheck']` is 0). That is the phase-1 store's behavior, not a UI choice; DESIGN.md does not say a repo filter hides rejections. Not fixed here.

## Unfinished

Nothing in this unit. `svelte-check` is not installed; type checking is by vitest and the build only.
