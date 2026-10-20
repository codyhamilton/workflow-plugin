# Brief: phase2-approval-page — User-code approval page

Consumer: a worker on `packages/yakka-analytics` (SvelteKit, Playwright, Vitest). Phase 2, the only unit.
Owned paths: `packages/yakka-analytics/src/routes/device/+page.svelte`, `packages/yakka-analytics/src/lib/api.ts`, `packages/yakka-analytics/src/lib/api.test.ts` (remove the loopback tests, add helper tests), `packages/yakka-analytics/tests/e2e/device.spec.ts` (replace). Touch nothing else.
Commits: one commit on `feat/device-login`; include the report in it.
Report: write `docs/plans/19-device-login/reports/phase2-approval-page.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: Phase 1 (closed, `2dc4811`). Read `docs/plans/19-device-login/reports/phase1-grant-flow.md` and `phase1-limits.md` for the server's real responses. The e2e test mocks the API, so no server runs.
Runs alongside: nothing.
Budget: read 6 files, about 250 lines changed, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/19-device-login/IMPLEMENTATION.md` and report `over budget`.

## Required reading, in order

1. `docs/plans/19-device-login/DESIGN.md`: Phase 2, "Domain: Device page (Pages)", and the `/v1/device/authorize` contract under "Domain: Device grant (server)".
2. `packages/yakka-analytics/src/routes/device/+page.svelte`: the page as it stands (loopback form).
3. `packages/yakka-analytics/src/lib/api.ts`: `apiPost`, `ApiError`, `createTenant`, `fetchMe`, `deviceAuthorizeAction`, `isValidLoopbackRedirectUri`, `oauthLoginPath`.
4. `packages/yakka-analytics/tests/e2e/device.spec.ts`: the two tests to be replaced; reuse their `page.route('**/v1/me', ...)` mock style.
5. `packages/yakka-analytics/src/lib/api.test.ts` lines using `isValidLoopbackRedirectUri`.

## Goal

The `/device` page approves or denies a user code with a credentialed `fetch`, never a navigating form, and no longer reads `state` or `redirect_uri`.

## Contract

Quote of the design's Device page contract, which wins over this brief on any conflict: `/device?user_code=X` prefills the code; `/device` alone shows an entry field. Signed out, it shows the existing GitHub sign-in link returning to the same URL. Signed in, it shows the code in large type with "Check this matches the code in your terminal", and the existing tenant, scope and expiry choices (create-tenant when the user has none). Approve and Deny call `/v1/device/authorize` with `fetch` and credentials, and the page shows "Approved — return to your terminal", "Denied", or the error. It no longer reads `state` or `redirect_uri` or posts a navigating form.

Server contract the calls rely on (Phase 1, done):
- `POST /v1/device/authorize` with JSON `{user_code, tenant, scope, expires_at}` approves → 200 `{"approved": true}`. `{user_code, action: "deny"}` denies → 200 `{"denied": true}`.
- 404 `{"error":"unknown_code"}` for a code that is unknown, expired or already decided. 403 for a tenant the user does not own. 400 for a bad scope or non-future `expires_at`. 429 after too many unknown-code attempts.

Choices left to you (state them in the report):
- Test ids: keep the existing `device-tenant`, `device-grant`, `device-expires`, `device-submit`, `device-oauth-login`, `device-tenant-name`, `device-tenant-submit`. Add `device-user-code` (the large-type code or the entry field), `device-deny`, `device-result` (the status text), `device-code-error`.
- The entry field's submit sets the `user_code` query parameter on the same route (`goto`, keep focus), so sign-in return URLs keep the code.
- Show the code upper-cased with the hyphen as typed. Do not validate its format client-side beyond non-empty; the server decides.
- `deviceAuthorizeAction` becomes a helper for the authorize URL used by `fetch`, renamed `deviceAuthorizeUrl` if cleaner. Same Pages-host / configured-base / same-origin logic. Delete `isValidLoopbackRedirectUri` and its tests.
- Map errors to short messages: 404 "That code is unknown or has expired. Run `yakka login` again.", 403 "You do not own that tenant.", 429 "Too many attempts. Wait and try again.", other: the `ApiError` message.
- After a decision, disable both buttons and keep the result visible; do not navigate.

## Changes

- Rewrite `+page.svelte` per the contract. Remove `deviceState`, `redirectUri`, `paramsOk`, the hidden fields, the `method="POST"` form action and the "missing state and redirect_uri" warning.
- Approve is disabled until a user code, tenant, scope and a future expiry are set. Approve sends one `fetch` (via a new `apiPost`-based helper in `api.ts`, `credentials: 'include'`) with the four fields. Deny sends `{user_code, action: "deny"}` and needs only the code.
- Signed out: the sign-in link's return URL (`oauthLoginPath(hostname, pathname + search)`) keeps `user_code`.
- Replace `tests/e2e/device.spec.ts`. Required tests:
  1. `/device?user_code=WDJB-MJHT` shows the code and the "Check this matches" text; Approve is disabled until tenant, scope and expiry are set, then enabled.
  2. Approve sends exactly one request to `/v1/device/authorize` with credentials and a JSON body of `user_code`, `tenant`, `scope`, `expires_at`; the page shows "Approved". No navigation away from `/device`.
  3. Deny sends `{user_code, action: "deny"}` and shows "Denied".
  4. A 404 from authorize shows the unknown-code error.
  5. `/device` with no parameter shows the entry field and no tenant form.
  6. Signed out (`/v1/me` → 401): `/device?user_code=X` shows the sign-in link whose `href` return parameter keeps `user_code=X`.
  7. A page loaded with `state` and `redirect_uri` in the URL does not use them (no request to a loopback URL; body has no `redirect_uri`).
  8. The page body never contains `wk_`.

### Keep untouched

Everything under `src/routes` other than `device`, the settings pages, token listing, the Go server, and `DESIGN.md`.

## Done evidence

- `cd packages/yakka-analytics && npx playwright test tests/e2e/device.spec.ts` passes, all eight tests named above.
- `npm test` (vitest) passes with the loopback helper tests removed.
- `npx svelte-check` (or the package's type check if different) passes for the files you touched.
- `grep -rn "redirect_uri\|isValidLoopback\|deviceAuthorizeAction" packages/yakka-analytics/src` finds no use of the loopback grant.

## Report back

`docs/plans/19-device-login/reports/phase2-approval-page.md`: what was done against the brief with test results; every departure and why; unfinished or deferred work; known problems; the choices above. Final message: commit hash, test results, departures, under 200 words. If the brief contradicts the code or the design, record it in the report; do not work around it silently.
