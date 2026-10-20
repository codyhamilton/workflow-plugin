---
cursor:
  subagentId: "bc-1b14c646-4a16-538d-b77b-ca702b1c6eee"
---

# Report: 5-04 — Legacy routes and shell retirement

**Status:** done

## What changed

- `+layout.svelte`: report nav, `FilterBar`, `FilterChips`, `SaveView`, and legacy `RouteSurface` solarized branch removed; shell nav is Overview, Profile, Settings with `Notices` only on chrome routes.
- `routes.ts`: `LEGACY_REPORT_PREFIXES` emptied so investigation uses analysis tokens everywhere.
- Eleven legacy `+page.svelte` routes replaced with a retirement stub (`legacy-route-stub`) — URLs stay for session-gate tests; old report UI not mounted.
- `helpers.ts`: `useServe` passes a flat `addInitScript` arg list (fixes nested-array local base bug).
- Owned e2e: retired legacy UI specs; `shell.spec.ts` rewritten for new chrome; `explore.spec.ts` asserts stub + no Perspective; deleted `phase5.spec.ts`.
- `docs/design/07-analytics-site.md`: route table, theme, investigation URL state, saved-analysis `localStorage`, retirement of builder/dashboard/explore paragraphs.

## Checks

**Before**

- `npx playwright test tests/e2e/investigation-shell.spec.ts tests/e2e/investigation-tools.spec.ts tests/e2e/overview.spec.ts tests/e2e/session.spec.ts`: 21 passed.
- `npx playwright test tests/e2e/explore.spec.ts`: 4 failed (legacy explore UI / `useServe` nested args).
- `npm test`: 248 passed.

**After**

- Same investigation/overview/session bundle: 21 passed.
- `npx playwright test tests/e2e/explore.spec.ts`: 2 passed.
- Full owned retirement bundle (above + shell, trends, usage, repos, quality, conversations, conversation, dashboards): 38 passed.
- `npm test`: 248 passed.
- `git diff --name-only` vs parent: no paths under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

## Departures

- Legacy routes use an on-path stub instead of `goto('/')` so `session.spec.ts` can keep asserting stay-on-route behavior for `/trends` and `/usage`.
- `interactions.spec.ts`, `filter-bar.spec.ts`, `builder.spec.ts`, and other non-owned e2e files still target retired UI; not rewritten (outside owned paths). Full `test:e2e` is not part of done evidence.

## Contradictions

None between this brief and DESIGN Phase 5 outcome or Assumption 2 (no explore/dashboard return).

## Problems

Non-owned e2e (`interactions.spec.ts`, `filter-bar.spec.ts`, etc.) will fail against the retired shell if run wholesale; root cause is scope — those specs were not in this brief’s owned list.
