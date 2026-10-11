# Brief: 4-10 — Hooks: harness, repo, event and tool bars plus the harness, norm_event and tool treemaps

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/hooks/+page.svelte`, `tests/e2e/hooks.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-10-hooks.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06 to 4-09, 4-11 to 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4410`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 8 files to read, about 250 lines to write, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": Hooks (harness → norm_event → tool treemap), drill-down rules; Phase 4 outcomes "Clicking a harness bar adds a `harness` filter chip, and shift-clicking excludes it" and "The 7d preset chosen on Overview persists when navigating to Hooks". The Amendment: `hook_events` counts parts from `message.part.updated`; no delta rows exist.
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01), `src/lib/charts/BarChart.svelte` and `Treemap.svelte` (4-04) — exports and props only.
3. `src/routes/hooks/+page.svelte` and `tests/e2e/hooks.spec.ts` — old test ids `hooks-<g>-<k>` and `hooks-<g>-row-<k>`; fixture constants `HOOKS_BY_*`.
4. `tools/workflow/internal/serve/analytics_query.go` — the `/schema` handler: which dims `hook_events` supports.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Hooks shows where hook activity comes from, and every bar, row and treemap leaf narrows the whole dashboard when clicked.

## Contract

- `/query` allows at most two `dim` parameters, so a three-level tree needs more than one request. The page shows two linked two-level treemaps: A is `hook_events` by `harness` then `norm_event`; B is `hook_events` by `norm_event` then `tool`. This is the realisation of DESIGN.md's "harness → norm_event → tool treemap" under the two-dimension cap; report it as a deviation in the verdict, do not hide it.
- Bars (`BarChart`, `top=20`, `bucket=none`): by `harness` (`testid="hooks-harness"`), `repo_id` (`hooks-repo_id`), `event` (`hooks-event`), `tool` (`hooks-tool`). The empty string key (hooks with no tool) is shown as `(none)` via `label()` and is clickable with the value `''`. Six `/query` requests in all (four bars, two treemaps); slots `hooks-harness`, `hooks-repo_id`, `hooks-event`, `hooks-tool`, `hooks-treemap-a`, `hooks-treemap-b`.
- Drill-down: bar click → `view.drill(dim, key, ev)`; shift-click excludes; treemap leaf click → drill each element of its path (`harness`, `norm_event` for A; `norm_event`, `tool` for B), shift excludes. `__other__` is not clickable.
- A `kind` filter does not apply to `hook_events`: the server returns `ignored_filters: ["kind"]` and the shell shows the notice; the page does nothing extra.
- Preset persistence: the page reads only `view`, so the 7d window chosen elsewhere applies here.

## Changes

Rewrite `+page.svelte` on `view`, the client, `BarChart` and `Treemap`. Keep the `hooks-<g>-<k>` and `hooks-<g>-row-<k>` ids on the table view of each bar chart if 4-04's `DataTable` allows a row id prefix; otherwise rewrite the spec to read rows from `<testid>-table`. Rewrite `hooks.spec.ts` against the recounted `HOOKS_BY_*`: each bar's table equals the hand count; `clickBar(page, 'hooks-harness', 0)` adds a `harness` chip and the URL gains `harness=<name>` and the other bars narrow; the same with `shift` adds `data-mode="exclude"` and the harness bar then omits that harness; with `?range=7d` set on `/` and a nav click to Hooks the URL keeps `range=7d`; a treemap A leaf click (through the table toggle row) adds two chips; `__other__` is inert (use `page.route`); the 1 s timing assertion from click to `expectSettled`.

### Keep untouched

The per-dimension numbers asserted today, now from the recounted fixture.

## Done evidence

Run the old `hooks.spec.ts` against the new page first and report which tests fail before you rewrite it.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- hooks.spec.ts` → all pass, including the shift-click exclude and the 7d persistence test.
- `trackRequests(page, /analytics\/query/)` reports six requests for one load.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
