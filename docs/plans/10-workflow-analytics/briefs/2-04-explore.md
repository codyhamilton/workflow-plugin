# Brief: 2-04 — Explore pivot (Perspective)

Consumer: a worker dispatched by the plan 10 phase 2 orchestrator. The orchestrator verifies the phase outcome by running this unit's e2e spec with the rest of the suite.
Owned paths: `packages/workflow-analytics/src/routes/explore/`, `packages/workflow-analytics/vite.config.ts` (only additions Perspective's WASM/worker loading needs), `packages/workflow-analytics/tests/e2e/explore.spec.ts`, plus `docs/plans/10-workflow-analytics/reports/2-04-explore.md`. Touch nothing else — in particular not `package.json` or `package-lock.json` (2-01 installed the Perspective packages; if one is missing, report `blocked` naming it), `svelte.config.js`, `src/lib/` (any file), the root layout, or `tests/e2e/fixture.ts`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/2-04-explore.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 2-01, 2-02 and 2-03 (committed on this branch; their routes and specs must keep passing).
Runs alongside: nothing (shares the e2e harness's `build/` directory and ports; runs after 2-03).
Budget: 10 files to read, about 400 lines to write including the spec, 70 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — the `explore` contract (lines 163-173), "Domain: Analytics site" (181-187), Phase 2 Outcome (line 290). Binding.
2. `docs/plans/10-workflow-analytics/reports/2-01-site-shell.md` — client, filter helpers, fixture exports, Perspective package versions, how to run the suites.
3. `packages/workflow-analytics/src/routes/+page.svelte` — the overview, as the idiom for a report route.
4. `packages/workflow-analytics/src/lib/api.ts`, `src/lib/filters.ts`, `src/lib/types.ts`, `tests/e2e/fixture.ts`, `tests/e2e/helpers.ts` — by export list first (`grep -n export`).
5. The installed Perspective packages' READMEs and `package.json` `exports` under `node_modules/@perspective-dev/` — how a Vite app loads the client/server WASM and registers `<perspective-viewer>` and its datagrid plugin.

Run commands from `packages/workflow-analytics`; Go is at `~/.local/go/bin`. Read ranges and grep; do not read a whole file to find one section, and truncate long tool output.

## Goal

`/explore` loads the capped fact slice for the URL filter into an embedded Perspective viewer and states plainly when the slice is capped.

## Contract

- "`/explore` loads the JSON `rows` into Perspective (`@perspective-dev/client` and `@perspective-dev/viewer`, Apache-2.0) and shows that viewer. When `truncated` is true, the page shows that the slice is capped, not a silent prefix. No second chart grammar and no SQL editor."
- `GET /v1/analytics/explore` returns `{"rows":[{}],"truncated":false}`; columns "and only these: `type`, `ts`, `harness`, `repo_id`, `plan`, `kind`, `event`, `tool`, `path`, `conversation_id`, `source`, `sha`, `screen_verdict`, `rejection_stage`"; "The response stops at 20,000 rows and sets `truncated` true when more rows match."
- "Charts on the fixed routes use LayerChart … Perspective only on `/explore`" (Solution Shape, Decisions).

Decisions settled at refine (do not re-derive):

1. **Loading:** Perspective is imported dynamically inside the `/explore` route (`onMount` + `import()`), so no other route downloads its JS or WASM. The viewer's datagrid plugin is the default view.
2. **Data:** one `GET /v1/analytics/explore` with the shared filter; the rows go into a Perspective table with an explicit schema where all 14 columns are `string` except `ts`, which is `datetime` (parse the RFC3339 string). A filter change replaces the table's data (or rebuilds it) without a full page reload.
3. **Cap notice:** when `truncated` is true, a banner above the viewer with `data-testid="explore-truncated"` says the slice is capped at the returned row count (newest first) and suggests narrowing the window or filters. When false, the banner is absent. A `data-testid="explore-count"` shows the loaded row count either way.
4. **Viewer layout:** the viewer fills the content area at a fixed minimum height; Perspective's own theme CSS, imported from the installed package. No custom pivot UI around it.
5. **`vite.config.ts`:** add only what Perspective needs (for example `optimizeDeps.exclude`, a WASM/worker asset rule, `build.target` for top-level await). If 2-01's config already works, change nothing.

### Keep untouched

2-01's files listed under Owned paths, and 2-02's / 2-03's routes. If a shared file needs a change, report it as a gap.

## Done evidence

Write the failing spec first and report its output before and after. Why: this is the outcome's `/explore` clause — the pivot shows the API's rows, a capped slice is never a silent prefix, and the heavy WASM stays off the fixed reports.

- `npm run test:e2e -- explore.spec.ts` → passes, with at least:
  - against the local serve, `/explore` renders `perspective-viewer`, `explore-count` equals the fixture's fact count plus its rejection count, the viewer's table size (read via `page.evaluate` on the element's `getTable()` → `size()`) equals the same number, and `explore-truncated` is absent;
  - `/explore?repo_id=<repo>` shows the filtered count and survives `page.reload()`;
  - with `page.route` stubbing `/v1/analytics/explore` to three rows and `truncated: true`, `explore-truncated` is visible and the count is 3;
  - loading `/` (overview) makes no request whose URL contains `perspective` or ends in `.wasm`.
- `npm run build && npm run check:bundle` (with the `E2E_FORBIDDEN` the 2-01 report names) → passes.
- `npm run test:e2e` (whole suite) → passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence (including in phase 1's routes or 2-01's shell): report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
