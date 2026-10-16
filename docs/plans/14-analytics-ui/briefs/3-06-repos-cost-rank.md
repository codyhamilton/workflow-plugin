# Brief: 3-06 — Repos cost ranking

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/repos/+page.svelte`; `packages/workflow-analytics/tests/e2e/repos.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/3-06-repos-cost-rank.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-01-filter-bar-ten-dims, 3-02-overview-kpi-links, 3-03-time-chart-interactions, 3-08-builder-scalar-heatmap.
Budget: 6 files to read, about 80 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 3 outcome for `/repos`.
2. `packages/workflow-analytics/src/routes/repos/+page.svelte`.
3. `packages/workflow-analytics/tests/e2e/repos.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Repos can rank repositories by window cost while keeping the multi-measure table and repo drill behavior.

## Contract

Phase 3 outcome:

- On `/repos`, a control ranks the repos by `cost_usd`. A repo click filters.

Existing drill contract: `repo_id` is a shared filter; `__other__` inert (already implemented).

## Changes

- Add a ranking control (select or toggle) defaulting to `hook_events` for backward compatibility or defaulting to `cost_usd` per outcome — outcome requires the control can rank by `cost_usd`; preserve table sort when ranking measure changes.
- Fetch `cost_usd` with `dim=repo_id`, `bucket=none`, `top=100` alongside the four existing measures (five query calls total).
- Bar chart `rows` use the selected ranking measure’s values; table still shows all four count columns plus cost if you add a cost column, or keep table and only change chart ranking — minimum: chart ranks by `cost_usd` when selected.
- Repo row/chart click continues `view.drill('repo_id', …)`.

### Keep untouched

Other routes and chart components.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/repos.spec.ts` from `packages/workflow-analytics` → passes, including an updated load test expecting five `/analytics/query` requests when cost ranking is enabled, and a test that selecting cost ranking orders the bar chart by fixture repo costs.
- Existing repo drill and `__other__` inert tests → still pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
