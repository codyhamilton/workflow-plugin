---
cursor:
  subagentId: "bc-10682fdb-8eab-571a-9f73-4246b7b5b6eb"
---

# Report: 2-01 — Analysis shell and tokens

**Status:** done with concerns

## What changed

- Added `packages/yakka-analytics/src/lib/analysis/` (`tokens.css`, route helpers, `RouteSurface`, `IdentityPanel`, `index.ts` exports).
- Document root uses non-solarized analysis tokens; legacy report paths scope solarized vars via `[data-legacy-theme]` in `theme.css`.
- `+layout.svelte` wraps legacy report chrome in `RouteSurface`; header/nav/theme controls use analysis tokens.
- Identity routes (`/login`, `/profile`, `/settings`, `/device`, `/oauth/callback`) restyled with analysis tokens and `IdentityPanel`.
- E2E: new `analysis-shell.spec.ts`; `shell.spec.ts` theme expectations updated for analysis vs legacy.
- `docs/design/07-analytics-site.md` Theme paragraph documents the analysis system and legacy scope.

## Checks

**Before**

- `npm run test:e2e -- tests/e2e/analysis-shell.spec.ts`: 1 failed (`/` `--bg` was `#fdf6e3`; browser install required on first run).
- `npm test`: 205 passed (unchanged baseline).

**After**

- `npm run test:e2e -- tests/e2e/analysis-shell.spec.ts`: 2 passed.
- `npm run test:e2e -- tests/e2e/analysis-shell.spec.ts tests/e2e/session.spec.ts tests/e2e/shell.spec.ts`: 25 passed, 2 failed (`dashboards shares…` trends chart visibility; `ignored-filter notice` on `/trends`). Same two failures on a clean checkout of this branch without these edits (environment/trends load, not introduced here).
- `npm test`: 205 passed.

## Departures

None.

## Contradictions

None with DESIGN.md phase 2 outcome or component/style contract.

## Problems

Two `shell.spec.ts` cases that hit `/trends` fail in this VM even on the pre-change tree; session gate and analysis-shell suites pass. Worth re-running full e2e where the serve fixture is known healthy.
