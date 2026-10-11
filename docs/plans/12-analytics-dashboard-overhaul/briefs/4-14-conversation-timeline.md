# Brief: 4-14 — Conversation timeline with token and cost totals

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/conversation/+page.svelte` (new), `tests/e2e/conversation.spec.ts` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-14-conversation-timeline.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06 to 4-13, 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4414`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 6 files to read, about 200 lines to write, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": Conversation timeline; Phase 4 outcome "Clicking a conversation ID opens its timeline with token and cost totals".
2. `src/lib/query.ts` (4-01), `src/lib/types.ts` (`ConversationDetail`), `src/lib/format.ts` (`costLabel`, `num`) — exports only.
3. `tools/workflow/internal/serve/analytics_conversation.go` — the response and the 404 and 400 cases.
4. `tests/e2e/fixture.ts` — `USAGE_C5` (4-03) and the `c5` and `c1` facts.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A conversation id leads to a page that lists what happened in order and says what it used and what it cost.

## Contract

- Route `/conversation?id=<id>` (not a path parameter, so the static build needs no extra routes). It calls `getJSON('conversation', 'analytics/conversation', new URLSearchParams({id}))` once. The window and filters do not apply: the shell hides the FilterBar here, and the page ignores `view`.
- Response: `{conversation_id, harness, repos, models, first_ts, last_ts, totals:{model_calls, tokens_in, tokens_out, tokens_cache_read, tokens_cache_write, tokens_reasoning, cost_usd, unpriced_calls}, events:[{ts, type, norm_event, event, tool, model, path, kind, source, sha, tokens?, cost_usd?}], truncated?}`. 404 for an unknown id (show "No such conversation", not the error panel's connection advice), 400 for a missing id (show "Open a conversation from the list").
- Totals (`data-testid="conv-total-<name>"` for each of `model_calls`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`, `unpriced_calls`; `conv-total-cost` shows `costLabel({cost: cost_usd, unpriced: unpriced_calls, calls: model_calls})`, never `$0.00` when `unpriced_calls > 0`).
- Timeline: `events` in `ts` order, one row each (`data-testid="timeline-row"`) with time, `norm_event` or `event`, tool, model, path and, when present, tokens and cost; a row with `tokens` and no priced cost shows `unpriced`. `truncated` shows `timeline-truncated` ("showing the first 5,000 events"). Long timelines are windowed with the same fixed-height scroll container approach as 4-13 (inline here: this unit does not own `VirtualRows`); under 100 `timeline-row` elements in the DOM for 5,000 events.
- Header: harness, repos, models, first and last timestamps, in the browser time zone.
- A "back to conversations" link goes to `/conversations`.

## Changes

New `conversation/+page.svelte` and `conversation.spec.ts`: `/conversation?id=c5` totals equal `USAGE_C5` (hand-counted; `conv-total-cost` shows the priced total together with the unpriced note because one `c5` call is unpriced); the rows are in `ts` order; `/conversation?id=nope` shows the 404 message without the connection advice; no id shows the 400 message; the id link from `/conversations` lands here (click `c5`); a `page.route` fulfilling the route with 5,000 events keeps the DOM under 100 rows; the 1 s timing assertion from navigation to the totals being visible.

## Done evidence

Write the failing `conversation.spec.ts` first and report its output before the page exists and after.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- conversation.spec.ts` → all pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
