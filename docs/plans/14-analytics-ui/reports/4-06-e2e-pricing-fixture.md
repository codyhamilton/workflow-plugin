# Report: 4-06 — E2E fixture pricing alignment

**Status:** done

## What changed

- **`fixture.ts`:** Recounted whole-window usage for priced `claude-opus-5-5` (table rates: input 4, cache_read 0.2, cache_write 5, output 20 USD/M tokens → **0.133977** on the c1 call). `USAGE_ALL`: `unpriced_calls` 1, `cost_usd` 0.156277; `USAGE_BY_MODEL` Opus row priced with `unpriced: 0`. Qwen stays unpriced.
- **`overview.spec.ts`:** Cost tile expectations use `costLabel()` with `USAGE_ALL` (shows `$0.16, 1 unpriced`).
- **`usage.spec.ts`:** Opus cost from `USAGE_BY_MODEL` + `costLabel()`; “only unpriced” window uses `?model=` qwen (Opus is priced under `harness=claude`); `$0.00` guard scoped to `usage-table` (histogram bins contain `$0.0001` substrings).
- **`interactions.spec.ts`:** Same qwen-only unpriced window; `/repos` fan-out expects **5** queries (four table measures + `cost_usd` from 3-06), not 4.

## Done evidence

**Before** (`E2E_PORT=4413`, same three spec files): **7 failed**, 33 passed — opus/unpriced mismatches on overview and usage; interactions unpriced harness test; repos fan-out expected 4 got 5.

**After:** **40 passed** (54.3s).

```
E2E_PORT=4413 npx playwright test tests/e2e/overview.spec.ts tests/e2e/usage.spec.ts tests/e2e/interactions.spec.ts
→ 40 passed
```

## Departures

- **E2E port:** Brief cites `4401`; worker used **4413** per dispatch instructions (avoid parallel unit collision).
- **Unpriced-only tests:** Filter changed from `harness=claude` to `model=` qwen because Opus is now priced; still asserts unpriced UI and no `$0.00` in the usage table.
- **Burst/repos test:** Updated expected query count 4→5 in owned `interactions.spec.ts` so the file passes with current `/repos` (not opus pricing, but required for done evidence on that spec file).

## Contradictions

None between brief, IMPLEMENTATION Phase 3 carried note, and store pricing table.

## Other issues

None found outside the above.
