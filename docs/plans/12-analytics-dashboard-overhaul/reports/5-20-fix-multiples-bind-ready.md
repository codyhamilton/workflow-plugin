---
# 5-20 — Fix the small-multiples crash from 5-18's `bind:ready`

Status: done

## What changed

- `packages/workflow-analytics/src/lib/charts/SmallMultiples.svelte`: `panelReady` still starts `{}`; added an `$effect.pre` that seeds `false` for every current panel key before its `EChart` mounts. `bind:ready={panelReady[panel.key]}` and the `ready` derived are unchanged (`data-ready` still means "every current panel ready", `"true"` with zero panels).
  - Root cause confirmed in the installed svelte runtime: `EChart`'s `ready = $bindable(false)` has a fallback; when the bound value is `undefined` the client runtime throws `props_invalid_value` (`node_modules/svelte/src/internal/client/reactivity/props.js:325-331`, `.../errors.js:386`). `panelReady` began empty, so the first `EChart` mount bound `undefined` and the whole multiples subtree failed to render.
  - `panels` is re-derived in place on every query (`BuilderChart.svelte:69` spreads a fresh `multiplesLayout(resp!)`), so seeding runs on every key change, not just at init.
- `packages/workflow-analytics/src/lib/charts/multi.test.ts`: added an SSR test rendering two panels (asserts no throw, a `-panel` node, `data-ready="false"`). It does **not** catch the client binding bug — see Deviations.
- `tests/e2e/area.spec.ts`: unchanged; 5-19 already carries the multiples assertion.

## Evidence

BEFORE — `E2E_PORT=4520 npm run test:e2e -- area.spec.ts builder.spec.ts`:
```
2 failed
  tests/e2e/area.spec.ts:24 › multiples chart settles in the browser
  tests/e2e/builder.spec.ts:31 › cost_usd by model and harness on a day bucket renders small multiples
5 passed
```
Both failed at `builder-chart-panel` visibility ("element(s) not found") — the subtree never rendered.

AFTER — same command: `7 passed (12.1s)`.

- `npm test`: 15 files, 161 passed.
- `npm run build`: passed (`Wrote site to "build"`, `✔ done`), no warnings.
- `git diff --stat`: `SmallMultiples.svelte` +8, `multi.test.ts` +12.

## Deviations

1. Brief item 2 asks for a client-side mount test in `multi.test.ts`. Not achievable here: `vite.config.ts` sets no `test.environment` (Vitest defaults to `node`) and neither `jsdom` nor `happy-dom` is installed; adding one means editing `package.json`/`vite.config.ts`, outside the owned paths ("touch nothing else"). An SSR two-panel test was added instead, but SSR drops `bind:`, so it cannot observe the binding and the client bug is covered only by item 3's e2e — the brief's stated fallback.
2. The brief suggests "derive the record from `panels`". Implemented as an `$effect.pre` seed instead: the init-derivation form emitted a `state_referenced_locally` build warning and only captured the first `panels`, while panels are re-derived in place (`BuilderChart.svelte:69`) so later keys would re-introduce the crash.
3. `area.spec.ts` left untouched (item 3 is a pass-through of 5-19's assertion).

## Contradictions

- The brief says the failing assertion is 5-19's `expectSettled`. In practice both before-failures occur earlier, at the `builder-chart-panel` visibility check (`area.spec.ts:27`, `builder.spec.ts:38`); `expectSettled` is never reached. Same root cause; recorded, not resolved silently.

## Unfinished / known limitations

- None unfinished.
- A panel key removed then re-added keeps its stale `true` until its chart re-reports, so `data-ready` can flicker `true` briefly. Removed-panel keys are ignored by `ready`, so the final readiness set is correct.
---
