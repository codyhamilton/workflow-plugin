---
cursor:
  subagentId: "bc-339da0b2-a075-5da1-a1f4-9d56d230d47f"
---

# Report: 5-02 — Investigation shell and landing handoff

**Status:** done

## What changed

- `+page.svelte`: branches on `isInvestigationQuery`; landing vs `InvestigationShell`.
- `src/lib/investigation/LandingView.svelte`: phase 4 landing trends plus `landing-open-investigation` → `investigationRequestToSearch` for `{ tz }`, `hook_events` / `day`.
- `src/lib/investigation/InvestigationShell.svelte`: URL parse/sync, presets, dim selector, `aggregate` (serial primary + companion `cost_usd`), trend/breakdown chart frame, brush, drill/shift-exclude, `notice-ignored`.
- Supporting modules: `request-mutate.ts`, `dims.ts`, `frames.ts`, `request-mutate.test.ts`.
- `tests/e2e/investigation-shell.spec.ts`: landing handoff, preset, drill, shift-exclude, URL paste.

## Checks

**Before**

- `npx playwright test tests/e2e/overview.spec.ts`: 2 passed (after `npx playwright install chromium`; initial run failed missing browser).
- `npx playwright test tests/e2e/investigation-shell.spec.ts`: 3 failed, 2 passed (no shell; missing charts / timeouts).
- `npm test`: 243 passed.

**After**

- `npx playwright test tests/e2e/overview.spec.ts`: 2 passed.
- `npx playwright test tests/e2e/investigation-shell.spec.ts`: 5 passed.
- `npm test`: 244 passed.

## Departures

- E2E `__other__` non-filter: covered in `request-mutate.test.ts` (no stable `__other__` bar in harness fixture); harness include drill still in e2e.
- Preset clicks scoped to `investigation-shell` because layout `FilterBar` also exposes `preset-*` test ids.

## Contradictions

None between this brief and cited DESIGN / design 7 contracts.

## Problems

None found outside done evidence.
