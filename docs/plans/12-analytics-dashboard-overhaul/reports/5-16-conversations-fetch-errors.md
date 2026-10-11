# 5-16 — Conversations: show fetch errors

Status: **done**

## What changed

- `packages/workflow-analytics/src/routes/conversations/+page.svelte`: import `clearError, setError` from `$lib/state.svelte`; the success handler calls `clearError()`; the rejection handler now, for a live non-`Superseded` error, resets `rows = []`, `next = undefined`, `loaded = false` and calls `setError(e)`. `Superseded` still returns early (it is not an error).
- `packages/workflow-analytics/tests/e2e/conversations.spec.ts`: three tests added — a 500 from `**/v1/analytics/conversations*` shows `error-panel` (and no rows); `route.abort()` shows the connection message plus the `/settings` link; changing the preset after an error retries successfully and clears the panel (mutable `fail` flag in the route handler).

## Check output

- `npm run test:e2e -- conversations.spec.ts` (`E2E_PORT=4516`), **before** the component change: `3 failed, 6 passed` — each new test timed out on `error-panel` not found.
- Same command, **after**: `9 passed (18.3s)` — the six existing tests (virtualisation and the 1 s timing assertion included) plus the three new ones.
- `npm test`: 74 passed (10 files).
- `npm run build`: clean, `built in 7.59s`, site written.

## Pager finding

No edit (not owned). `src/lib/components/Pager.svelte:28-37` already wraps its page load in try/catch: `clearError()` on success and `setError(e)` on failure (only when the filter key is unchanged). It does **not** swallow errors.

## Deviations

None from the brief.

## Contradictions

None between the brief and the contracts it cites. Caveat on evidence strength: the layout `$effect` (`src/routes/+layout.svelte:32-37`) clears the error on any URL/filter change, so in the recovery test the panel also clears on the preset navigation itself; the success-path `clearError()` is still correct but this test does not isolate it.

## Known problems

- No new non-trivial bug found outside the done evidence.
- Pre-existing carried client bugs are unchanged (`IMPLEMENTATION.md` Phase 4 Carried 4.8): notices self-clear; `query.ts` can drop a shared in-flight entry for same-key joiners; `costLabel` can emit `$0.00` when `unpriced < calls`. Not fixed here (out of scope).
