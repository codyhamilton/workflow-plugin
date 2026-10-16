# Brief: 4-04 — Conversation window and timeline

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/conversation/+page.svelte`; `packages/workflow-analytics/src/routes/+layout.svelte`; `packages/workflow-analytics/src/lib/types.ts` (add optional `window_totals` on `ConversationDetail` only); `packages/workflow-analytics/src/lib/params.ts` (add `conversationParams` only: `id` plus optional `from`/`to` from resolved window, no dimension keys); `packages/workflow-analytics/tests/e2e/conversation.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/4-04-conversation-window-timeline.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-01-quality-score-series (coordinate `types.ts` / `params.ts` with 4-01).
Runs alongside: 4-02-executions-shape-series, 4-03-conversations-cost-distribution.
Budget: 14 files to read, about 260 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 4 `/conversation` outcome; Domain: Report interaction (“`/conversation` shows that window control. Dimension filters are not sent to `GET /v1/analytics/conversation`.”); Domain: Analytics reads **`GET /v1/analytics/conversation`** (`from`/`to`, `totals`, `window_totals`, `truncated`); Decisions (“`totals` on one conversation is the whole run.”).
2. `packages/workflow-analytics/src/routes/+layout.svelte` — `chrome` hides FilterBar on `/conversation`.
3. `packages/workflow-analytics/src/routes/conversation/+page.svelte` — fetch ignores window today.
4. `tools/workflow/internal/serve/analytics_conversation_test.go` — `window_totals` and events outside range still listed.
5. `packages/workflow-analytics/tests/e2e/conversation.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The conversation timeline shows the shell window control, loads optional range totals from the API, marks in-window vs out-of-window events, and keeps full-run `totals` beside `window_totals`.

## Contract

Phase 4 outcome:

- On `/conversation`, the window control is visible. Events inside `from`/`to` are marked, events outside that range stay listed, and `window_totals` are shown beside `totals`.

`GET /v1/analytics/conversation` from DESIGN.md (binding):

- Optional `from` and `to`, RFC3339, inclusive. `events` stays the whole run in time order, capped at 5,000. `from` and `to` do not drop events. `totals` is the whole conversation, including events past the cap. `truncated` applies to `events` only. When `from` or `to` is present, `window_totals` is that range's full totals, not the capped slice. When both are omitted, `window_totals` is absent.

Domain: Report interaction:

- `/conversation` shows that window control. Dimension filters are not sent to `GET /v1/analytics/conversation`.

## Changes

- Show filter chrome on `/conversation` (at minimum `FilterBar` window presets and custom range). Do not send shared dimension filters to the conversation GET — use `conversationParams(id, view.state, view.tz)` for `from`/`to` only (always send resolved window when user picked a preset/custom range; omit both only when the product already treats the window as “all” — match how other rest routes send `from`/`to`).
- Refetch conversation when window params change (still one conversation `id`).
- UI: display `totals` tiles as today; when `window_totals` present, show a labelled second row or paired tiles for the window slice.
- Timeline rows: visually mark events whose `ts` falls inside the requested window vs outside (class or badge); never hide out-of-window events.
- Keep back link, virtualised scroller, truncation notice, and 404/400 messages.

### Keep untouched

`FilterBar.svelte` internals unless a one-line test id is required; backend; other routes’ layout branches (`embed`, `/dashboards`, `/settings`).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/conversation.spec.ts` → passes, including new tests: on `/conversation?id=c5` the preset control is visible; narrowing preset changes the conversation request query to include `from` and `to`; stubbed response with an event outside range still lists it with out-of-window marking; stub shows `window_totals` distinct from `totals`; when window params cleared to match “no from/to” behaviour, UI hides `window_totals`. Existing totals/virtualisation/back-link tests still pass (update expected cost copy only if 4-06 already landed — if still failing on opus pricing, note in report, do not edit `fixture.ts` here).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
