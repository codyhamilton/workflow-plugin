# Brief: 1-02 — OAuth, session, and remote request auth

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 1.
Owned paths: `tools/workflow/internal/serve/oauth.go`, `tools/workflow/internal/serve/session.go`, `tools/workflow/internal/serve/serve.go` (everything not owned by 1-01: `Handler`, `auth`, `tenantFor`, route handlers), `tools/workflow/internal/serve/serve_test.go` (OAuth, session, and remote auth tests), `docs/plans/13-client-registration/reports/1-02-oauth-session-remote-auth.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/1-02-oauth-session-remote-auth.md` and include it in the commit.
Depends on: 1-01.
Runs alongside: nothing.
Budget: 12 files to read, about 900 lines to change including tests, 70 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Identity and admission (full contract), Domain: Request authorization (full contract), Phase 1 outcome (full paragraph).
2. `docs/plans/13-client-registration/reports/1-01-registry-remote-config.md` — departures from its brief.
3. `tools/workflow/internal/serve/registry.go` — API from 1-01.
4. `tools/workflow/internal/serve/serve.go` — `Handler`, `auth`, `tenantFor`, `cors`, `localGuard`.
5. `tools/workflow/internal/serve/serve_test.go` — `do`, `newServer`, local mode HTTP tests.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

On a remote collector, implement GitHub login and admission, session cookies, admin domain policy, and remote `/v1` authorization (bearer vs session) so the phase 1 outcome holds for HTTP. Loopback behavior stays local mode with tenant `local` and no session requirement.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Identity and admission**

- "Authorize URL requests scopes `read:user` and `user:email`. `GET /oauth/login` redirects to GitHub with a `state` value the callback checks. `GET /oauth/callback` exchanges the code. A missing or mismatched `state`, or a failed exchange, sets no session."
- "The identity stored for the session is the GitHub user id (the stable owner id), the GitHub login, and the verified email addresses GitHub returned for that login. An unverified address does not count. The admin is the session whose verified addresses include `codyh@ctzns.net`."
- "Domain policy is one collector-wide record: `everyone`, or `allow_list` plus a set of domains. Default when no record exists: `everyone`. A domain is the host part of an email, compared case-insensitively, exact (`ctzns.net` does not admit `a.ctzns.net`)."
- "A login gets a session only if policy is `everyone`, or any verified email's domain is on the allow list, or the login is the admin. Otherwise the callback sets no cookie and redirects to `/login?error=denied`. Login does not create a tenant."
- "The admin is admitted even when the allow list does not contain `ctzns.net`, so a bad list cannot remove the only person who can edit it."
- "Session cookie: name `workflow_session`, HttpOnly, SameSite=Lax, Secure when `WORKFLOW_PUBLIC_URL` is https. It expires 14 days after login and is not slid forward by activity. Each authenticated request re-reads policy against the emails stored for that session; a session that would now be denied is cleared and treated as logged out. Logout (`POST /logout`) clears the cookie and does not revoke tokens."
- "`PUT /v1/admin/policy` with a session that is not the admin is 403. Body: `{\"mode\":\"everyone\"|\"allow_list\",\"domains\":[\"example.com\"]}`. `domains` is the list when mode is `allow_list`, and is stored empty when mode is `everyone`."
- "Mutating session routes require `Content-Type: application/json` and an `Origin` equal to `WORKFLOW_PUBLIC_URL` (local mode: a loopback origin). Anything else is 403 and changes nothing. The device-code exchange is not a session route and is not subject to that `Origin` rule."
- "A dashboard login redirects to `/`, the analytics dashboard. A login started by `workflow login` returns to the device page. The OAuth callback itself does not create a tenant. Static files stay unauthenticated. Ledger data does not."

**Request authorization (phase 1 subset)**

- "If the request has `Authorization: Bearer <token>`, the registry decides." (Phase 2 implements token lookup; in phase 1 no issued tokens exist — unknown bearer is 401.)
- "With no bearer, a session may call those GETs for a `tenant` query it owns, and may not call `POST /v1/ingest` (ingest is bearer-only). A missing `tenant`, or one the session does not own, is 403 `{\"error\":\"no such tenant\"}`."
- "No bearer and no session on a remote data route is 401 `{\"error\":\"unauthorized: this service requires a token; sign in at <WORKFLOW_PUBLIC_URL>/login\"}`."
- "`GET /v1/health` stays unauthenticated. Profile and admin routes reject a bearer with 401; they accept only a session, as the identity contract says."
- "`GET /v1/me` with a session returns `{\"github_id\",\"github_login\",\"admin\",\"tenants\":[{\"name\"}]}`. `github_login` is the login stored on the session. Without a session it is 401."

**Phase 1 outcome (HTTP portions this unit must satisfy)**

- Remote bind + OAuth env starts; `WORKFLOW_SERVE_KEYS` or missing OAuth env refuses before listen (from 1-01).
- Dashboard login as verified `codyh@ctzns.net` sets `workflow_session` and lands on `/`; admin admitted when allow list omits `ctzns.net`; denied user gets `/login?error=denied` and no cookie.
- `GET /v1/analytics/summary` with no session on remote → 401, not tenant `local`.
- `POST /v1/ingest` with no bearer stores nothing; with session and no bearer stores nothing.
- Session summary with no owned tenant → 403 `no such tenant`.
- Admin `PUT /v1/admin/policy`; non-admin 403; policy change clears denied sessions on next request.
- Loopback: `/` and `GET /v1/analytics/summary` for tenant `local` with no cookie/bearer even when OAuth env is set.

Decisions for this unit:

- **GitHub in tests**: inject a test base URL for authorize/token/user/emails HTTP (env var or `Options` field) so unit tests never call github.com.
- **OAuth `state`**: store in an HttpOnly short-lived cookie or server-side map; callback must validate.
- **`POST /logout`**: session route; same Origin rule as other mutating session routes.
- **Bearer on remote without registry token** (phase 1): always 401 `{\"error\":\"unauthorized\"}` via existing keyed path only in tests that still pass `Config.Keys`; remote `ConfigFromEnv` servers have empty keys.

## Changes

- Register routes: `GET /oauth/login`, `GET /oauth/callback`, `POST /logout`, `GET /v1/me`, `PUT /v1/admin/policy`.
- Implement GitHub code exchange and email verification filter.
- Session middleware: load session from cookie, re-check policy, attach to request context, clear cookie when denied.
- Rewrite `auth` / `tenantFor` for `cfg.Remote()`: bearer path unchanged when keys present in tests; remote production uses session for GETs with `?tenant=`; ingest requires bearer; profile routes session-only.
- Update 401 message to use `WORKFLOW_PUBLIC_URL/login` on remote.
- `Handler`: apply `localGuard` only when `cfg.Local()`.
- Add `originGuard` for mutating session routes per contract.

### Keep untouched

- `packages/workflow-analytics` (unit 1-03).
- `tools/workflow/internal/serve/site.go` unless a one-line hook is unavoidable for logout POST (prefer routing in `serve.go`).
- Token issuance, `POST /v1/tenants`, device OAuth (later phases).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && go test ./internal/serve/ -run 'OAuth|Session|RemoteAuth|Policy' -count=1` → pass (new tests covering admission, admin bypass, denied login, remote 401/403, ingest without bearer, loopback unchanged).
- `cd tools/workflow && go test ./internal/serve/ -count=1` → pass full package.
- Observable: in a remote `httptest` server, successful mock GitHub login sets `Set-Cookie: workflow_session=…` and `GET /v1/me` returns `admin:true` for `codyh@ctzns.net`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
