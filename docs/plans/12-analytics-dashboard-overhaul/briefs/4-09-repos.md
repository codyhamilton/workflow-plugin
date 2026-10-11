# Brief: 4-09 — Repos: a fixed number of requests, not one per repo

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/repos/+page.svelte`, `tests/e2e/repos.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-09-repos.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06 to 4-08, 4-10 to 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4409`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 6 files to read, about 150 lines to write, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Phase 4 outcome: "`/repos` issues one request, not one per repo" and "Domain: Dashboard site".
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01), `src/lib/charts/BarChart.svelte` (4-04) — exports and props only.
3. `src/routes/repos/+page.svelte` and `tests/e2e/repos.spec.ts` — the old facets-then-one-summary-per-repo fan-out and its test ids (`repo-<repo>-<field>`).
4. `tests/e2e/fixture.ts` — `SUMMARY_*`, `HOOKS_BY_REPO`, `REPOS`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The Repos table needs the same number of requests for two repos or two hundred.

## Contract

- One request cannot carry four measures, so the contract is: a fixed number of `/query` requests, one per column measure with `dim=repo_id`, `top=100`, `bucket=none`, independent of the repo count. Measures: `hook_events`, `conversations`, `artifact_versions`, `commits`. This is the loosest reading of DESIGN.md's "one request, not one per repo"; report it as such, do not hide it.
- Rows are `{k: [repo_id], v}`; join the four by repo. A repo missing from a measure has 0 for it. `__other__` (beyond top 100) is shown as a row and is not clickable.
- Clicking a repo row or bar calls `view.drill('repo_id', repo, ev)` (shift excludes). Test ids kept: `repo-<repo>-<field>` for each cell. The chart is `BarChart` `testid="repos-chart"` for `hook_events` by repo.

## Changes

Rewrite `+page.svelte` on `view` and the client; slots `repos-hook_events`, `repos-conversations`, `repos-artifact_versions`, `repos-commits`. Rewrite `repos.spec.ts` against the recounted fixture: the cell numbers equal the hand-counted per-repo values (derive none from `FACTS`); `trackRequests(page, /analytics\//)` counts four `analytics/query` requests (and no `analytics/summary`) on load; a `page.route` that fulfils each `analytics/query` with 40 invented repos still produces exactly four requests; a repo-row click adds a `repo_id` chip and shift-click an exclude chip whose table drops that repo; `__other__` is inert; the 1 s timing assertion.

### Keep untouched

The `repo-<repo>-<field>` ids and the numbers they assert.

## Done evidence

Run the old `repos.spec.ts` against the new page first and report which tests fail before you rewrite it.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- repos.spec.ts` → all pass, with the request-count tests.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
