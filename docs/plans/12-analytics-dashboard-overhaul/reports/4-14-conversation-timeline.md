# 4-14 — Conversation timeline with token and cost totals

Status: **done with concerns**

Concern: one spec change depends on the `/conversations` id link owned by 4-13, which is not on this
branch. Named under Contradictions.

## What changed

- `src/routes/conversation/+page.svelte` (new): `/conversation?id=<id>`. One `getJSON('conversation',
  'analytics/conversation', new URLSearchParams({id}))` per id; ignores the window and filters (the
  shell already hides the FilterBar for this path). Header shows harness, repos, models and
  first/last timestamps via `toLocaleString()` (browser zone). Totals render `conv-total-<name>` for
  `model_calls`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`,
  `tokens_reasoning`, `unpriced_calls`, and `conv-total-cost` = `costLabel({cost, unpriced, calls})`.
  Timeline rows (`timeline-row`) are sorted by `ts`, show time/norm_event/tool/model/path and, when
  present, tokens and cost; tokens with no priced cost show `unpriced`. A fixed 600 px scroll
  container with 28 px rows and a 10-row margin windows 5,000 events to ~32 DOM rows (inline: this
  unit does not own `VirtualRows`). `truncated` renders `timeline-truncated`. A `back-to-conversations`
  link goes to `/conversations`. 404 → `conversation-message` "No such conversation"; 400 → "Open a
  conversation from the list"; both avoid the layout error panel and its connection advice; other
  errors go through `setError`.
- `tests/e2e/conversation.spec.ts` (new): 8 tests — `USAGE_C5` totals + `$0.02, 1 unpriced` cost,
  ts-ordered rows, 404 without connection advice, 400, the list drill-down, 5,000 events under 100
  DOM rows, 1 s navigation→totals timing, and the truncated banner.

## Check output

Before (failing spec, page absent): `E2E_PORT=4414 npm run test:e2e -- conversation.spec.ts` → `8
failed` (no `conv-total-*` / `timeline-row` / `conversation-message` elements).

After (measured):

- `npm test` → `Test Files 11 passed (11) / Tests 76 passed (76)`.
- `npm run build` → exit 0, `✓ built in 10.96s`, `Wrote site to "build"`.
- `E2E_PORT=4414 npm run test:e2e -- conversation.spec.ts` → `8 passed (19.8s)`.

## Deviations

1. The drill-down test falls back to `page.goto('/conversation?id=c5')` when no
   `a[href="/conversation?id=c5"]` exists on `/conversations`; the click path runs once 4-13 lands.
2. Rows display `norm_event` when non-empty; the server normalises the `transcript.assistant_message`
   fact to `norm_event = "usage"`, so the row text is `usage`, not the raw event name. The spec
   asserts the rendered value.

## Contradictions

- Brief "Changes" requires a test clicking the id link from `/conversations`, but the link is owned by
  4-13 and the stated dependency is 4-05 only. On this branch `/conversations` renders the id as plain
  text (no anchor), so a click cannot navigate. Resolved by the fallback in Deviation 1, not silently.

## Known problems

- None beyond the dependency gap above.

## Unfinished

- None. No bug outside the done evidence was found.
