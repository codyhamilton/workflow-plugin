# Brief: 4-06 — E2E fixture pricing alignment

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/tests/e2e/fixture.ts`; `packages/workflow-analytics/tests/e2e/overview.spec.ts`; `packages/workflow-analytics/tests/e2e/usage.spec.ts`; `packages/workflow-analytics/tests/e2e/interactions.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/4-06-e2e-pricing-fixture.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 4-01-quality-score-series, 4-05-explore-usage-columns.
Budget: 6 files to read, about 120 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/IMPLEMENTATION.md` — Phase 3 Carried (opus pricing vs e2e expectations).
2. `packages/workflow-analytics/tests/e2e/fixture.ts` — `USAGE_ALL`, `USAGE_BY_MODEL`, facts for `claude-opus-5-5`.
3. `tools/workflow/internal/store/` — grep pricing for `claude-opus-5-5` (read the price table or lookup used at read time; do not change Go).
4. Failing specs: `overview.spec.ts`, `usage.spec.ts`, `interactions.spec.ts` — assertions for opus and unpriced counts.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Hand-counted e2e expectations match the synthetic serve’s read-time pricing so overview and usage specs assert the numbers the API actually returns.

## Contract

No DESIGN.md product outcome — this unit closes Phase 3 carried test debt only. The store prices `claude-opus-5-5`; specs must not treat that model as unpriced. Recount `USAGE_ALL`, `USAGE_BY_MODEL`, and any summary tile strings from `FACTS` using the same pricing rules as the server.

## Changes

- Update `fixture.ts` constants (`unpriced_calls`, `cost_usd`, per-model rows) to reflect priced opus where the store assigns a non-zero price; keep qwen (or other genuinely unpriced models) as unpriced.
- Update overview, usage, and interactions expectations (`$0.13` opus line, `1 unpriced`, etc.) to match recomputed constants — prefer importing from `fixture.ts` over literals where specs already do.
- Do not change product UI or Go pricing tables.

### Keep untouched

Application source under `src/`, other e2e specs unless a shared constant forces a one-line import fix.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- From `packages/workflow-analytics`: `E2E_PORT=4401 npx playwright test tests/e2e/overview.spec.ts tests/e2e/usage.spec.ts tests/e2e/interactions.spec.ts` → all pass (was 5 failures on opus/unpriced before this unit).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
