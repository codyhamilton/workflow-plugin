# Brief: 2-03 — Profile UI, collector overview, and e2e setup

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 2.
Owned paths: `packages/workflow-analytics/src/lib/api.ts`, `packages/workflow-analytics/src/lib/api.test.ts`, `packages/workflow-analytics/src/routes/profile/+page.svelte` (new), `packages/workflow-analytics/src/routes/+layout.svelte` (nav link to profile only), `packages/workflow-analytics/src/routes/+page.svelte` (only if needed to satisfy phase 2 one-tenant overview outcome), `packages/workflow-analytics/tests/e2e/global-setup.ts`, `packages/workflow-analytics/tests/e2e/helpers.ts`, `packages/workflow-analytics/tests/e2e/settings.spec.ts` (replace keyed `WORKFLOW_SERVE_KEYS` server usage), `packages/workflow-analytics/tests/e2e/` (profile or session specs as needed), `docs/plans/13-client-registration/reports/2-03-analytics-profile-e2e.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/2-03-analytics-profile-e2e.md` and include it in the commit.
Depends on: 2-01.
Runs alongside: 2-02, 2-04.
Budget: 12 files to read, about 450 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Tenancy and tokens (profile create/list/revoke), Domain: Request authorization (collector site, session GETs), Phase 2 outcome (profile, `/`, no bearer).
2. `docs/plans/13-client-registration/IMPLEMENTATION.md` — Phase 1 **Carried** items 1 and 2 (read only; do not edit IMPLEMENTATION.md).
3. `docs/plans/13-client-registration/reports/1-03-analytics-session-site.md` — collector mode behavior.
4. `packages/workflow-analytics/src/lib/api.ts` and `api.test.ts`.
5. `packages/workflow-analytics/tests/e2e/global-setup.ts` and `settings.spec.ts`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Add a collector `/profile` where a logged-in user creates tenants and tokens (showing plaintext only on create), list and revoke tokens, and keep the overview on `/` using session + `tenant` from `GET /v1/me` with no stored bearer. Fix e2e global setup so Playwright can run without `WORKFLOW_SERVE_KEYS`.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

- "`POST /v1/tokens` … On this profile route it appears only in this response."
- "`GET /v1/tokens` … never `token`."
- "`POST /v1/tokens/<id>/revoke` …"
- "On the collector origin the embedded site sends no `Authorization` header. It does not attach `workflow-analytics-key`. Its data GETs carry `?tenant=` taken from `GET /v1/me`."
- "Pages `/settings` still stores a pasted bearer, sends that bearer, and does not send the session cookie."

**Phase 2 outcome (this unit)**

- Logged-in user creates tenant and token via profile; lists without plaintext; revoke from profile.
- "After login, with one owned tenant, `/` shows that tenant's summary from a cookie-only request whose `tenant` comes from `GET /v1/me`, and the site does not send a stored bearer."

Decisions for this unit:

- **API helpers**: `apiPost` / `apiDelete` or dedicated functions mirroring `apiGet` collector mode (`credentials: 'include'`, no bearer on collector origin; JSON body + session Origin behavior is browser-default same-origin).
- **Profile UX**: form for tenant name (`POST /v1/tenants`), form for token (`tenant` select among owned, `scope`, `expires_at` required — no server default); on successful create, show plaintext once with copy affordance; list table with revoke action; admin sees link or section to `GET /v1/admin/tokens` when `me.admin`.
- **Nav**: add Profile link in header nav (collector and Pages both may show it; on Pages without session it will 401 — acceptable or hide when not collector).
- **Carried item 1 (e2e)**: remove `WORKFLOW_SERVE_KEYS` from `global-setup.ts`. For cross-origin bearer tests in `settings.spec.ts`, start a second **remote-mode** test server (OAuth env + mock GitHub pattern from `serve_test.go`, or a small shell helper) and seed a `read` or `read_write` token via session APIs; write `keyed` base URL and issued token into `state.json` instead of env keys. Run `npm test` and `npx playwright test tests/e2e/session.spec.ts` (and updated settings spec) as done evidence.
- **Carried item 2 (tenant on other routes)**: do **not** add `tenant` to every analytics route in this unit; only `/` and `/profile` are in scope. Note remaining gap in the report for phase 3 if still true.

## Changes

- Implement profile page and API wrappers for tenant/token CRUD.
- Update layout nav.
- Rework e2e global setup and settings spec for issued bearer tokens.
- Vitest for new API helpers (mock `fetch`).

### Keep untouched

- `tools/workflow/internal/serve` (2-01).
- Routes other than `/`, `/login`, `/settings`, `/profile` for tenant query wiring (carried item 2).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/workflow-analytics && npm test` → pass.
- `cd packages/workflow-analytics && npx playwright test tests/e2e/session.spec.ts tests/e2e/settings.spec.ts --grep-invert @slow` → pass (or document `@slow` skip if none).
- Observable: in collector mode Vitest, `apiGet` for analytics paths sends no `Authorization` header and includes `credentials: 'include'`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
