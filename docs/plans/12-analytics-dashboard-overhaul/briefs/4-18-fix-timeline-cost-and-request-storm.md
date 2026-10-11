# Brief: 4-18 — Show unpriced events as unpriced and stop the superseded-request storm

Consumer: a TypeScript worker (flash-tier). A second fixer after 4-16, from the re-verification of 4-17 on the real-ledger copy.
Owned paths: `packages/workflow-analytics/src/routes/conversation/+page.svelte`, `src/routes/+page.svelte`, `src/routes/usage/+page.svelte`, `src/lib/query.ts`, `src/lib/query.test.ts`, `src/lib/view.svelte.ts`, `tests/e2e/conversation.spec.ts`, `tests/e2e/overview.spec.ts`, `tests/e2e/usage.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-18-fix-timeline-cost-and-request-storm.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit. Do not use `/tmp`; use `.scratch/` inside the repo.
Depends on: 4-17.
Runs alongside: nothing.
Budget: 8 files to read, about 100 lines to write, 40 tool turns. Past the budget, stop and report `over budget`.

Run npm commands from `packages/workflow-analytics`. The Go API is read-only here.

## Required reading, in order

1. `DESIGN.md` — "Domain: Dashboard site", the data-layer bullet (aborts superseded requests; debounces ≤ 250 ms) and the `costLabel` rule.
2. `src/routes/conversation/+page.svelte` (`rowCost`) and `tools/workflow/internal/store/conversation.go` (how an event's `cost_usd` is set; Phase 3 chose `cost_usd: 0` for kept usage events whose model is unpriced).
3. `src/routes/+page.svelte` effects (lines 45 to 120), `src/routes/usage/+page.svelte` effects, `src/lib/view.svelte.ts` (`facets`, `paramsFor`), `src/lib/query.ts`.

## Goal

Per-event rows of an unpriced model read "unpriced", never `$0.00`; and a single preset change on Overview or Usage issues each distinct query once, not 12 to 17 requests of which 5 to 7 are superseded and aborted (the server keeps working on aborted requests, so they eat the API budget).

## Defects (measured on the compacted, purged real-ledger copy)

- **A. Timeline events show `$0.00`.** The conversation API returns `cost_usd: 0` (not null) for unpriced usage events, so `rowCost` prints `$0.00` on every such row, while the header total correctly says "unpriced". A priced model's event cost is greater than 0; a usage event (`tokens` present) with `cost_usd` of 0 or null is unpriced.
- **B. Request storm.** Overview 30d to 90d made 17 requests (12 distinct, 5 superseded); Usage 14 requests; Overview to Usage 12. Slowest call 700 to 800 ms under that load, so interactions took 1.03 to 1.39 s against a 1 s target. Suspected cause: effects re-run when `view.facets` or tz settles after the window changes, which supersedes queries already in flight. Find the real cause by logging requests in a test (`trackRequests`), then fix it so each distinct query is sent once per window change.

## Changes

1. A: in `rowCost`, an event with `tokens` and a `cost_usd` null or not greater than 0 returns `'unpriced'`; a positive cost goes through `costLabel` as now. Update `conversation.spec.ts` so the unpriced fixture events assert "unpriced" and none shows `$0`.
2. B: remove the cause of the superseded requests in the Overview and Usage effects (read signals that change after the window settles with `untrack`, or gate on a single settled flag), without losing the existing guard that waits for facets. If the cause is in `query.ts` or `view.svelte.ts`, fix it there. Set the client default `maxConcurrent` to 4 and update its test.
3. Add a regression spec on Overview and on Usage: switching the preset from 30d to 90d once issues each distinct normalised `/analytics/*` URL at most once (count requests through `trackRequests`; assert no URL repeats and the request total equals the page's distinct-query count).

## Done evidence

Failing specs first (report their output before and after).

- `npm test`, `npm run build`, `E2E_PORT=4418 npm run test:e2e` all pass.
- State the request counts before and after for Overview and Usage on a 30d to 90d change, measured in the fixture e2e.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. What changed, the check output before and after, every deviation and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently. Do not spawn agents beyond read-only research helpers.
