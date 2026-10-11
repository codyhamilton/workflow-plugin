---
# Report: 4-03 Fixture with usage facts, recounted constants, e2e helpers and a configurable port

Status: done

## What changed
- `packages/workflow-analytics/tests/e2e/fixture.ts`: added `c5` (opencode, r1) with three `transcript.assistant_message` facts (`at(4,7)`, `at(2,7)`, `at(1,7)`: two priced Sonnet calls on different days, one unpriced `ollama-maxctx/qwen3-coder:30b-a3b-q4_K_M` call) and one Claude `transcript.assistant_message` on `c1` (`at(5,13)`, unpriced Opus). Added `'opencode'` to `HARNESSES`. Exported `USAGE_ALL`, `USAGE_BY_MODEL` (keyed by the derived model name the normaliser stores), and `USAGE_C5` (the `/conversation?id=c5` `totals`). Recounted, as comment-free literals: `SUMMARY_ALL` (conversations 5, hook_events 10), `SUMMARY_R1` (4, 9), `HOOKS_BY_REPO` (r1 9), `HOOKS_BY_HARNESS` (+opencode 3), `HOOKS_BY_EVENT` (+`transcript.assistant_message` 4), `HOOKS_BY_TOOL` ('' 6), `HOOK_EVENTS_BY_DAY` (3/2/2/3), `CONVERSATION_ROWS` (c5 inserted before c2; c1 hook_events 4).
- `packages/workflow-analytics/tests/e2e/helpers.ts`: added `trackRequests`, `expectSettled`, `clickBar` (4-04 grid `left 120, right 24, top 8, bottom 24`, bar centre from `<testid>-table` rows), and `brush` (mid-height drag between two width fractions).
- `playwright.config.ts` + `tests/e2e/global-setup.ts`: `PREVIEW_PORT = Number(process.env.E2E_PORT) || 4391`, both used for the preview origin and the keyed serve's `WORKFLOW_SERVE_CORS_ORIGINS`.
- Forced spec edits: `hooks.spec.ts` `R1` (event +usage 4, tool '' 6, harness claude 5/opencode 3); `fixture.spec.ts` inline series groups (repo_id/harness/event/tool); `trends.spec.ts` `BY_HARNESS`/`BY_HARNESS_R1` claude d5 2→3, repo group d5 2→3, and the cursor d2 cell assertion. `executions`/`quality`/`conversations`/`overview`/`repos`/`explore`/`settings` needed no edit (they read `SUMMARY_*`/`CONVERSATION_ROWS` or derive).

## Check output
Before:
- `npm run test:e2e` (default port 4391): `26 passed (21.4s)`.

After:
- `npm run test:e2e` (default port 4391): `26 passed (17.9s)`.
- `E2E_PORT=4393 npm run test:e2e` (full): `26 passed (17.9s)`.
- `E2E_PORT=4393 npm run test:e2e -- fixture.spec.ts`: `1 passed (11.3s)`.
- A first default-port run failed all preview-backed tests with `net::ERR_CONNECTION_REFUSED http://127.0.0.1:4391` (a parallel worker held 4391); re-run once free passed. Evidence for this change is the `E2E_PORT=4393` run, which exercises the same code path.

## Curl comparison (step 2), literal vs server
Server started manually (`serve` + `POST /v1/ingest` with the fixture), queries on `/v1/analytics/`:
```
cost_usd   dim=model  anthropic/claude-sonnet-5-5 0.0223 | 0.0223
cost_usd   dim=model  claude-opus-5-5            0      | 0
cost_usd   dim=model  ollama-maxctx/qwen3-coder… 0      | 0
unpriced_calls dim=model  sonnet 0 | 0
unpriced_calls dim=model  opus   1 | 1
unpriced_calls dim=model  qwen   1 | 1
model_calls    dim=model  sonnet 2 | 2
model_calls    dim=model  opus   1 | 1
model_calls    dim=model  qwen   1 | 1
tokens_in      dim=model  sonnet 3000 | 3000   (USAGE_ALL sum 3502 | 3502)
tokens_out     dim=model  sonnet 500  | 500    (sum 6105 | 6105)
tokens_cache_read  dim=model sonnet 3100 | 3100 (sum 99397 | 99397)
tokens_cache_write dim=model sonnet 450  | 450  (sum 1372 | 1372)
tokens_reasoning   dim=model sonnet 60   | 60   (sum 60 | 60)
conversation id=c5 totals model_calls 3|3 tokens_in 3500|3500 tokens_out 600|600
  tokens_cache_read 3100|3100 tokens_cache_write 450|450 tokens_reasoning 60|60
  cost_usd 0.0223|0.0223 unpriced_calls 1|1
summary conversations 5|5 hook_events 10|10 model_calls 4|4 unpriced_calls 2|2
  cost_usd 0.0223|0.0223 tokens_in 3502|3502 tokens_out 6105|6105
  tokens_cache_read 99397|99397 tokens_cache_write 1372|1372 tokens_reasoning 60|60
series?metric=hook_events&bucket=day&group=harness|repo_id|event|tool: all groups equal
  the recounted constants (claude 5 / cursor 2 / opencode 3; r1 9 / r2 1; +transcript.assistant_message 4; '' 6)
```
Every literal equals the server value; `0.0123 + 0.0100` serialised exactly as `0.0223`.

## Departures
- File-read budget: the brief allows 8 reads; recounting every moved constant needed the normaliser (`ingest/extract.go`, `normalise.go`), `store/usage.go`, `store/analytics.go`, the six specs it lists and the 4-04/4-08/4-14 briefs. Tool turns stayed well under 60 and lines changed under 250.
- `trends.spec.ts` cell assertion: the trends table renders one cell per (series × union-of-times), so once `opencode` has a point on `DAYS.d2` the `cursor`×`d2` cell exists with value 0. Changed `toHaveCount(0)` to `toHaveText('0')` (the original intent: cursor's r2 point is filtered out).
- `fixture.spec.ts` carries inline series-group numbers (not the `HOOKS_BY_*` exports); recounted there too.

## Contradictions
- `clickBar` reads N from `<testid>-table` (4-03), but 4-04's toggle defaults to the chart and may mount `DataTable` only after a toggle click. The helper falls back to clicking `<testid>-table-toggle` when the table has no rows. Named, not resolved silently.
- No contradiction between the fixture counts and the ingest/pricing code: Claude and Opus are absent from `pricing_table.json`, so the Opus call is unpriced; OpenCode's reported `cost > 0` passes through.

## Unexercised
- `clickBar` and `brush` are written against the 4-04 contract but unexercised until 4-04 lands; no spec calls them here.

## Bugs
- None found outside the done evidence.

## Unfinished
- None. The existing suite passes against the unchanged site (retained route shapes did not regress); the new `USAGE_*` constants are consumed by 4-07/4-08/4-14.
---
