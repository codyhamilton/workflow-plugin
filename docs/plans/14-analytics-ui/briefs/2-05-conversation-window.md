# Brief: 2-05 — Conversation window and totals

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `tools/workflow/internal/store/conversation.go`; `tools/workflow/internal/store/conversation_test.go`; `tools/workflow/internal/serve/analytics_conversation.go`; `tools/workflow/internal/serve/analytics_conversation_test.go`; `tools/workflow/internal/serve/analytics_bench_test.go` (conversation cases with `from`/`to` on at least one preset). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/2-05-conversation-window.md` and include it in the commit.
Depends on: nothing (may land before or after 2-01; do not edit files outside owned paths).
Runs alongside: `2-01-distribution-read` when bench edits are coordinated — if `analytics_bench_test.go` conflicts, finish 2-01 first then rebase this unit’s bench hunk.
Budget: 6 files to read, about 280 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — **`GET /v1/analytics/conversation`**, Decisions (`totals` is the whole run), Phase 2 conversation fixture bullets.
2. `tools/workflow/internal/store/conversation.go` — current totals over returned events only (must change).
3. `tools/workflow/internal/serve/analytics_conversation.go` — handler.
4. `tools/workflow/internal/serve/analytics_conversation_test.go` — truncation test patterns.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Single-conversation read accepts optional window bounds, returns whole-run `totals`, range-scoped `window_totals` when bounds are present, and still lists all events with the cap applied only to the list.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Domain: Analytics reads, **`GET /v1/analytics/conversation`**. Settled:

- Optional `from` and `to`, RFC3339, inclusive. `from` after `to` → 400 `{"error":"from after to"}`.
- `events` stays the whole run in time order, capped at 5,000; `from`/`to` do not drop events.
- `totals` is the whole conversation, including events past the cap.
- `truncated` applies to `events` only.
- When `from` or `to` is present, `window_totals` is full totals for that inclusive range (not the capped slice). When both omitted, `window_totals` is absent.
- Dimension filters are not sent to this route (handler does not use shared `parseFilter` window presets for conversation list filters — only `from`/`to`/`id`).

## Changes

- Store: compute `Totals` over all kept usage calls in the conversation regardless of event cap; add `WindowTotals` when bounds provided (inclusive on `ts`). Events query unchanged except tests may mark which events fall inside the window for the UI later — response still returns all events.
- Handler: parse `from`/`to` without requiring the analytics filter bar keys; emit `window_totals` object matching `totals` shape when either bound set; validate `from after to`.
- Tests: when `events` truncated, `totals` still equals uncapped run; with `from`/`to`, `window_totals` matches range; an event outside the range remains in `events`; no `window_totals` when bounds omitted.
- Bench: at least one `conversation/...` case adds explicit `from` and `to` RFC3339 within the preset window.

### Keep untouched

Shared filter keys on other routes. Conversations list from 2-04 (different files). Event field shape on each event.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `go test ./internal/store/ -run TestConversation -count=1` from `tools/workflow` → passes, including truncated-events vs full totals and window_totals cases.
- `go test ./internal/serve/ -run TestConversation -count=1` from `tools/workflow` → passes, including 400 on `from after to` and absent `window_totals` when no bounds.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output before and after, deviations, contradictions. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
