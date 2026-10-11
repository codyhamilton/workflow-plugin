# Brief: 5-16 — Conversations: show fetch errors

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/conversations/+page.svelte`, `packages/workflow-analytics/tests/e2e/conversations.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-16-conversations-fetch-errors.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: every other unit (disjoint paths). The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 4 files to read, about 40 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — "Carried (Phase 4)" item 7 and "4-13-conversations".
2. `src/routes/conversations/+page.svelte` — the `getJSON` rejection handler (it returns without acting on a non-`Superseded` error).
3. `src/routes/executions/+page.svelte` — the pattern (`clearError`/`setError`, `counts = null`).
4. `tests/e2e/conversations.spec.ts` and `tests/e2e/settings.spec.ts` — how a connection or 4xx error is provoked (`page.route`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A failed conversations request is shown in the shell's error panel instead of rendering nothing.

## Contract

The layout's error panel (`data-testid="error-panel"`) shows `fetchError` from `setError`; `Superseded` is not an error. The same pattern is already used by Executions, Trends and Quality.

## Changes

Call `clearError()` on success, `setError(e)` on a non-`Superseded` rejection, and reset `rows`, `next` and `loaded` so no stale rows stay. The same handling goes in `Pager.svelte`'s page loads only if it is already missing there: do not edit `Pager` (not owned); report if it swallows errors. Add tests: a `page.route` that answers `/v1/analytics/conversations` with 500 shows `error-panel`; with a network abort shows the connection message; recovery on a retry (change the preset) clears the panel.

### Keep untouched

Virtualisation, test ids and the 1 s timing assertion.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm run test:e2e -- conversations.spec.ts` → the new error tests fail before and pass after; existing tests pass.
- `npm test` and `npm run build` → pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
