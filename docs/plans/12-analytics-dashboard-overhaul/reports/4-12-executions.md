# 4-12 — Executions: shared client, drill-down cells and conversation links

Status: **done**

## What changed

- `src/routes/executions/+page.svelte`: rewritten on the shared `view` module and the `getJSON` client (no more `apiGet`/`filterParams`/`parseFilter`). The first page is `getJSON<Executions>('executions', 'analytics/executions', view.paramsFor('rest', extra))`, where `extra` is `{limit}` only when the URL carries `limit`; a `null` `paramsFor` (pending facets or an empty exclude complement) skips the fetch. Kept the `exec-count-<shape>` tiles, the `exec-row` table and the unchanged `Pager` (cursor paging, response dropped after a filter change). `repo_id`/`plan`/`harness` cells are now buttons that call `view.drill(key, value, { shift: ev.shiftKey })`; the conversation cell is an `<a href="/conversation?id=<id>">` that keeps no filters. Added cell test ids `exec-repo`/`exec-plan`/`exec-harness`/`exec-conversation` (the guarded ids are untouched).
- `tests/e2e/executions.spec.ts`: kept the three original tests; added include-click, shift-click exclude, conversation-link navigation and the 1 s drill-timing assertion (7 tests total).

## Check output

Before (old spec run against the new page, per Done evidence): `E2E_PORT=4412 npm run test:e2e -- executions.spec.ts` → `3 passed (20.3s)` — no failures.

After (measured):

- `npm test` → `Test Files 11 passed (11) / Tests 76 passed (76)`.
- `npm run build` → exit 0 (`✓ built in 10.61s`, `Wrote site to "build"`).
- `E2E_PORT=4412 npm run test:e2e -- executions.spec.ts` → `7 passed (21.7s)`.

The conversation-link test logs `[404] GET /conversation`: 4-14's timeline route is a parallel unit and is absent from this worktree. The link and the `/conversation?id=c3` navigation both pass; only the target page is missing here.

## Deviations

1. The brief writes `view.drill(key, value, ev)`, but `drill`'s third parameter is `{ shift?: boolean }` (`view.svelte.ts:105`), not a `MouseEvent`; a raw event has no `.shift`, so shift-click would never register. Mapped `ev.shiftKey → { shift: … }`, matching `BarChart`/`Treemap` (`onselect?.({ …, shift: !!native?.shiftKey })`).
2. The brief writes `view.paramsFor('rest', {limit})`; `limit` is optional and `paramsFor` appends each extra value, so `{limit: null}` would send `limit=null`. `extra` is passed only when the URL has a `limit`.
3. Added four cell test ids (above) so the spec can target a cell inside an `exec-row`; no guarded id changed.

## Contradictions

- The two points in Deviations are the only conflicts between the brief and the contracts it cites; both are named, not resolved silently. No conflict with the "range too wide" contract: `resolveWindow` clamps `'rest'` windows to 399 days, so the page never issues a request that could 400.

## Known problems

- The `exec-row` click tests locate cells by their added test ids; if a later unit changes the row markup it must keep `exec-repo` (and the others) or update this spec.

## Bugs

- None found outside the done evidence.

## Unfinished

- None.
