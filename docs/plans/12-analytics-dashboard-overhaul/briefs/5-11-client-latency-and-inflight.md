# Brief: 5-11 — Data client: lower debounce for discrete actions and fix the shared in-flight entry

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/lib/query.ts`, `packages/workflow-analytics/src/lib/query.test.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-11-client-latency-and-inflight.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-01, 5-02, 5-03, 5-04, 5-12, 5-14, 5-15, 5-16. The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 4 files to read, about 120 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Data layer" ("debounces filter changes (≤ 250 ms), aborts superseded requests, and caches responses") and the Phase 4 outcome "A burst of filter changes issues only the last request".
2. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — "Phase 4 verification" (latency table) and "Carried (Phase 4)" items 1 and 8.
3. `src/lib/query.ts` — all of it (180 lines); `src/lib/query.test.ts` — the burst, supersede and cache tests.
4. `src/lib/view.svelte.ts` — read only, to see how facets and routes call `getJSON`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Part of the 1.1 to 1.4 s settle time on the large ledger (a 250 ms debounce in front of a 0.45 to 0.62 s API call) is the client's wait: cut it for discrete actions, and fix the shared in-flight entry bug, with no extra requests in a burst.

## Contract

Measured (Phase 4 verification, large copy): Overview 30d to 90d 1.16 s, Usage 30d to 90d 1.20 s, Overview to Usage 1.21 s, All time 1.31 to 1.36 s, filter add about 1.0 s; target 1 s from input to settled chart. DESIGN.md allows "≤ 250 ms", so a lower value is within the contract.

Settled decision: the debounce is a trailing 100 ms window by default (down from 250), and a call whose slot has been idle for at least 250 ms (the previous call on that slot settled or was never made) fires on the leading edge with no wait. A burst (a call arriving while the slot has an unsettled call or within 250 ms of the previous one) debounces 100 ms trailing and supersedes as today. Preset clicks and navigations after a pause therefore wait 0 ms; typing or rapid clicking still issues only the last request.

## Changes

1. `createClient` options: `debounceMs` default 100, new `idleMs` default 250 (leading edge when a slot was idle longer), both still injectable for tests. A cache hit stays synchronous.
2. Bug (Carried 8, "`query.ts` can drop a shared in-flight entry for same-key joiners"): reproduce it first in a test with two slots that share one key. Look at `release` and the `perform` `finally`: when slot A's superseded call releases a shared fetch while slot B has joined it, or when a fetch is aborted by `release` and a later joiner arrives before the abort is observed, `inflight` can lose or keep a dead entry and the joiner receives `Superseded` or a hung promise. Fix so a joiner always either shares a live fetch or starts a new one, and add the regression test.
3. Tests: leading edge fires without waiting after idle; a burst of five calls on one slot issues one fetch; the 100 ms window; the shared-entry regression; existing tests updated, never weakened (recount, do not edit expected numbers to fit).
4. Do not add prefetching, optimistic rendering or any new request.

### Keep untouched

The exported API (`createClient`, `client`, `getJSON`, `normalise`, `Superseded`), the concurrency limit of 4, session cache, abort of superseded calls and notice setting.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- query` → the new tests fail before and pass after (shared-entry regression and leading edge), existing tests pass.
- `npm run build` → passes; `npm run test:e2e -- overview.spec.ts usage.spec.ts` → pass (the request-count assertions there are the burst guard).
- Record the measured p50 of a preset click to settled chart on the fixture before and after (a short Playwright snippet or the existing `expectSettled` timing); the large-ledger figure is re-measured by the orchestrator, not by you.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
