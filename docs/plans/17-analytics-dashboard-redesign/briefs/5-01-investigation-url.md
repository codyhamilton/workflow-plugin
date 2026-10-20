# Brief: 5-01 — Investigation URL codec

Consumer: the phase 5 investigation URL worker.
Owned paths: `packages/yakka-analytics/src/lib/investigation/request-url.ts` (new), `packages/yakka-analytics/src/lib/investigation/request-url.test.ts` (new), `packages/yakka-analytics/src/lib/aggregate.ts` (type-only fixes listed below), `packages/yakka-analytics/src/lib/aggregate.test.ts` (only the `ConversationDetail` totals fixture fix listed below). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to origin branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/5-01-investigation-url.md` (handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: phases 2 and 3 (already on this branch).
Runs alongside: nothing.
Budget: 10 files to read, about 200 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Interactive analysis (investigation path and URL sentences), Domain: Aggregation boundary (request shape), Phase 5 outcome (URL round-trip sentence only).
2. `packages/yakka-analytics/src/lib/aggregate.ts` — `AggregateRequest`, `AggregateAsk`, `AggregateWindow`, `AggregateFilters`. Grep `toUrlState`; do not change runtime behaviour.
3. `packages/yakka-analytics/src/lib/urlstate.ts` — `parseUrlState`, `toSearch`, `DIM_KEYS`, filter param names (`x.<dim>` for excludes).
4. `packages/yakka-analytics/src/lib/presets.ts` — preset ids (grep `PRESETS` / `id`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Pure functions round-trip a boundary `AggregateRequest` through the page query string so phase 5 views can paste a URL and reproduce the same window, filters, and `ask`.

## Contract

Cited from `DESIGN.md`, Domain: Interactive analysis. Settled.

> The live investigation serialises into the query string: window, filters, and `ask`. Pasting that URL reproduces the investigation. The keys are the boundary request, not the old per-page keys (`metric`, `group`, `m`, `d`, `b`, `c`, and the report path).

Aggregation boundary request fields (same file, Domain: Aggregation boundary): `tenant` is not stored in the URL (session/bearer). `window` uses preset names from `src/lib/presets.ts` or explicit `from`/`to` with `tz`. `filters.include` / `filters.exclude` use the same dim keys as `urlstate` (`repo_id`, `harness`, `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`). Each `ask` variant matches `AggregateAsk` in `aggregate.ts`.

Settled: empty query on `/` is the landing; this unit does not implement routing UI.

## Changes

Add `request-url.ts` exporting at least:

- `isInvestigationQuery(params: URLSearchParams): boolean` — true when the query encodes an investigation (non-empty `ask` param is the discriminator).
- `parseInvestigationRequest(params: URLSearchParams, now?: Date): AggregateRequest` — builds `window`, `filters`, and `ask`. Reject or omit unknown `ask` values with a clear error type or throw; do not silently fall back to landing.
- `investigationRequestToSearch(request: AggregateRequest, now?: Date): URLSearchParams` — inverse of parse; stable key order is not required but round-trip must hold.

**Query key scheme** (boundary-shaped, not legacy report keys):

- Window: reuse `range`, `from`, `to` as `urlstate` does. Add `tz` when not the browser default is required for round-trip; if `tz` is omitted on write, parse may default to `UTC` only in tests with an explicit `now`.
- Filters: same include keys and `x.<dim>` exclude keys as `urlstate`.
- `ask` required for investigation: one of `trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, `executions`.
- Ask fields: `measure`, `bucket`, `dim`, `grain`, `kind`, `id` (conversation id) as required by each `AggregateAsk` variant. Use plain names (`measure`, not `m`).

Do not read or write `metric`, `group`, `m`, `d`, `b`, `c`, or `report` keys.

Round-trip tests must cover: trend with `hook_events` and `cost_usd`; trend with breakdown `dim=model`; breakdown on `repo_id`; distribution `cost_usd` grain `call`; quality `kind=design`; conversations; conversation with `id`; executions with optional `bucket`; include and exclude filters; preset `7d` and custom `from`/`to`.

**Carried type fixes (phase 3, behaviour unchanged):**

- In `aggregate.ts`, `unionMeta` calls that pass `Conversations` or `Executions` responses must only read `partial`, `ignored_filters`, and `truncated` when present (widen input or map to `MetaFields` without changing returned meta).
- In `aggregate.test.ts`, remove `hook_events` from `ConversationDetail.totals` in the fixture if `tsc` rejects it.

Do not add Svelte, routes, or chart imports.

### Keep untouched

`src/routes/`, `src/lib/analysis/`, `src/lib/views.ts`, `packages/yakka/internal/serve`, `packages/yakka/internal/store`. No HTTP or `aggregate()` behaviour changes beyond the `unionMeta` typing fix.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npm test -- src/lib/investigation/request-url.test.ts` → fails before the module exists, then passes all round-trip cases listed above.
- `cd packages/yakka-analytics && npx tsc --noEmit` → no TS2559 on `unionMeta` for conversations/executions; no TS2353 on conversation `totals` in `aggregate.test.ts`.
- `cd packages/yakka-analytics && npm test` → full unit suite still passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
