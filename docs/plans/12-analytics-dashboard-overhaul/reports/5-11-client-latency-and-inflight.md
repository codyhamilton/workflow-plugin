# Report: 5-11 — Data client: lower debounce for discrete actions and fix the shared in-flight entry

Status: **done**

## What changed

- `packages/workflow-analytics/src/lib/query.ts`
  - `createClient` options: `debounceMs` default **100** (was 250); new `idleMs` default **250**; both still injectable. Cache hits stay synchronous.
  - Leading edge: when a slot's previous call has **settled** and the slot has been idle at least `idleMs`, the next call runs immediately with no wait. A call while the previous is unsettled or within `idleMs` of its settle debounces 100 ms trailing and supersedes as before.
  - Shared in-flight fix: `Fetch` gains `dead`. `release` marks it dead once `refs` reaches 0; `run` never joins a dead entry (starts a new fetch instead); `perform` refuses to commit (`cache.set`) or resolve once the fetch is dead, including a re-check after `await`.
- `packages/workflow-analytics/src/lib/query.test.ts`
  - Existing burst test now exercises the default window (counts unchanged: one fetch, last params, four `Superseded`).
  - Added: 100 ms default window; leading edge fires with no wait after idle; a call within the idle window still debounces and supersedes; the shared-entry regression.

## Checks (before → after)

- New/updated tests against the old `query.ts` (Phase 1): 4 failed / 9 passed. Failures: burst test (timeout — old default 250 vs advanced 100), `waits the 100 ms default debounce window` (spy called 0), `fires on the leading edge with no wait` (spy called 1, not 2), shared-entry regression (`{v:'stale'}` instead of `{v:'fresh'}`).
- After (Phase 2): `npm test -- query` → **13 passed (13)**.
- `npm run build` → pass (client + server build).
- `E2E_PORT=4511 npm run test:e2e -- overview.spec.ts usage.spec.ts` → **20 passed**. Burst guards included: overview `switching 30d to 90d issues each distinct query once` (10 distinct), `one summary and at most ten query requests per load`; usage `one load issues seven /analytics/query requests, none per model` (exactly 7), `switching 30d to 90d issues each distinct query once` (7 distinct).
- Fixture p50 preset click → settled chart: **before 46 ms** (samples `[59,46,47,34,34]`), **after 34 ms** (samples `[51,44,33,34,34]`). The large-ledger figure is re-measured by the orchestrator.

## Deviations from the brief

1. **Leading edge is not applied to a slot that has never made a call.** The brief (line 30) includes "(the previous call on that slot settled **or was never made**)"; a cold slot debounces 100 ms instead. Reason: change 3 requires "a burst of five calls on one slot issues one fetch", and the cited Phase 4 outcome is "A burst of filter changes issues only the last request". Firing a cold slot on the leading edge emits the **first** request of a burst (two requests for a cold burst) and breaks that outcome and the unit burst test. Preset clicks/navigations after a pause are always preceded by the mount load's settled call, so they still wait 0 ms. See the contradiction below.
2. **The brief's stated symptom for the shared-entry bug did not reproduce as written.** Change 2 says a same-key joiner can receive `Superseded` or a hung promise. Over 72,000 randomized orderings (two-to-three slots sharing one key, supersession at `debounceMs` 0/10/250, fetch signals both honoured and ignored) no joiner lost its data or hung: `refs` is symmetric, so `release` never aborts a fetch a live slot still holds. The reproducible defect is different but in the same mechanism: `release` deletes the entry and calls `abort()`, but **abort is cooperative**, so a released fetch that resolves late still ran `cache.set(f.key, data)`, overwriting the cache for a newer same-key generation; and a same-key joiner arriving after the drop issued a duplicate fetch. Fixed with the `dead` guard (skip on join, refuse cache commit/resolve). The regression test asserts a joiner gets the fresh value and that a late released resolve cannot poison the cache. This reframes the symptom; it does not change the goal (`inflight` never strands or serves a dead entry).

## Contradictions in the contracts this brief cites

- **Brief line 30 vs change 3 / Phase 4 outcome.** "the previous call on that slot settled **or was never made**" conflicts with "a burst of five calls on one slot issues one fetch" and "A burst of filter changes issues only the last request". Resolved in favour of the burst outcome (cold slots debounce); recorded above.
- **Brief lines 15/28 vs DESIGN.md 207/427.** DESIGN allows "debounces filter changes (≤ 250 ms)"; 100 ms is within it, so no conflict.

## Unfinished work

None. Large-ledger latency is re-measured by the orchestrator per the brief; all other done evidence is recorded above.

## Known problems

None outside this unit.

## Non-trivial bugs found outside the done evidence

None.
