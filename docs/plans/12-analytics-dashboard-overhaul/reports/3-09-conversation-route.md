# Execution report — 3-09 `GET /v1/analytics/conversation`

**Status:** done

## What changed

- `internal/store/conversation.go` (new): `Tenant.Conversation(ctx,id)` plus
  `ConversationEvent`, `ConversationTotals`, `ConversationDetail`. Reads `facts WHERE
  conversation_id=?` ordered `ts,row_hash`, `LIMIT 5001`; a `base` CTE adds `_mid`
  (`CASE WHEN type='hook_event' AND norm_event='usage' THEN CASE WHEN harness='claude' THEN
  json_extract(raw,'$.backfill.ref') END END`) and `_rn = ROW_NUMBER() OVER (PARTITION BY
  _mid ORDER BY tok_out DESC, row_hash ASC)` — the same selection as 3-05's `usageRowsWhere`.
  A separate aggregate supplies `MIN/MAX(ts)` over all facts; `harness` is the modal value
  (ties smaller name); `repos`/`models` are sorted distinct non-empty. Only kept usage facts
  get `Tokens`/`CostUSD` (via `Cost`); totals are accumulated from the returned events so
  their sum equals `totals`.
- `internal/serve/analytics_conversation.go` (new): GET handler, `id` required (400), unknown
  404 `conversation not found`, emits the contract shape with `truncated:true` past 5,000.
- `internal/serve/serve.go`: one `mux.HandleFunc("/v1/analytics/conversation", …)` line.
- Tests: `store/conversation_test.go`, `serve/analytics_conversation_test.go`.

## Checks

Before: files absent; route absent (only `TestAnalyticsConversations` matched `-run Conversation`).

After (`cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store ./internal/serve -run Conversation -v`):
`TestConversationTimeline, Dedupe, Truncate, Unknown` (store) and `TestConversationRouteFields,
RouteErrors, RouteDedupe, RouteTruncate` (serve) all PASS; `ok` both packages.
`go vet ./internal/store ./internal/serve` → exit 0, no output.
`gofmt -l` on the four new files + `serve.go` → no output.
Full packages: `ok store 1.144s`, `ok serve 3.082s`.

## Deviations

- `ConversationEvent` carries an unexported `priced bool` so the totals loop can count
  `unpriced_calls` without recomputing `Cost` (recomputing would lose the harness and the
  reported-cost branch). Not part of the JSON contract.
- `cost_usd` is emitted on **every** kept usage fact, including unpriced ones (value from
  `Cost`, i.e. `0`). The brief's "present only on usage facts and from `Cost`" fixes when it may
  appear, not that unpriced calls omit it; `DESIGN.md` marks the field optional. Duplicates
  still omit it as required. If the intent was omission when unpriced, this is the one line to
  change.

## Contradictions

None between the brief and the contracts it cites. The brief's totals keys and event fields
match the DESIGN bullet verbatim.

## Unfinished / out of scope

None. No non-trivial bugs found outside the done evidence.
