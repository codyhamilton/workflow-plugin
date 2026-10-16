# Brief: 3-01 — Filter bar ten dimensions

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/lib/components/FilterBar.svelte`; `packages/workflow-analytics/src/lib/view.svelte.ts` (`mapFacets` only); `packages/workflow-analytics/tests/e2e/filter-bar.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/3-01-filter-bar-ten-dims.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-02-overview-kpi-links, 3-03-time-chart-interactions, 3-06-repos-cost-rank, 3-08-builder-scalar-heatmap.
Budget: 8 files to read, about 120 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Domain: Report interaction (shared filter keys, exclude on `conversation_id`), and Phase 3 outcome bullet on the filter bar.
2. `packages/workflow-analytics/src/lib/urlstate.ts` — `DIM_KEYS`.
3. `packages/workflow-analytics/src/lib/components/FilterBar.svelte` — current five-dimension pattern.
4. `packages/workflow-analytics/src/lib/view.svelte.ts` — `mapFacets` and facet fields from `GET /v1/analytics/facets`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The shared filter bar exposes all ten shared filter dimensions from the interaction contract, with exclude on `conversation_id` labelled as unsupported.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Domain: Report interaction:

- Shared filter keys stay `repo_id`, `harness`, `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`. The filter bar offers every one of them. Exclude stays the facet complement. Exclude on `conversation_id` stays unsupported and labelled so.

Phase 3 outcome: The filter bar lists all ten shared dimensions.

## Changes

- Replace the hard-coded five-key `MULTIS` list with controls for every `DimKey` in `DIM_KEYS`, using the same multi-select + `view.drill` / `view.removeChip` pattern as today.
- Labels: human-readable captions for `norm_event`, `event`, `tool`, `source`, `conversation_id` (match the tone of existing Repo/Harness labels).
- Options: keep `options(key)` — facet values plus URL-selected values, never an empty-string option.
- `mapFacets`: map `norm_events` → `norm_event`, `events` → `event`, `tools` → `tool` (tool names). The facets route does not list `source` or `conversation_id`; those controls still render and show URL-selected values only.
- On the `conversation_id` control, show a short note that shift-click exclude is not applied (chips already say “(not applied)” via `FilterChips.svelte`; the bar label or hint should match the contract’s “labelled so”).
- Do not add server or facets API changes (out of phase surfaces).

### Keep untouched

Chip rendering, `params.ts` filter encoding, and routes other than imports of `FilterBar`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/filter-bar.spec.ts` from `packages/workflow-analytics` → passes; tests assert `data-testid="filter-<key>"` exists for all ten keys, selecting a facet-backed value updates the URL, and the conversation_id control shows the unsupported-exclude label text.
- `npx playwright test tests/e2e/overview.spec.ts -g "no filter control offers an empty option"` → still passes (repo_id harness kind plan subset unchanged).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
