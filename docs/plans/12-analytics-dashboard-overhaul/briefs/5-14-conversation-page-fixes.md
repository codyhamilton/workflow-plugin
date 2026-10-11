# Brief: 5-14 — Conversation page: back link, unpriced rows, cost label

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/conversation/+page.svelte`, `packages/workflow-analytics/src/lib/format.ts`, `packages/workflow-analytics/src/lib/format.test.ts`, `packages/workflow-analytics/tests/e2e/conversation.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-14-conversation-page-fixes.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: every other unit (disjoint paths). The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 6 files to read, about 130 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — "Carried (Phase 4)" items 3, 4 and 8, and "4-18" (timeline rows of an unpriced usage event read "unpriced").
2. `src/routes/conversation/+page.svelte` — back link, `tokens`, row rendering, header totals with `costLabel`.
3. `src/lib/format.ts` and `format.test.ts` — `costLabel`.
4. `tests/e2e/conversation.spec.ts` and `tests/e2e/fixture.ts` (`USAGE_C5`, conversation ids) — assertions to keep.
5. SvelteKit `afterNavigate` (`$app/navigation`): `navigation.from?.url` is the page the user came from.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The conversation's back link returns to the exact list the user came from, with its range and filters; timeline rows with no tokens and no cost no longer read "unpriced"; and `costLabel` never prints `$0.00` for a group that holds unpriced calls.

## Contract

- Back link (Carried 3): hard-coded to `/conversations` and drops the window and filters. The layout hides the chrome here and the conversation URL carries only `id`. Use `afterNavigate(({from}) => ...)`: when `from.url.pathname` is a site route other than `/conversation` and `/settings`, remember `pathname + search` (also in `sessionStorage` under `workflow-analytics-last-list`, in try/catch, so a reload keeps it); the back link points at that, labelled with the route name ("Back to Conversations", "Back to Executions", …). With no remembered value it falls back to `/conversations`. Do not edit links in other routes.
- Timeline rows (Carried 4): a usage event with tokens in and out both 0 and cost 0 or absent reads blank (no "unpriced" text); "unpriced" is for events that have tokens (in or out > 0) and no price (`cost_usd` null or 0).
- `costLabel` (Carried 8): with `calls` known, `unpriced > 0 && unpriced < calls && cost === 0` currently returns `$0.00`; it must read `unpriced` for the part that cannot be priced, e.g. `$0.00, 3 unpriced` is wrong because the 0 is not a price; return `unpriced` only when every call is unpriced, and when some are unpriced and the priced cost is 0 return `${n} unpriced`. Pin the full truth table in `format.test.ts` (calls undefined/0/n, unpriced 0/some/all, cost 0/small/large) and recount existing assertions rather than editing them to fit.

## Changes

Keep the header totals, 5,000-event virtualisation, the 404 and 400 messages, and test ids. `format.ts` is imported by Overview, Usage and Repos; keep the signature, and check those suites still pass.

### Keep untouched

Any behaviour in the conversation page not listed above.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- format` → the new truth-table cases fail before and pass after.
- `npm run test:e2e -- conversation.spec.ts` → new tests pass: opening a conversation from `/conversations?range=7d&harness=claude` and clicking back lands on that exact URL; a zero-token, zero-cost row has no "unpriced" text while a priced-model-less row with tokens still reads "unpriced".
- `npm test` and `npm run build` → pass; `npm run test:e2e -- overview.spec.ts usage.spec.ts repos.spec.ts` still pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
