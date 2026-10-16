# Brief: 1-03 — Analytics site session mode

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 1.
Owned paths: `packages/workflow-analytics/src/lib/api.ts`, `packages/workflow-analytics/src/lib/api.test.ts`, `packages/workflow-analytics/src/routes/+layout.svelte`, `packages/workflow-analytics/src/routes/login/+page.svelte` (new), `packages/workflow-analytics/src/routes/+page.svelte` (only changes needed to pass `tenant` from `/v1/me`), `packages/workflow-analytics/tests/e2e/` (new or updated specs for login and session GETs only), `docs/plans/13-client-registration/reports/1-03-analytics-session-site.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/1-03-analytics-session-site.md` and include it in the commit.
Depends on: 1-02.
Runs alongside: nothing.
Budget: 10 files to read, about 350 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Client presentation (collector-origin bullet), Domain: Request authorization (`GET /v1/me`, session GETs), Phase 1 outcome (site: no stored bearer; 403 vs 401).
2. `docs/plans/13-client-registration/reports/1-02-oauth-session-remote-auth.md` — actual route shapes and error bodies.
3. `packages/workflow-analytics/src/lib/api.ts` and `api.test.ts`.
4. `packages/workflow-analytics/src/routes/+layout.svelte` and `+page.svelte`.
5. `packages/workflow-analytics/tests/e2e/helpers.ts` — patterns for API mocking.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

When the site is served from the collector origin (empty `workflow-analytics-base`), use the session cookie for data reads: no `Authorization` header, no `workflow-analytics-key`. Add `/login` for denied sign-in. Distinguish 403 `no such tenant` from 401 so the dashboard does not show the settings token prompt for the former.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

- Request authorization: "On the collector origin the embedded site sends no `Authorization` header. It does not attach `workflow-analytics-key`. Its data GETs carry `?tenant=` taken from `GET /v1/me`."
- Request authorization: "`GET /v1/me` with a session returns `{\"github_id\",\"github_login\",\"admin\",\"tenants\":[{\"name\"}]}`. … Without a session it is 401."
- Request authorization: "A missing `tenant`, or one the session does not own, is 403 `{\"error\":\"no such tenant\"}`."
- Identity and admission: denied admission → `/login?error=denied`.
- Phase 1 outcome: "the site does not treat that as a logged-out 401"; "The collector-origin site sends no stored bearer."

Decisions for this unit:

- **Collector vs Pages**: If `localStorage` `workflow-analytics-base` is non-empty, keep today's behavior (optional bearer from `workflow-analytics-key`). If base is empty (same-origin embedded), use `credentials: 'include'` on fetches, never send `Authorization`, resolve tenant from `GET /v1/me` once per navigation (or when tenant list changes).
- **`/login` page**: show sign-in link to `/oauth/login` (same origin) and surface `error=denied` from the query string.
- **Layout error panel**: 401 → prompt to sign in at `/login` (not `/settings` token help) when in collector mode; 403 with `no such tenant` → explain no tenant yet (phase 2 creates them; empty list is valid in phase 1).
- **`/settings`**: unchanged pasted-token path for cross-origin Pages.

## Changes

- Extend `apiGet` (or add `apiGetSession`) for collector mode: relative `/v1/…`, `credentials: 'include'`, no bearer header.
- Add `fetchMe()` returning the `/v1/me` shape; wire overview (and shared data loaders if any) to append `tenant` query param from the first owned tenant when present.
- Add `/login` route.
- Update `+layout.svelte` error copy per collector vs Pages mode.
- Vitest coverage for collector-mode fetch (no Authorization header, credentials include).
- Optional Playwright spec: mocked `/v1/me` + summary with `?tenant=` (follow existing e2e patterns).

### Keep untouched

- `/settings` token UX for non-empty base URL.
- Chart components and filter state machinery except where overview must pass `tenant`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/workflow-analytics && npm test` → pass (including new api tests for collector mode).
- `cd packages/workflow-analytics && npm run test:e2e -- --grep 'session|login'` → pass if specs added; if Playwright skipped for env, report `done with concerns` and cite vitest coverage only.
- Observable: with empty base in vitest, `apiGet('analytics/summary')` call uses `credentials: 'include'` and no `authorization` header.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
