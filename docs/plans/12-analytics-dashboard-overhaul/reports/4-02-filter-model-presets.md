# Report: 4-02 — URL view state, presets, bucket picker, range-safe API params, cost label

Status: **done with concerns**

Concern: the full-suite `npm test` currently fails in `src/lib/query.test.ts` (a concurrent
worker's untracked file, not an owned path). Every test in this brief's five test files passes; the
build passes.

## What changed

| File | Change |
| --- | --- |
| `packages/workflow-analytics/src/lib/urlstate.ts` (new) | `DIM_KEYS`/`DimKey`, `PresetId`/`PRESET_IDS`, `UrlState`, `Chip`; `parseUrlState`, `toSearch`, `applyDrill`, `removeChip`, `chips`. Imports `KINDS` from `./filters` (read-only). |
| `packages/workflow-analytics/src/lib/urlstate.test.ts` (new) | 13 tests: defaults, preset/custom parse, invalid range fallback, include/exclude parse, unknown `kind` dropped, `DIM_KEYS` order, two round-trips, route-param carry-over, `__other__` identity, include↔exclude move, `removeChip`, `chips` order. |
| `packages/workflow-analytics/src/lib/presets.ts` (new) | `PRESETS` (8, in brief order), private `parts`/`offsetMs`/`localMidnight` (iterative DST-safe), `presetWindow`. |
| `packages/workflow-analytics/src/lib/presets.test.ts` (new) | 7 tests: order/labels, `all` null, span arithmetic, and the four exact DST/winter expectations (Sydney Jan, Sydney DST-end, NY DST-start, NY winter). |
| `packages/workflow-analytics/src/lib/buckets.ts` (new) | `Bucket`, `bucketCount` (upper bound), `pickBucket` (finest allowed within cap). Private `ymd` duplicated per spec. |
| `packages/workflow-analytics/src/lib/buckets.test.ts` (new) | 3 tests: hour/day/week/month selection, null under `allowed: ['hour']`, count bound sanity. |
| `packages/workflow-analytics/src/lib/params.ts` (new) | `Route`, `Window`, `ApiParams`; `resolveWindow`, `apiParams`, `scoresParams`. |
| `packages/workflow-analytics/src/lib/params.test.ts` (new) | 12 tests: rest clamp of `all`, query `all`, custom over-wide clamp, narrow preset, tz/window params, `all=1`, facet complement, pending, empty, include-minus-exclude, `conversation_id` excludes ignored, `scoresParams`. |
| `packages/workflow-analytics/src/lib/format.ts` (modified) | Appended `costLabel` only; `label`/`num` unchanged (diff: 15 added lines, 0 removed). |
| `packages/workflow-analytics/src/lib/format.test.ts` (new) | 8 tests: all-unpriced, mixed, priced, no-calls, sub-cent, unknown-calls unpriced, plus `label`/`num` regression. |

## Check output

### Before (STEP A, failing)

```
FAIL src/lib/urlstate.test.ts   (import resolution: ./urlstate missing)
FAIL src/lib/presets.test.ts    (import resolution: ./presets missing)
FAIL src/lib/buckets.test.ts    (import resolution: ./buckets missing)
FAIL src/lib/params.test.ts     (import resolution: ./params missing)
FAIL src/lib/format.test.ts > costLabel ...  TypeError: (0 , costLabel) is not a function
Test Files  6 failed | 5 passed (11)   # 5 mine + query.test.ts (another worker)
     Tests  6 failed | 27 passed (33)
```

### After (mine)

```
$ npx vitest run src/lib/urlstate.test.ts src/lib/presets.test.ts src/lib/buckets.test.ts \
    src/lib/params.test.ts src/lib/format.test.ts
✓ src/lib/format.test.ts (8 tests)
✓ src/lib/buckets.test.ts (3 tests)
✓ src/lib/presets.test.ts (7 tests)
✓ src/lib/params.test.ts (12 tests)
✓ src/lib/urlstate.test.ts (13 tests)
Test Files  5 passed (5)
     Tests  43 passed (43)
```

### After (full suite)

```
$ npm test
✓ src/lib/urlstate.test.ts (13 tests)   ✓ src/lib/params.test.ts (12 tests)
✓ src/lib/presets.test.ts (7 tests)     ✓ src/lib/format.test.ts (8 tests)
✓ src/lib/buckets.test.ts (3 tests)     (and api/filters/series/charts/theme, all pass)
❯ src/lib/query.test.ts (8 tests | 1 failed)
 FAIL  src/lib/query.test.ts > createClient.get > never runs more than maxConcurrent fetches at once
Test Files  1 failed | 10 passed (11)
     Tests  1 failed | 75 passed (76)
```

`query.test.ts`/`query.ts` are untracked new files from a concurrent worker; not owned here and left
untouched.

### Build

```
$ npm run build
✓ built in 9.05s
  Wrote site to "build"
  ✔ done
```

## Deviations

1. **`resolveWindow` only clamps a `custom`/preset window on `rest` when both `from` and `to` are
   present.** The brief's `rest` rule is stated for "any window wider than 399 days"; a custom range
   with one edge missing has no width, so nothing to clamp. This matches the spec's literal "if from
   and to and to-from > 399 days".
2. **`PRESET_IDS` typed as `PresetId[]` (mutable) not `readonly`.** The spec's snippet says
   `PresetId[]`; followed literally even though it is only read.
3. **Spec said "six `*.test.ts` files" but the owned list contains five** (`urlstate`, `presets`,
   `buckets`, `params`, `format`). I wrote the five that exist; there is no sixth module.

No other departures; style (tabs, single quotes, ESM, explicit return types, `as const`, minimal
JSDoc) matches `filters.ts`.

## Contradictions

1. **`costLabel` branch rules conflict with the brief's final sentence.** For `calls > 0`,
   `0 < unpriced < calls`, `cost === 0` the written branches return `$0.00` — the first guard needs
   `unpriced >= calls`, `cost > 0` is false, and `calls === 0` is false, so it falls to the final
   `return '$0.00'`. But the brief says "A cost of `$0.00` must never come out for a row that has
   unpriced calls." These cannot both hold. I implemented the branch rules **as written** (the
   authoritative step in the spec) and the tests do not exercise that combination. Not resolved;
   flagged for the design owner.
2. **`hour` bucket bound wording vs formula.** The brief says `hour` is "for windows of about 16
   days or less"; the given `bucketCount('hour') = ceil(ms/3600000)+2` allows up to 398 h ≈ 16.6
   days at `cap = 400`. Minor; the formula is authoritative and is what is implemented.

## Unfinished

None. `npm run build` passes; all 43 tests in the five owned test files pass. The only red in the
repo is `query.test.ts`, which belongs to another unit.

## Problems

- Full-suite `npm test` is red because of a concurrent worker's in-progress `query.test.ts`. It is
  out of scope and was not modified. Re-run `npm test` once 4-03/4-04 land.
