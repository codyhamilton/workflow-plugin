# Report: 4-01 — One client data module: debounce, abort, cache, notices

Status: **done**

## What changed (against each part of the brief)

- **§1 `packages/workflow-analytics/src/lib/api.ts`** — added optional third parameter `signal?: AbortSignal` to `apiGet` and passed it into the existing `fetch(url, {headers, signal})`. Nothing else changed; base URL, bearer header, `ApiError` mapping and the non-JSON message are untouched.
- **§2 `src/lib/query.ts` (new)** — exports `class Superseded`, `type Slot`, `normalise(path, params)` (base from `localStorage[BASE_KEY]` + `/v1/` + de-slashed path; params sorted by key then value, empty values dropped), `createClient({debounceMs=250, maxConcurrent=3, fetcher=apiGet})` returning `{get<T>, clearCache()}`, the `client` singleton, and `getJSON<T>`. `get` implements per-slot supersession (clears the pending timer, rejects the prior call with `Superseded` under a per-call `settled` guard, releases its fetch interest), an in-memory success-only cache, debounce bursts to one fetch with the last params, in-flight dedupe by normalised key with a per-fetch refcount (abort only when refs hit 0), FIFO concurrency capped at `maxConcurrent`, a pre-fetch aborted-signal rejection, and `clearCache()`. `setNotice(slot, resp)` runs only when the response carries `partial` or a non-empty `ignored_filters` (brief §3 line 49), on both the fetch-success and cache-hit paths; the `resp &&` guard means a `null`/primitive body writes no notice.
- **§3 `src/lib/state.svelte.ts`** — `fetchError`, `setError`, `clearError` unchanged; added `notices` (`$state` keyed by slot), `setNotice`, `clearNotices`.
- **§4 `src/lib/types.ts`** — additive only: added `QueryRow`, `QueryResponse`, `Schema`, `TimelineEvent`, `Totals`, `ConversationDetail`; added `models`/`norm_events` to `Facets` and the eight token/cost/model fields to `Summary`. No existing type removed.
- **§5 `src/lib/query.test.ts` (new)** — 8 tests: normalise ordering/empty-drop/base; burst of five (one fetch, last params, four `Superseded`); mid-flight abort signal; cache hit; two slots share one fetch; `maxConcurrent: 2` peak; error not cached. `api.test.ts` untouched.

## Check output

Before (`npm test`; `query.ts` absent). The query suite fails to import, as required:

```
FAIL src/lib/query.test.ts [ src/lib/query.test.ts ]
Error: Cannot find module './query' imported from '.../src/lib/query.test.ts'
Test Files  5 failed | 5 passed (10)
     Tests  25 passed (25)
```

(The other four failing suites were sibling units' untracked tests whose modules had not landed at that moment — see Known problems.)

After (`npm test`; sibling modules had landed):

```
✓ src/lib/query.test.ts (8 tests) 13ms
Test Files  11 passed (11)
     Tests  76 passed (76)
```

`npm run build`:

```
✓ built in 3.98s (client) / 7.92s (server)
  Wrote site to "build"
  ✔ done
EXIT=0
```

Old routes (`trends`, `conversations`, `executions`, `explore`, `repos`, `hooks`, `quality`, `settings`) all compiled. Eight tests cover the seven required cases (`normalise` has two).

## Deviations

1. **The cache-hit path also calls `setNotice` for a cached `partial`/`ignored_filters` response.** The brief says "after a response"; a cache hit is not a new response. Named departure: a cached partial query should still surface its notice for that slot, so `get`'s cache branch applies the same guard as the fetch path.
2. **The `maxConcurrent` test's stub resolves `{}`, not `undefined`.** Test-only choice to return a plain object; the response guard treats any non-object body as no notice, so this has no behavioural effect.

## Contradictions

- **Same-slot, same-key re-request while in flight: brief §3 bullet 1 vs bullet 4 — named, not resolved.** Bullet 1: a new call on a slot aborts that slot's in-flight request, cancels its debounce, and the earlier promise rejects with `Superseded`. Bullet 4: identical normalised keys in flight at once share one fetch. For one slot re-requesting the same key mid-flight these conflict: sharing would join the existing fetch, but bullet 1 says abort and re-fetch. The implementation follows bullet 1 — the superseding call aborts the first fetch and issues one new fetch (one redundant request on this edge). Cross-slot identical keys still share one fetch per bullet 4. Left to the consumer.
- **Checked against the Go source and found none.** `analytics_query.go:97-115` (`/query` — `ignored_filters` only when non-empty, `partial` only while compaction incomplete, `truncated` only when true), `analytics_conversation.go:23-57` (`/conversation` keys, `tokens`/`cost_usd` optional, `truncated` optional), and `analytics.go:245-270` (`/facets` `models`/`norm_events`, `/summary` `model_calls`, `unpriced_calls`, `cost_usd`, token sums) all match the brief and the types added. No brief-vs-Go contradiction found.

## Unfinished

None.

## Known problems

- **A slot's notice is only set, never cleared, by a clean response.** `setNotice` runs only for responses carrying `partial`/`ignored_filters`, so a later clean response on the same slot leaves any earlier notice in place (stale). `clearNotices()` clears all slots; brief §4 gives no per-slot clear. Route units should call `clearNotices()` when they need a clean slate.
- **BEFORE run was polluted by concurrent siblings.** Untracked sibling test files (`buckets`, `params`, `presets`, `urlstate`) existed before their source modules landed in this worktree, so the before-count is 5 failed suites. They landed before the AFTER run; the one failure this unit is responsible for is `query.test.ts`, and it is the line quoted above.
