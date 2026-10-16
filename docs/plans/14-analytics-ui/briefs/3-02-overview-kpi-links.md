# Brief: 3-02 — Overview KPI links

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/+page.svelte`; `packages/workflow-analytics/tests/e2e/overview.spec.ts` (add KPI link tests only; do not rewrite unrelated tests). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/3-02-overview-kpi-links.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-01-filter-bar-ten-dims, 3-03-time-chart-interactions, 3-06-repos-cost-rank, 3-08-builder-scalar-heatmap.
Budget: 6 files to read, about 100 lines to change, 20 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Domain: Report interaction (overview KPI links), Decisions (heatmap cells do not filter).
2. `packages/workflow-analytics/src/routes/+page.svelte` — tile layout and sparklines.
3. `packages/workflow-analytics/src/routes/+layout.svelte` — `navHref` preserves query string (match that pattern).
4. `packages/workflow-analytics/tests/e2e/overview.spec.ts` — fixture expectations.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Overview KPI tiles link to the report that owns each measure, keeping the current filter and window query string, and trends targets receive the correct metric parameter.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Domain: Report interaction:

- Each overview KPI links to the report that owns the measure, keeping the current query string. The link sets `measure` only when the target is `/trends`: `artifact_versions`, `distinct_content`, or `commits`, one per tile. Conversations → `/conversations`. Hook events → `/hooks`. Model calls, tokens, cost, and unpriced calls → `/usage`.

Decision: Heatmap cells do not filter. Do not add drill to the overview weekday×hour heatmap in this unit.

## Changes

- Wrap each primary KPI tile (the nine sparkline tiles in `SPARKS`, not the grouped summary sections) in a link that preserves `page.url.search` (same approach as layout nav).
- Map targets: `conversations` → `/conversations`; `hook_events` → `/hooks`; `model_calls`, `tokens_in`/`tokens` tile, `cost_usd`, `unpriced_calls` → `/usage`; `artifact_versions`, `distinct_content`, `commits` → `/trends`.
- The trends route reads the query param `metric` today (`trends/+page.svelte`). Set `metric=` to the three trend-owned measures above; do not rename the param in this phase.
- When linking to `/trends`, set only that tile’s `metric` and keep other filter/window params; clear a stale `metric` when navigating to non-trends routes is not required if the URL already carries unrelated params.
- Style links so solarized tokens and spacing stay consistent (no new hex in route `<style>`).

### Keep untouched

Heatmap, sparkline data loading, grouped summary sections, and filter bar behavior.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/overview.spec.ts -g "KPI"` from `packages/workflow-analytics` → passes; new tests cover: with `?repo_id=` on `/`, clicking the conversations tile lands on `/conversations` with the same `repo_id`; clicking artifact versions lands on `/trends` with `metric=artifact_versions` and the same filter params; hook events → `/hooks`; cost → `/usage`.
- `npx playwright test tests/e2e/overview.spec.ts -g "overview shows the fixture numbers"` → still passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
