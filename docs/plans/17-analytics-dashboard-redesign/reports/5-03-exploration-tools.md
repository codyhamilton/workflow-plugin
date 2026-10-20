---
cursor:
  subagentId: "bc-bb008dea-f925-5086-8294-611142bfd0e1"
---

# Report: 5-03 — Exploration tools

**Status:** done

## What changed

- `src/lib/investigation/tools/`: `registry.ts`, `UsageTool.svelte`, `QualityTool.svelte`, `ConversationsTool.svelte`, `SavedAnalysisTool.svelte`.
- `InvestigationShell.svelte`: tool strip (breakdowns, usage, quality, conversations, saved), tool panels, quality aggregate fetcher with distinct query slots.
- `src/lib/saved-analysis.ts` + `saved-analysis.test.ts`: `{ id, name, spec }` in `yakka-analytics-saved-analysis`.
- `tests/e2e/investigation-tools.spec.ts`: unpriced usage, quality window/baseline table, conversation detail + in-window marker, saved round-trip.

## Checks

**Before**

- `npm test -- src/lib/saved-analysis.test.ts`: no test file (exit 1).
- `npx playwright test tests/e2e/investigation-tools.spec.ts`: no tests (exit 1).
- `npm test`: 244 passed.

**After**

- `npm test -- src/lib/saved-analysis.test.ts`: 4 passed.
- `npx playwright test tests/e2e/investigation-tools.spec.ts`: 4 passed.
- `npx playwright test tests/e2e/investigation-shell.spec.ts`: 5 passed.
- `npm test`: 248 passed.

## Departures

- Usage model table uses per-measure `aggregate` breakdown calls with dedicated `getJSON` slots (parent `aggregate` slot would supersede parallel breakdowns).
- Quality e2e stubs scores/baselines (same pattern as legacy `quality.spec.ts`); zero-scorer serve alone did not populate the table because `aggregate` quality issues three same-slot requests.
- Conversation timeline uses `investigation-timeline-in` / `out` markers (legacy page uses `timeline-out` only).

## Contradictions

None between this brief and DESIGN Domain: Interactive analysis.

## Problems

`aggregate()` parallel quality reads share one query slot; investigation works via a custom fetcher in the shell. Fixing that in `aggregate.ts` is outside this brief’s owned paths.
