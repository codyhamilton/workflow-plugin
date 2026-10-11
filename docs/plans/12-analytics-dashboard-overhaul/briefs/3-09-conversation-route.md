# Brief: 3-09 — `GET /v1/analytics/conversation` timeline

Consumer: a Go worker (flash-tier); the Phase 4 drill-down reads this route.
Owned paths: `tools/workflow/internal/store/conversation.go` (new), `conversation_test.go` (new), `tools/workflow/internal/serve/analytics_conversation.go` (new), `analytics_conversation_test.go` (new), and `tools/workflow/internal/serve/serve.go` (only the one `mux.HandleFunc` line). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-09-conversation-route.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-05, 3-06.
Runs alongside: 3-07, 3-08.
Budget: 6 files to read, about 300 lines to write, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads: the **`GET /v1/analytics/conversation`** bullet (binding, quote the JSON shape).
2. `tools/workflow/internal/store/usage.go` (3-05) — the call-selection helper; `store/pricing.go` `Cost`.
3. `tools/workflow/internal/serve/analytics_query.go` (3-06) — handler style, auth wrapper, `errJSON`.
4. `tools/workflow/internal/serve/serve.go` lines 420-432 — route registration.
5. `tools/workflow/internal/store/analytics.go` — `ExploreRow`, column names, `rfc`-style time formatting in `serve/analytics.go` line 180.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

One conversation's timeline and totals are returned, with no bodies, in time order, from the columns.

## Contract

Design, cited: "`GET /v1/analytics/conversation` (`id` required). It returns `{"conversation_id","harness","repos","models","first_ts","last_ts","totals":{tokens…,cost_usd},"events":[{"ts","type","norm_event","event","tool","model","path","kind","source","sha","tokens"?,"cost_usd"?}]}` in time order, capped at 5,000 events with `truncated`. It returns no bodies."

Settled by this brief:
- Store: `func (t *Tenant) Conversation(ctx, id string) (ConversationDetail, bool, error)`; `false` when no fact has that `conversation_id`. It reads `facts WHERE conversation_id=?` (index `facts_conv(conversation_id, ts)`) ordered `ts, row_hash`, `LIMIT 5001`. No window filter and no other filter keys.
- `harness` is the most frequent harness among its facts (ties to the smaller name); `repos` and `models` are sorted distinct non-empty values; `first_ts` and `last_ts` are RFC3339 UTC of the min and max `ts` over ALL its facts (a separate aggregate, not just the 5,000 returned).
- `tokens` on an event is `{"in","out","cache_read","cache_write","reasoning"}` present only on usage facts; `cost_usd` present only on usage facts and from `Cost`. `totals` uses the same deduped call selection as 3-05 (so a repeated Claude message counts once in totals; the repeated events themselves all remain in `events`, the later duplicates carry no `tokens` or `cost_usd`, to keep the sum of events equal to `totals`). `totals` keys: `model_calls`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`, `cost_usd`, `unpriced_calls`.
- Serve: GET, `id` required (400 `{"error":"id required"}`), unknown id is 404 `{"error":"conversation not found"}`, `truncated:true` when more than 5,000 facts. Never include `raw`.

## Done evidence

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store ./internal/serve -run Conversation -v` passes with tests for: time order; fields from the contract present for a mixed fixture (prompt, tool, usage, artifact_version, commit); a Claude duplicate pair counts once in `totals` and the second event has no `cost_usd`; sum of event `cost_usd` equals `totals.cost_usd`; a fixture of 5,001 facts returns 5,000 events with `truncated:true` and `last_ts` from the 5,001st; missing `id` 400; unknown id 404; the JSON contains no `raw` key (assert on the decoded keys).
- `go vet` and `gofmt -l` print nothing for both packages.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
