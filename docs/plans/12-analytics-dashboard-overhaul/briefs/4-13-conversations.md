# Brief: 4-13 — Conversations: a virtualised list that opens the timeline

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/conversations/+page.svelte`, `src/lib/components/VirtualRows.svelte` (new), `tests/e2e/conversations.spec.ts`. Touch nothing else (do not edit `Pager.svelte`).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-13-conversations.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06 to 4-12, 4-14, 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4413`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 7 files to read, about 250 lines to write, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": Conversations (virtualised), drill-down rules ("conversation IDs open the timeline").
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01) — exports only.
3. `src/routes/conversations/+page.svelte`, `src/lib/components/Pager.svelte` (read-only) and `tests/e2e/conversations.spec.ts` — test ids `conv-row`, `conv-<id>-<field>`.
4. `tests/e2e/fixture.ts` — `CONVERSATION_ROWS`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The conversations table stays responsive with thousands of loaded rows, and a conversation id opens its timeline.

## Contract

- `conversations` is a `rest` route and keyset-paged (limit 1 to 500, `next` cursor); the real ledger has about 4,700 conversations in 30 days. The first page goes through the client (`getJSON('conversations', 'analytics/conversations', view.paramsFor('rest', {limit}))`); `Pager` loads more.
- Virtualisation: `VirtualRows.svelte` renders only the rows in the scroll viewport plus a margin of ten, with fixed row height, inside a scroll container of fixed height (about 600 px). It takes `{rows, rowHeight, children snippet}`. With 5,000 loaded rows the DOM holds fewer than 100 `conv-row` elements.
- Cells: the conversation id is a link to `/conversation?id=<id>`; `harness` and each repo cell call `view.drill(...)` (shift excludes). Test ids kept: `conv-row`, `conv-<id>-<field>`.
- For small fixture data (four rows) all rows are in the DOM and existing assertions hold.

## Changes

Rewrite `+page.svelte` on `view`, the client, `VirtualRows` and `Pager`. Update `conversations.spec.ts`: rows equal `CONVERSATION_ROWS` (recount by hand if 4-03 moved them; never edit to match); the id link goes to `/conversation?id=c3`; a harness cell click adds a chip; with a `page.route` fulfilling `analytics/conversations` with 5,000 generated rows and no cursor, `conv-row` count in the DOM is under 100 and scrolling the container to the bottom shows the last row; the 1 s timing assertion.

### Keep untouched

The `conv-*` test ids and the cursor-paging behaviour.

## Done evidence

Run the old `conversations.spec.ts` against the new page first and report which tests fail before you change it.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- conversations.spec.ts` → all pass, including the 5,000-row test.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
