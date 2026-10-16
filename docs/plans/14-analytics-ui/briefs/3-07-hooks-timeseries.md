# Brief: 3-07 — Hooks time series and brush

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/hooks/+page.svelte`; `packages/workflow-analytics/tests/e2e/hooks.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/3-07-hooks-timeseries.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-03-time-chart-interactions.
Runs alongside: 3-04-trends-stacked-drill, 3-05-usage-distribution.
Budget: 8 files to read, about 150 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 3 `/hooks` outcome; Domain: Report interaction (brush, drill, zero-fill on count series).
2. `packages/workflow-analytics/src/routes/hooks/+page.svelte`.
3. `packages/workflow-analytics/src/routes/trends/+page.svelte` — bucket pick and All-time clamp pattern.
4. `packages/workflow-analytics/tests/e2e/hooks.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Hooks adds an interactive hook-event time series split by `norm_event` or `tool`, with brush window selection, while keeping treemap drill and the existing bar panels.

## Contract

Phase 3 outcome:

- On `/hooks`, the time series is `GET /v1/analytics/query` with `measure=hook_events`, a time bucket, and one dimension of `norm_event` or `tool`. Brush sets the window. A treemap leaf still drills.

Domain: Report interaction — brush sets custom range; clicking filter keys drills; `__other__` inert.

## Changes

- Add controls: time bucket (reuse `pickBucket` / offered buckets like trends) and dimension toggle `norm_event` | `tool`.
- Fetch `/analytics/query` with `measure=hook_events`, selected `dim`, `top` appropriate for series (8 or 20 — match trends top-N behavior), and time bucket; zero-fill gaps in the client for count series (reuse trends `buildSeries` logic or a shared helper copied minimally into this page to avoid owning `trends/+page.svelte`).
- Render `TimeChart` with `onbrush` → `view.setWindow`; optional series drill when the split dimension is a filter key (`norm_event`, `tool`).
- Keep existing bar charts and treemaps; treemap `drillPath` unchanged.
- Gate loads on facets like today.

### Keep untouched

Treemap/Bar chart components and other routes.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/hooks.spec.ts` from `packages/workflow-analytics` → passes, including new tests: time series visible with `data-testid` e.g. `hooks-over-time`; request URL includes `measure=hook_events`, a time `bucket`, and `dim=norm_event` or `dim=tool`; brush narrows URL `from`/`to`; treemap drill test still passes.
- `npx playwright test tests/e2e/hooks.spec.ts -g "fixture counts"` → still passes for static bars.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
