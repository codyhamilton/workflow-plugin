# Report: 3-01 — Filter bar ten dimensions

Status: `done`

## What changed

- `FilterBar.svelte`: Replaced the five-key `MULTIS` list with `{#each DIM_KEYS}`; extended `LABELS` for `norm_event`, `event`, `tool`, `source`, and `conversation_id`; added `filter-conversation_id-exclude-hint` (“Exclude not applied”) on the conversation control.
- `filter-bar.spec.ts` (new): E2e coverage for all ten `filter-<key>` test ids, harness selection updating the URL, and the conversation exclude hint.
- `view.svelte.ts` (`mapFacets`): No edit — existing mapping already maps `norm_events` → `norm_event`, `events` → `event`, and `tools` → `tool` (names).

## Done evidence

### `npx playwright test tests/e2e/filter-bar.spec.ts` (E2E_PORT=4391)

Before (spec absent):

```
Error: No tests found.
```

After:

```
  3 passed
```

### `npx playwright test tests/e2e/overview.spec.ts -g "no filter control offers an empty option"`

After:

```
  1 passed
```

## Departures

None.

## Contradictions

None between this brief and `DESIGN.md` / `urlstate.ts`.

## Other issues

None observed outside done evidence.
