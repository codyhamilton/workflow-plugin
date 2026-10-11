# Brief: 4-15 — Explore and Settings on the shared view state

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/explore/+page.svelte`, `src/routes/settings/+page.svelte`, `tests/e2e/explore.spec.ts`, `tests/e2e/settings.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-15-explore-settings.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06 to 4-14 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4415`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 7 files to read, about 120 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": Explore (Perspective), Settings; "Unchanged: `/settings` base URL and token behaviour, the non-JSON connection error".
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01, `client.clearCache`) — exports only.
3. `src/routes/explore/+page.svelte`, `src/routes/settings/+page.svelte`, `tests/e2e/explore.spec.ts`, `tests/e2e/settings.spec.ts`.
4. `tools/workflow/internal/serve/analytics.go` — the `explore` handler (cap 20,000 rows, `truncated`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Explore follows the shared window and filters like every other view, and changing the API connection clears cached data.

## Contract

- Explore stays Perspective (imported only in this route, so the other routes' bundles do not carry it). `explore` is a `rest` route (clamped to 399 days; the shell shows the notice) and capped at 20,000 rows: keep `explore-count`, `explore-truncated` and the capped text. Request via `getJSON('explore', 'analytics/explore', view.paramsFor('rest'))` and ignore `Superseded`.
- Settings: the base URL and token behaviour, the localStorage keys, and the non-JSON error message are unchanged. Saving settings calls `client.clearCache()` so cached responses from the old base URL are not shown. The cache key already includes the base URL, so this is a belt and braces step; do not add anything else.
- The unchanged contract is asserted by `settings.spec.ts` (bearer token, keyed serve across origins, 401 panel text); it must pass unmodified except for markup the shell changed.

## Changes

Update both routes accordingly. Update `explore.spec.ts`: the counts equal the recounted `total(SUMMARY_*)` (they derive from the fixture constants; recount by hand if 4-03 moved the constants, never edit to match), a `repo_id` chip narrows the slice and survives a reload, an exclude chip (`x.repo_id=r2`) resolves to the complement and narrows it, the capped-slice test still passes, the 1 s timing assertion. Update `settings.spec.ts` only where needed.

### Keep untouched

Everything `settings.spec.ts` asserts about the token, the base URL and the error text; the `perspective-viewer` loading code.

## Done evidence

Run the old `explore.spec.ts` and `settings.spec.ts` against the new routes first and report which tests fail before you change them.

- `npm test` and `npm run build` → pass; `npm run check:bundle` passes (run through `scripts/e2e-build.mjs` by the e2e run).
- `npm run test:e2e -- explore.spec.ts settings.spec.ts` → all pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
