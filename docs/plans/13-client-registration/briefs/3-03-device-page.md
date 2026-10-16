# Brief: 3-03 — Device page

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 3.
Owned paths: `packages/workflow-analytics/src/routes/device/+page.svelte` (new), `packages/workflow-analytics/src/lib/api.ts` (device helpers only), `packages/workflow-analytics/src/lib/api.test.ts` (device API tests), `packages/workflow-analytics/tests/e2e/device.spec.ts` (new, if you add Playwright coverage), `docs/plans/13-client-registration/reports/3-03-device-page.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/3-03-device-page.md` and include it in the commit.
Depends on: 3-02.
Runs alongside: 3-04 (after 3-02 lands).
Budget: 10 files to read, about 450 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Client presentation (device page questions, no silent defaults, no plaintext in page response).
2. `docs/plans/13-client-registration/reports/3-02-device-auth-server.md` — actual device create redirect and query params (read after 3-02 lands).
3. `packages/workflow-analytics/src/routes/profile/+page.svelte` — tenant create and token form patterns (contrast expiry prefill).
4. `packages/workflow-analytics/src/lib/api.ts` — `createTenant`, `createToken`, collector session fetches.
5. `packages/workflow-analytics/src/routes/login/+page.svelte` — OAuth link pattern.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Ship the collector device page at a stable path (e.g. `/device`) that `workflow login` opens: after session (via GitHub if needed), the user must choose tenant, grant, and expiry; the page never invents defaults; submit uses the 3-02 device create flow and does not display the issued plaintext.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Client presentation**

- "The device page lists tenants this user owns and asks which tenant, which grant (`read` or `read_write`), and the lifetime (`expires_at`, RFC3339 UTC, strictly in the future). The collector does not fill those in. There is no server-side lifetime default."
- "The page does not silently choose among several tenants, and it does not silently choose the grant. It does not name a tenant from the GitHub login. If the user owns none, they type a name and the page creates it through `POST /v1/tenants`."
- "Abandoning the page writes no token and leaves `client.toml` unchanged." (CLI side unchanged here; page must not auto-submit.)
- "The device page's create response to the browser does not contain the plaintext."
- "A login started by `workflow login` returns to the device page." (Preserve `return` / query params the CLI sets; link unauthenticated users through `/oauth/login?return=…` consistent with existing cookie.)

**Phase 3 outcome (this unit)**

- "That page issues no token until the user has chosen a tenant, a grant (`read` or `read_write`), and an expiry, and it does not invent a lifetime."
- "If the user has no tenant, they type a name and the page creates it."

## Changes

- Parse `state` and loopback `redirect_uri` (names per 3-02 report) from the query string; refuse submit when missing or invalid.
- Tenant picker: empty list → show create-tenant field; multiple tenants → require explicit selection (no pre-selected sole tenant unless the user confirms — prefer empty default forcing choice when count > 1).
- Grant: require explicit `read` or `read_write` selection (no default checked).
- Expiry: empty initial value — **Carried item 4**: do not copy profile's three-month prefill (`defaultExpiry` in profile); user must enter a future RFC3339 time.
- Submit calls the device create API from 3-02 (session cookie + JSON + `Origin`); follow redirect to loopback with code (browser navigation).
- **Carried item 1 (tenant on other routes)**: do not add `tenant` query to analytics routes beyond `/` and `/profile`; note in report if still true.
- **Carried item 3 (e2e seeds registry)**: do not rewrite `global-setup.ts` OAuth login; optional `device.spec.ts` may mock APIs like `session.spec.ts`.

### Keep untouched

- `/profile` token create UX except you may read it for contrast; do not change profile expiry prefill in this unit unless required for shared helper extraction (prefer duplicate minimal form code over scope creep).
- `workflow login` CLI (3-04).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/workflow-analytics && npm test` → pass, including new api tests for device helpers.
- Observable in devtools or Playwright: device page expiry field starts empty; submit disabled or rejected until tenant, scope, and expiry set; successful submit navigates away without rendering `wk_` in the DOM.
- If Playwright added: `npx playwright test tests/e2e/device.spec.ts` → pass (or document skip reason in report).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
