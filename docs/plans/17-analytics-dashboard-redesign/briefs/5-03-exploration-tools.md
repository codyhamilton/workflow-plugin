# Brief: 5-03 — Exploration tools (usage, quality, conversations, saved analysis)

Consumer: the phase 5 exploration-tools worker.
Owned paths: `packages/yakka-analytics/src/lib/investigation/tools/` (new), `packages/yakka-analytics/src/lib/saved-analysis.ts` (new), `packages/yakka-analytics/src/lib/saved-analysis.test.ts` (new), `packages/yakka-analytics/src/lib/investigation/InvestigationShell.svelte` (or the single shell Svelte file `5-02` introduced — grep `investigation` under `src/lib/investigation/` and edit only that shell entry and a new `tools/registry.ts` in the same folder), `packages/yakka-analytics/tests/e2e/investigation-tools.spec.ts` (new). Touch nothing else except chart-frame and `format.ts` imports (read-only).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to origin branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/5-03-exploration-tools.md` (handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `5-02-investigation-shell`.
Runs alongside: nothing.
Budget: 22 files to read, about 700 lines to change, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Interactive analysis (Usage and cost, Quality, Conversation grain, Saved analysis bullets); Assumption 2; Phase 5 outcome sentences for those tools.
2. `packages/yakka-analytics/src/lib/investigation/` — shell from `5-02` and `request-url.ts`.
3. `packages/yakka-analytics/src/lib/aggregate.ts` — `distribution`, `quality`, `conversations`, `conversation` result shapes.
4. `packages/yakka-analytics/src/lib/analysis/chart-frame/` — `DistributionChart`, `QualityChart`, trend/breakdown for usage.
5. `packages/yakka-analytics/src/lib/format.ts` — `costLabel` (design 7 Cost / unpriced).
6. `packages/yakka-analytics/src/routes/usage/+page.svelte`, `quality/+page.svelte`, `conversations/+page.svelte`, `conversation/+page.svelte` — grep unpriced, window_totals, in-window marking (behaviour to match, not files to extend).
7. `packages/yakka-analytics/src/lib/views.ts` — grep `SavedView` (old `{ report, params }` shape to replace for saved analysis only).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Inside the investigation on `/`, four tools return: usage and cost (one tool), quality, conversation grain, and saved analysis. Each tool drives the same URL/boundary request model and chart frame; saved analysis stores `{ id, name, spec }` in `localStorage` and reopens on the investigation path.

## Contract

Cited from `DESIGN.md`, Domain: Interactive analysis. Settled.

> **Usage and cost** are one tool. Model against model, tokens and `cost_usd`, over time (`ask: trend` with dim `model`) and as a distribution (`ask: distribution`, grain `call`). Unpriced cost is shown as unpriced, not as zero (design 7, Cost).
>
> **Quality** is one tool. One kind `design`, `brief`, or `report`: the window score distribution beside the all-time baseline, and the score series for the bucket (`ask: quality`). A bucket with no point is a gap.
>
> **Conversation grain** is one tool. The window's conversations (`ask: conversations`), with model and cost on the row, and one run (`ask: conversation`): the event list is the whole run, events inside the window are marked, `totals` is the run, and `window_totals` is present when a window is set (design 7, conversation read).
>
> **Saved analysis** is one tool. The person saves the investigation and opens it again by name. Stored record: `{ id, name, spec }` where `spec` is the boundary request that reproduces it (the `ask`, the window, and the filters). It is not `{ report, params }` with `report` one of `overview`, `trends`, `usage`, … Persistence is client-side (`localStorage`). There is no server view store. Opening one stays inside the investigation.

Assumption 2: repos, hooks, executions remain breakdowns in the shell; this unit does not add standalone repo/hook/explore/dashboard routes.

## Changes

**Tool strip** in the investigation shell: switch tool by updating the investigation `AggregateRequest` / URL (no `/usage` navigation). Register four tools under `investigation/tools/`:

1. **Usage and cost** — UI to flip between model-over-time (`ask: trend`, `measure` token measures and `cost_usd`, `dim: model`) and distribution (`ask: distribution`, `grain: call`, optional `dim: model`). Table or chart labels use `costLabel`; zero priced cost with unpriced calls must read `unpriced`, never `$0.00` when all calls are unpriced (match `usage.spec.ts` expectations in spirit on the investigation surface). Test ids prefixed `investigation-usage-` where you assert unpriced.

2. **Quality** — kind selector `design` | `brief` | `report`; `QualityChart` with window scores vs baseline; bucket selector for `ask: quality`; empty buckets render as gaps in the series.

3. **Conversation grain** — list from `ask: conversations` with model and cost columns; row opens `ask: conversation` with `id` in the request/URL. Event list shows full run; mark in-window events; show `totals` and `window_totals` when the boundary returns them (do not “fix” server second bugs).

4. **Saved analysis** — `saved-analysis.ts`: `list`, `save`, `remove`, `get` with `localStorage` key distinct from legacy `views.ts` (`yakka-analytics-saved-analysis` or similar). `spec` is `AggregateRequest` JSON-serializable (no `tenant` required in storage). UI: name field, save, open by name; opening applies `spec` via `investigationRequestToSearch` and stays on `/`.

Wire tools only through `aggregate` and chart frame; no `$lib/charts/`, no `getJSON` in tools.

Do not delete `views.ts` or old routes here (`5-04`).

### Keep untouched

`src/routes/+layout.svelte`, legacy `src/routes/*` report pages, `packages/yakka/internal/serve`, `packages/yakka/internal/store`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npm test -- src/lib/saved-analysis.test.ts` → passes save/list/open round-trip.
- `cd packages/yakka-analytics && npx playwright test tests/e2e/investigation-tools.spec.ts` → fails before tools exist, then passes:
  - Usage tool: unpriced model shows `unpriced` not `$0.00` (fixture model `ollama-maxctx/qwen3-coder:30b-a3b-q4_K_M` or equivalent).
  - Quality tool: baseline visible beside window distribution for `design`.
  - Conversations: list row links to detail with events; in-window marker on at least one event when fixture window overlaps.
  - Saved analysis: save current investigation, reload, open by name restores query params for `ask` and window.
- `cd packages/yakka-analytics && npm test` → passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
