# Brief: 4-02 — Session 403 on the landing reads

Consumer: the phase 4 fixer.
Owned paths: `packages/yakka-analytics/tests/e2e/session.spec.ts` (only the two tests named below). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to `origin` branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/4-02-session-403.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit. Test results, not a file list, model, or cost.
Depends on: `4-01-landing-trend` (commit `c4d8a94` is on this branch).
Runs alongside: nothing.
Budget: 4 files to read, about 40 lines to change, 15 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `packages/yakka-analytics/tests/e2e/session.spec.ts` — `no tenant: summary 403 no such tenant sends to /profile` and `tenant present: summary 403 no such tenant does not send to /profile`.
2. `packages/yakka-analytics/src/routes/+page.svelte` — the `aggregate` calls only. `/` does not request `analytics/summary`. The first read is `analytics/facets`, then `analytics/query`. A rejection calls `setError`.
3. `packages/yakka-analytics/src/lib/session-gate.ts` — `shouldNavigateToProfile`. A 403 whose message is `no such tenant` goes to `/profile` only when `me` returned no tenant.

Read ranges and grep; do not read a whole file to find one section.

## Goal

The phase 1 profile send still happens when the landing's analytics read is 403 `no such tenant` and `me` has no tenant, and it still does not happen when `me` has a tenant.

## Contract

Cited from `DESIGN.md`, Domain: Session gate. Settled.

> A 403 `no such tenant` goes to `/profile` only when `me` returned no tenant.

`src/lib/api.ts` `parseJsonResponse` turns `{ "error": "no such tenant" }` on a non-OK response into `ApiError` with that message. `setError` copies `ApiError.status` and `ApiError.message` onto `fetchError`. The layout effect calls `shouldNavigateToProfile` with those fields.

## Changes

In the two tests only, stop fulfilling `**/v1/analytics/summary*`. Fulfill `**/v1/analytics/**` with status 403 and JSON `{ error: 'no such tenant' }`. Leave the `GET /v1/me` bodies as they are.

`no tenant`: after `goto('/')`, the URL matches `/profile`.

`tenant present`: track requests whose URL contains `/v1/analytics/`. After `goto('/')`, wait until that count is greater than 0, then the URL is still `/` and does not match `/profile`. Do not assert before the analytics request has been seen. A 404 on an unmocked read is not this test.

Do not edit `+page.svelte`, the session gate, `helpers.ts`, or any other test.

## Done evidence

Identify the failing check before changing the mock. Report its output before and after.

- `cd packages/yakka-analytics && npx playwright test tests/e2e/session.spec.ts -g "no such tenant"` → the no-tenant test fails first (stays on `/`), then both pass.
- `cd packages/yakka-analytics && npx playwright test tests/e2e/session.spec.ts` → the file passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
