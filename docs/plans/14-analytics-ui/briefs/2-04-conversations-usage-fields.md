# Brief: 2-04 — Conversations usage fields

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `tools/workflow/internal/store/analytics.go` (`ConvRow`, `ConversationsPage`, and usage aggregation helpers only); `tools/workflow/internal/store/analytics_test.go` (conversations usage tests only); `tools/workflow/internal/serve/analytics.go` (`analyticsConversations` response fields only); `tools/workflow/internal/serve/analytics_test.go` (conversations route assertions only); `tools/workflow/internal/serve/analytics_bench_test.go` (conversations cases unchanged path but must still 200). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/2-04-conversations-usage-fields.md` and include it in the commit.
Depends on: `2-03-executions-shape-series`.
Runs alongside: nothing.
Budget: 8 files to read, about 300 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — **`GET /v1/analytics/conversations`** row fields and model rule; Phase 2 conversations fixture bullet.
2. `tools/workflow/internal/store/usage.go` — kept usage calls and `Cost`.
3. `tools/workflow/internal/store/analytics.go` — `ConversationsPage`, harness fill, existing harness tie-break.
4. `tools/workflow/internal/serve/analytics.go` — `analyticsConversations`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Each conversation list row includes in-window usage totals and a `model` chosen by the most-frequent rule over in-window kept model calls.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Domain: Analytics reads, **`GET /v1/analytics/conversations`**. Settled:

- Each row gains `model`, `model_calls`, `unpriced_calls`, `cost_usd`, `tokens_in`, `tokens_out`.
- `model` uses the most-frequent model on in-window kept calls; ties to smaller name; `""` when no calls.
- Counts and cost/tokens are in-window (same window filter as other columns). Order stays `last_ts` desc, `conversation_id` asc.

## Changes

- Extend `ConvRow` and SQL/page aggregation: join or post-query usage totals per conversation using the same kept-call selection as `usageRowsWhere` scoped to the page’s conversation ids (avoid loading the whole tenant when paging).
- Handler JSON adds the new fields with the same rounding as elsewhere for `cost_usd`.
- Store test on the shared `fixture(t)`: assert at least one row’s `model` matches the most-frequent rule over known usage facts. Serve test checks JSON keys on `/v1/analytics/conversations`.

### Keep untouched

Executions shape/series behavior from 2-03. Conversation detail route (`/conversation`). Existing paging keyset order.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `go test ./internal/store/ -run 'TestAnalyticsConversations|TestConversationsPage' -count=1` from `tools/workflow` → passes with model and usage field assertions on the fixture.
- `go test ./internal/serve/ -run 'TestAnalytics.*Conversation|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow` → passes (list route, not single-conversation tests).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output before and after, deviations, contradictions. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
