# Brief: 4-01 — One client data module: debounce, abort, cache, notices

Consumer: a TypeScript worker (flash-tier); every Phase 4 route unit calls the client this unit writes.
Owned paths: `packages/workflow-analytics/src/lib/api.ts`, `src/lib/api.test.ts`, `src/lib/types.ts`, `src/lib/state.svelte.ts`, `src/lib/query.ts` (new), `src/lib/query.test.ts` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-01-data-client.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 4-02, 4-03, 4-04.
Budget: 6 files to read, about 350 lines to write, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics` (`npm install` first if `node_modules` is missing). The Go API is read-only here; do not change it.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site", the bullet on the one client data module (debounce 250 ms or less, abort superseded, cache per session by normalised query, `partial` and `ignored_filters` notices, never render a superseded result).
2. `packages/workflow-analytics/src/lib/api.ts` and `api.test.ts` — `apiGet(path, params)`, the base URL and token keys, the non-JSON message. All of this behaviour stays.
3. `packages/workflow-analytics/src/lib/state.svelte.ts` and `types.ts` — the error state and the response types.
4. `tools/workflow/internal/serve/analytics_query.go` (the response writer near line 97) and `analytics_conversation.go` — the `/query`, `/schema` and `/conversation` response shapes.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Every report fetches through one module that never issues redundant requests and never lets a superseded response reach the screen.

## Contract

- `apiGet` paths are relative to `/v1`, for example `analytics/summary`. Params are `URLSearchParams`.
- A `/query` response is `{measure, bucket, dims, rows:[{t?, k:string[], v:number}], ignored_filters?:string[], partial?:boolean, truncated?:boolean}`. `k` has one entry per dimension. `t` is an RFC3339 string with the tz offset.
- `/schema` returns `{measures:[{name, unit, dims}], buckets}`. `/conversation?id=` returns `{conversation_id, harness, repos, models, first_ts, last_ts, totals:{model_calls, tokens_in, tokens_out, tokens_cache_read, tokens_cache_write, tokens_reasoning, cost_usd, unpriced_calls}, events:[{ts, type, norm_event, event, tool, model, path, kind, source, sha, tokens?, cost_usd?}], truncated?}`. `/summary` gains `model_calls`, `unpriced_calls`, `cost_usd` and token sums; `/facets` gains `models` and `norm_events`. Check each against the Go files before typing it.
- Phase 3 left little latency headroom (worst case 463 to 483 ms against a 500 ms bound). The client therefore caches, dedupes identical in-flight requests and limits concurrency.

## Changes

1. `api.ts`: add an optional third argument `signal?: AbortSignal` passed to `fetch`. Nothing else changes.
2. `query.ts` exports:
   - `class Superseded extends Error`.
   - `type Slot = string`. A slot is one consumer on a page, for example `overview-kpi-cost`.
   - `normalise(path: string, params: URLSearchParams): string`: base URL (read from localStorage with `BASE_KEY`) + path + params sorted by key then value, empty values dropped. Two orderings of the same params give the same string.
   - `createClient(opts?: {debounceMs?: number /* default 250 */, maxConcurrent?: number /* default 3 */, fetcher?: typeof apiGet})` returning `{get<T>(slot, path, params): Promise<T>, clearCache(): void}`.
   - `client`: the singleton, and `getJSON<T>(slot, path, params)` bound to it.
3. `get` semantics:
   - A new call on a slot aborts that slot's in-flight request and cancels its pending debounce; the earlier promise rejects with `Superseded`. A superseded promise never resolves with data.
   - A cache hit resolves without waiting for the debounce but still supersedes the slot's earlier call.
   - Otherwise the call waits `debounceMs`, then fetches. A burst of N calls on one slot inside the debounce issues one request, with the last params.
   - Identical normalised keys in flight at once share one fetch (each slot still resolves its own promise; aborting one slot's interest must not abort a fetch another slot still wants).
   - At most `maxConcurrent` fetches run at once across slots; the rest queue in order.
   - Only successful responses are cached, in memory, for the page session. Errors are not cached.
   - After a response, call `setNotice(slot, resp)` from `state.svelte.ts` when the response has `partial` or `ignored_filters`.
4. `state.svelte.ts`: keep `fetchError`, `setError`, `clearError` unchanged (the 401 and non-JSON paths rely on them). Add `notices` (a `$state` record keyed by slot: `{partial: boolean, ignored: string[]}`), `setNotice(slot, resp)`, `clearNotices()`.
5. `types.ts`: add `QueryRow`, `QueryResponse`, `Schema`, `TimelineEvent`, `ConversationDetail`, `Totals`; add the new `Summary` and `Facets` fields. Do not remove existing types (routes still use them until their units land).

### Keep untouched

Everything `api.test.ts` asserts today (base URL, bearer header, error mapping, non-JSON message). The localStorage key names.

## Done evidence

Write the failing `query.test.ts` first (vitest fake timers, a stub `fetcher`), and report its output before and after.

- `npm test` → passes, with tests for: a burst of five calls on one slot inside 250 ms makes the fetcher run once with the last params; the four earlier promises reject with `Superseded`; the fetcher receives an `AbortSignal` that is aborted when the slot is superseded mid-flight; a repeated identical call after success does not call the fetcher; two slots with the same key share one fetch; with `maxConcurrent: 2` and five distinct calls never more than two run at once; reordered params normalise to one key; an error is not cached.
- `npm run build` → passes (old routes still compile).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
