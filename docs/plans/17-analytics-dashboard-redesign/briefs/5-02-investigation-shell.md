# Brief: 5-02 — Investigation shell and landing handoff

Consumer: the phase 5 investigation shell worker.
Owned paths: `packages/yakka-analytics/src/routes/+page.svelte`, `packages/yakka-analytics/src/lib/investigation/` (new tree except `tools/` — create `tools/.gitkeep` or leave absent), `packages/yakka-analytics/tests/e2e/investigation-shell.spec.ts` (new), `packages/yakka-analytics/tests/e2e/overview.spec.ts` (only to keep landing checks passing alongside investigation). Touch nothing else except imports from modules this unit owns or from `5-01` (`request-url`).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to origin branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/5-02-investigation-shell.md` (handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `5-01-investigation-url`, phase 4 landing (already on branch).
Runs alongside: nothing.
Budget: 18 files to read, about 600 lines to change, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Landing trend view; Domain: Interactive analysis (first four bullets through drill/shift); Phase 5 outcome (landing vs investigation, brush, breakdown, drill, exclude, URL).
2. `packages/yakka-analytics/src/lib/investigation/request-url.ts` — `isInvestigationQuery`, `parseInvestigationRequest`, `investigationRequestToSearch`.
3. `packages/yakka-analytics/src/routes/+page.svelte` — current landing-only implementation.
4. `packages/yakka-analytics/src/lib/aggregate.ts` — `aggregate`, result types for `trend` and `breakdown`; grep `controls`, `ignored_filters`.
5. `packages/yakka-analytics/src/lib/analysis/chart-frame/` — `TrendChart`, `BreakdownChart`, `drill.ts`, callback types.
6. `docs/design/07-analytics-site.md` — Drill-down bullet (grep `shift-click`, `__other__`).
7. `packages/yakka-analytics/tests/e2e/overview.spec.ts` — landing assertions to preserve.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

`/` shows the phase 4 landing when the query is empty. A control opens the investigation on the same window with `hook_events` and `cost_usd` encoded in the URL. With an investigation query, one graph reads through `aggregate`, updates on window brush, breakdown dim change, drill, and shift-click exclude, and syncs the live request back to the address bar.

## Contract

Cited from `DESIGN.md`, Domain: Interactive analysis. Settled.

> Empty query on `/` is the landing. The investigation path is `/` with an `ask` query: window, filters, and `ask` are the boundary request. A control on the landing trend opens it on the landing window and on `hook_events` and `cost_usd`.
>
> The graph is interactive. Changing the window (a preset, or a brush on a time axis) and changing a breakdown dim ask the aggregation boundary again, and the graph updates from that result. Drill applies a real filter dim. `__other__`, the empty key, `hour_of_day`, and `weekday` are not filters (design 7, Drill-down). Shift-click excludes where the boundary can express an exclude.

Assumption 2: repo, harness, hook, and execution shape are breakdown dims inside this investigation, not separate routes. This unit provides a breakdown dim control that can set `ask: trend` or `ask: breakdown` / `ask: executions` per design boundary shapes; it does not build usage, quality, conversation, or saved-analysis tool UIs (phase `5-03`).

Phase 5 outcome (URL): pasting the address reproduces window, filters, and ask; keys are the boundary request (`5-01` codec).

## Changes

**`+page.svelte`:** Branch on `isInvestigationQuery(page.url.searchParams)`. Empty query: keep two landing trends (phase 4 behaviour) and add a visible control (e.g. “Investigate” / “Open analysis”) that `goto`s to `/` with `investigationRequestToSearch` for the resolved landing window (`{ tz }` thirty-day judgement), filters empty, and an initial investigation ask that shows both `hook_events` and `cost_usd` (two trend charts or one combined layout — both measures must be visible without leaving `/`). Non-empty investigation query: render the investigation shell instead of landing.

**Investigation shell** under `src/lib/investigation/` (no `tools/` yet):

- Load session tenant like landing (`sessionGate`, `isCollectorMode`, `tenantNameFromMe`).
- Parse URL → `AggregateRequest` via `5-01`; on change, `replaceState` / `goto` with updated search from `investigationRequestToSearch`.
- Window controls: at least presets from `presets.ts` and brush-end from `TrendChart` / quality series when present; brush sets custom `from`/`to` on the request.
- Breakdown dim selector using `result.controls` from `aggregate` (facet lists); changing dim updates `ask` (`trend` with `dim`, or `breakdown`, or `executions` with bucket when that shape fits the selected exploration).
- Wire `ondrill` / shift-click via `isDrillableMark` and `applyDrill` logic equivalent to `urlstate.applyDrill` on the request’s filter maps, then re-fetch.
- Show `ignored_filters` (including `conversation_id` on shift-exclude) with a notice test id `notice-ignored` when non-empty.
- Use chart frame components only (`$lib/analysis/chart-frame`), not `$lib/charts/`.
- Call `aggregate` only; no `getJSON` in the route or shell.

Do not implement usage/cost, quality, conversation list/detail, or saved-analysis panels. A minimal tool strip may say “coming” or hide those entries; `5-03` adds them.

### Keep untouched

`src/routes/+layout.svelte`, legacy report routes, `src/lib/views.ts`, `src/lib/components/SaveView.svelte`, `packages/yakka/internal/serve`, `packages/yakka/internal/store`. Do not remove report nav (phase `5-04`).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npx playwright test tests/e2e/overview.spec.ts` → still passes (empty `/` landing).
- `cd packages/yakka-analytics && npx playwright test tests/e2e/investigation-shell.spec.ts` → new file; fails before implementation, then passes:
  - From landing, control opens `/?` with investigation query; both `hook_events` and `cost_usd` charts or sections visible.
  - Changing a preset triggers a new `aggregate` read (listen for `analytics/query` or `analytics/facets`) and updates `range` or `from`/`to` in the URL.
  - Drill on a drillable dim adds a filter param; `__other__` drill does not.
  - Shift-click exclude adds `x.<dim>` when supported; shift-exclude `conversation_id` shows `notice-ignored` when `ignored_filters` contains `conversation_id`.
  - Copy URL in browser, new page load reproduces the same `ask` and filter params.
- `cd packages/yakka-analytics && npm test` → passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
