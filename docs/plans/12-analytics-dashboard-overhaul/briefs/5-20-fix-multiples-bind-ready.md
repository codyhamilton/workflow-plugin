# Brief: 5-20 — Fix the small-multiples crash from 5-18's `bind:ready`

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/lib/charts/SmallMultiples.svelte`, `packages/workflow-analytics/src/lib/charts/multi.test.ts`, `packages/workflow-analytics/tests/e2e/area.spec.ts`. Touch nothing else.
Commits: commit to the current branch when done evidence passes, plain-summary title, owned paths and the report only.
Report: before committing write `docs/plans/12-analytics-dashboard-overhaul/reports/5-20-fix-multiples-bind-ready.md` (rubric `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-19. Runs alongside: nothing in Phase 5 touches these paths.
Budget: 3 files to read, about 30 lines to change, 25 tool turns. Past the budget stop, write a handoff, report `over budget`.

Run npm commands from `packages/workflow-analytics`. Use `E2E_PORT=4520` for e2e.

## Goal

5-18 added `bind:ready={panelReady[panel.key]}` in `SmallMultiples.svelte` (line 79). In a browser this throws `props_invalid_value` (binding an undefined key of a `$state` record to a prop with no fallback), so the whole multiples subtree never renders and 5-19's `chart=multiples` + `expectSettled` assertion in `tests/e2e/area.spec.ts` fails. 5-5's SSR test could not see it.

## Contract

1. Make the panels render and report readiness: initialise each panel's `panelReady` key to `false` before it is bound (for example derive the record from `panels`), or replace the binding with an `onready` callback prop if the child cannot take a bound undefined; keep `data-ready` on the root equal to "every panel ready" (`"true"` when there are zero panels).
2. A test in `multi.test.ts` that would have caught this where possible (a client-side mount of `SmallMultiples` with two panels asserting no throw and ready becomes true); if the vitest environment cannot mount it, say so in the report and rely on item 3.
3. `area.spec.ts` multiples assertion passes in the browser (it is the failing check; report its output before and after).

## Done evidence

- `npm run test:e2e -- area.spec.ts builder.spec.ts` fails on multiples before, passes after.
- `npm test` and `npm run build` pass.

## Report back

Under 1,500 tokens: status, what changed, before/after output, deviations, contradictions. Never resolve a contradiction silently.
