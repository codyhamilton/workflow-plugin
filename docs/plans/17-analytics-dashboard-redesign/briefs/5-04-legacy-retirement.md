# Brief: 5-04 — Legacy routes and shell retirement

Consumer: the phase 5 legacy-retirement worker.
Owned paths: `packages/yakka-analytics/src/routes/+layout.svelte`, `packages/yakka-analytics/src/lib/analysis/routes.ts`, `packages/yakka-analytics/src/routes/trends/+page.svelte`, `packages/yakka-analytics/src/routes/builder/+page.svelte`, `packages/yakka-analytics/src/routes/usage/+page.svelte`, `packages/yakka-analytics/src/routes/repos/+page.svelte`, `packages/yakka-analytics/src/routes/hooks/+page.svelte`, `packages/yakka-analytics/src/routes/quality/+page.svelte`, `packages/yakka-analytics/src/routes/executions/+page.svelte`, `packages/yakka-analytics/src/routes/conversations/+page.svelte`, `packages/yakka-analytics/src/routes/conversation/+page.svelte`, `packages/yakka-analytics/src/routes/explore/+page.svelte`, `packages/yakka-analytics/src/routes/dashboards/+page.svelte`, `packages/yakka-analytics/tests/e2e/helpers.ts` (only `useServe` init-script fix), `packages/yakka-analytics/tests/e2e/shell.spec.ts`, `packages/yakka-analytics/tests/e2e/trends.spec.ts`, `packages/yakka-analytics/tests/e2e/usage.spec.ts`, `packages/yakka-analytics/tests/e2e/repos.spec.ts`, `packages/yakka-analytics/tests/e2e/quality.spec.ts`, `packages/yakka-analytics/tests/e2e/conversations.spec.ts`, `packages/yakka-analytics/tests/e2e/conversation.spec.ts`, `packages/yakka-analytics/tests/e2e/explore.spec.ts`, `packages/yakka-analytics/tests/e2e/dashboards.spec.ts`, `packages/yakka-analytics/tests/e2e/phase5.spec.ts`, `packages/yakka-analytics/tests/e2e/interactions.spec.ts`, `docs/design/07-analytics-site.md` (route table, Chart builder, Saved views and dashboards, and any sentences this phase supersedes). Touch nothing else except deleting or gutting legacy-only imports on the owned route files.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to origin branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/5-04-legacy-retirement.md` (handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `5-03-exploration-tools` (investigation must expose the jobs before nav removal).
Runs alongside: nothing.
Budget: 25 files to read, about 500 lines to change, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Interactive analysis (non-goals, old modules list); Phase 5 outcome (old routes and report nav).
2. `packages/yakka-analytics/src/routes/+layout.svelte` — nav, `FilterBar`, `SaveView`, `legacyReport`.
3. `packages/yakka-analytics/src/lib/analysis/routes.ts` — `isLegacyReportPath`.
4. `docs/design/07-analytics-site.md` — route table and saved-view/dashboard paragraphs.
5. `packages/yakka-analytics/tests/e2e/helpers.ts` — `useServe` (carried nested-array bug).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The report nav and per-report filter chrome leave the shell. Legacy report URLs no longer render the old analytics pages; investigation on `/` is how those jobs are reached. Design 7 documents the new route story.

## Contract

Cited from `DESIGN.md`, Phase 5 outcome. Settled.

> Opening `/trends`, `/usage`, `/repos`, `/hooks`, `/quality`, `/executions`, `/conversations`, `/conversation`, `/explore`, `/builder`, and `/dashboards` does not render those reports, and the report nav is not in the shell.

Domain non-goals (same file): no port of old pages with new paint; no twelve-tile grid; no dedicated `/explore`; no `{ report, params }` saved-view record for the new saved-analysis tool.

`/profile`, `/settings`, `/login`, `/device`, `/oauth/callback` stay. Theme controls may stay in the header.

## Changes

**Layout:** Remove the report nav links (Trends, Builder, Usage, Repos, Hooks, Quality, Executions, Conversations, Explore, Dashboards). Remove `FilterBar`, `FilterChips`, `SaveView`, and legacy solarized wrapper for report paths from the main chrome on `/` and investigation. Keep session gate, theme, errors, and `RouteSurface` for identity routes. Investigation and landing on `/` use analysis tokens only.

**Legacy routes:** Replace each owned `+page.svelte` listed in Owned paths with a minimal redirect or stub that does not mount the old report UI (e.g. `goto('/')` or a short “Analysis moved to Overview” with link to `/`). Do not delete route folders (URLs may still be hit).

**`routes.ts`:** Drop or empty `LEGACY_REPORT_PREFIXES` so `/` investigation is not treated as legacy solarized.

**`helpers.ts`:** Fix `useServe` so `addInitScript` receives a flat args list; local base must be `http://127.0.0.1:<port>` without `,,e2e-local-stay` (carried from phase 4).

**Tests:** Retire or rewrite owned e2e files so CI does not expect old report UIs. Prefer consolidating proof into `investigation-shell.spec.ts` and `investigation-tools.spec.ts` where overlap exists; delete `phase5.spec.ts` builder/dashboard tests that contradict Assumption 2. Remove or rewrite `shell.spec.ts` cases that depended on report nav and `SaveView` (`dashboards shares filter chrome`, `a saved view is listed…`) — they should pass or be removed with justification in the report.

**Design 7:** Update the route table: `/` is landing + investigation; list legacy paths as redirected or non-report; replace Chart builder / Saved views and dashboards paragraphs to describe investigation URL state and `saved-analysis` localStorage, not `{ report, params }` dashboards.

Do not remove `src/lib/views.ts` unless nothing imports it; orphan code may remain if unused.

### Keep untouched

`src/lib/aggregate.ts`, `src/lib/investigation/` (except imports from layout if any), `packages/yakka/internal/serve`, `packages/yakka/internal/store`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npx playwright test tests/e2e/investigation-shell.spec.ts tests/e2e/investigation-tools.spec.ts tests/e2e/overview.spec.ts tests/e2e/session.spec.ts` → passes.
- `cd packages/yakka-analytics && npx playwright test tests/e2e/explore.spec.ts` → passes after `useServe` fix (or file removed if explore route is gone — report which).
- For each legacy path `/trends`, `/usage`, `/quality`, `/conversations`, `/builder`, `/dashboards`, `/explore`: `page.goto` does not show legacy test ids such as `builder-chart`, `dash-tile`, `trends-chart`, or solarized-only report titles from the old pages.
- Observable: header nav has no “Trends” or “Dashboards” link; `data-testid` `saveview-save` is absent on `/`.
- `cd packages/yakka-analytics && npm test` → passes.
- `git diff --name-only` against parent commit includes no path under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
