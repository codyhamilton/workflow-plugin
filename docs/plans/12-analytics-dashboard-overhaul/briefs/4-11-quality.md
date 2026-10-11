# Brief: 4-11 — Quality: scores with exactly one kind, on the shared client

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/quality/+page.svelte`, `tests/e2e/quality.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-11-quality.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06 to 4-10, 4-12 to 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4411`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 6 files to read, about 150 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": Quality view.
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01), `src/lib/params.ts` (`scoresParams`, 4-02) — exports only.
3. `src/routes/quality/+page.svelte` and `tests/e2e/quality.spec.ts` — test ids `quality-kind-*`, `q-row`, `q-<check>-w-<f>`, `q-<check>-b-<f>`.
4. `tools/workflow/internal/serve/analytics.go` — the `scores` handler (`scoresKind` makes `kind` required) and the `baselines` route.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Quality shows the same scores and baselines as before, always asking for exactly one kind, on the shared window and filters, without redundant requests.

## Contract

- `scores` answers `400 "kind required"` unless exactly one `kind` is sent. The selected kind is the first `kind` include in the URL, default `design`; `scoresParams(params, kind)` (4-02) sets it. The `kind` kind tabs call `view.setInclude('kind', [k])`.
- `scores` is a `rest` route: the window is clamped to 399 days (the shell shows `notice-clamped` for All time). The `baselines` request is all-time and takes only `kind`, as today; it goes through the client so it is cached per kind.
- Keep the table markup and ids: `quality-kind-<kind>`, `q-row`, `q-<check>-w-<f>`, `q-<check>-b-<f>`. No chart is added: Quality is a table in the design.
- `scores` is fast only after `ANALYZE facts` has run (Phase 3 Carried item 4); that is server-side and not this unit's concern.

## Changes

Rewrite `+page.svelte` to use `view.paramsFor('rest')`, `scoresParams`, `getJSON` with slots `quality-scores` and `quality-baselines`, and `view.setInclude`. Update `quality.spec.ts` for the shell: kind tabs set the URL's `kind`, a fixture with no `kind` in the URL requests `kind=design` (`trackRequests`), switching kind issues one `scores` request, a request without `kind` is never sent, the 1 s timing assertion. Existing numeric assertions stay unless 4-03's recount moved them (recount by hand; never edit a number to match a failing run).

### Keep untouched

The test ids above and the numbers they assert.

## Done evidence

Run the old `quality.spec.ts` against the new page first and report which tests fail before you change it.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- quality.spec.ts` → all pass.
- Every `analytics/scores` request in the run carries exactly one `kind` (assert in the spec).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
