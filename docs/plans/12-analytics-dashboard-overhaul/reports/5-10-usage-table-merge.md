# Report: 5-10 — Usage table: one consistent key set

Status: **done**

## What changed
- The five usage-by-model-* slots (`usage-by-model-cost`, `-calls`, `-unpriced`, `-tokens-in`, `-tokens-out`) now request `top=100` instead of `top=20`, so all five ask for the same key set and the table can no longer merge mismatched model keys.
- `__other__` rows are labelled `other models`, marked inert (`tr.inert`, no drill on click), and cost() is guarded so a folded tail row with `unpriced < calls` reads `unpriced`, never `$0.00`.
- When the response contains `__other__`, a `usage-truncated-note` ("Table truncated to 100 models; \"other models\" folds the rest.") is shown after the table.
- The empty model key now renders `(none)` via `label()` and is inert; its row data-testid remains `usage-row-`.
- Per-measure cells use a new `cell(map, key)` helper: a genuinely absent key renders `—`, while a present key renders `num(...)` (including `0`).
- Banner totals (`usage-unpriced-banner`) are unchanged; `totalCalls`/`totalUnpriced` still sum over `models`.

## Check output
Before (STEP 2):
```
✘  13 tests/e2e/usage.spec.ts:185:1 › the five by-model table requests ask for top=100 (932ms)
  Error: cost_usd
  Expected: "100"
  Received: "20"
```

After (STEP 4):
```
14 passed (30.2s)
  ✓ 13 ... the five by-model table requests ask for top=100 (498ms)
  ✓ 14 ... empty model key shows (none) and is inert; __other__ shows other models with a truncation note (999ms)
```

`npm test`: 74 passed (10 files).
`npm run build`: ✓ built, adapter-static wrote "site" — pass.

## Deviations
1. Added the `cost()` guard because `costLabel` returns `$0.00` when `unpriced < calls` (format.ts is owned by 5-14, so the guard lives here).
2. Added a fourth test covering `(none)` / other-models / truncation-note / inertness (the brief listed four tests; this is the fourth).
3. If a model's calls count is `0` but the key is present, the calls cell now shows `0` (present key) — absent keys show `—`.

## Contradictions / observations
- The brief says the cost-by-model chart keeps `top=20`, but that chart shares the table's five by-model responses (there is no separate chart query), so it now sees up to 100 keys; the time-series requests do keep `top=20`.
- The brief says an empty `model` filter is rejected by the API, but the backend accepts `?model=` (only the empty model is dropped from facets); per the brief the `(none)` row is still made inert.
- The brief says a missing measure is "shown as `—`", but the backend emits `v=0` rows for every model that has a call, so `—` appears only for genuinely absent keys.
- Fixture has 3 models, so the real merge defect cannot be reproduced; the `top=100` request assertion is the regression guard.

## Unfinished
None.
