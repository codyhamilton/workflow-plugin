# Execution report: 4-03 — Conversations usage and cost distribution

**Status:** done

## What changed

- **`types.ts`**: Extended `Conversations` row with `model`, `model_calls`, `unpriced_calls`, `cost_usd`, `tokens_in`, `tokens_out` (score-series and executions types unchanged).
- **`conversations/+page.svelte`**: Added `model` (drill button) and formatted `cost` columns; fetches `analytics/distribution` with `measure=cost_usd` and `grain=conversation` via `view.paramsFor('rest')`; renders the `"all"` row with `DistributionChart` (`conversations-distribution`).
- **`conversations.spec.ts`**: Tests for c5 model/cost, distribution request params, model drill narrowing rows; virtual-scroll stub rows include usage fields.

## Check output

**Before** (`E2E_PORT=4415 npx playwright test tests/e2e/conversations.spec.ts`):

```
9 passed (17.3s)
```

**After:**

```
12 passed (19.5s)
```

New cases: c5 model/cost, distribution `grain=conversation&measure=cost_usd`, model chip + single visible row; all prior paging/virtualisation/error tests pass.

## Departures

None.

## Contradictions

None between this brief and cited DESIGN / API contracts.

## Known problems

None found in done-evidence scope.
