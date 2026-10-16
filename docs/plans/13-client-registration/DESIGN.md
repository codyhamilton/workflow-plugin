# Client registration

## Intent

User request, verbatim:

> Important next step for this workflow service is to be able to run it as a collector on fly.io, so that both cloud and local agents can post events. Key item we are missing is client registration, which will be via keys we issue from the service. I'm wondering if we can do it like this - we register this as a github oauth app. We have a login page on the service, which logs the user in with github. On the user profile page we let them create api tokens, which then can be configured in various places - user device, claude / codex remote agent env etc for submitting events and getting data. feasible? /design

## Problem

`workflow serve` can store a tenant's facts and answer reads, but the only remote credential is `WORKFLOW_SERVE_KEYS`: a process-start env string of `tenant=key` pairs, one key to one tenant, with no issuer, no expiry, and no way to add a key without restarting. The client file that would hold a key (`~/.config/workflow/client.toml`) is documented as written by `workflow login`, and that command does not exist. The analytics site asks a person to paste the same long-lived tenant key into `localStorage`. Nothing in the tree is a GitHub login, a profile, or a fly.io collector. Cloud and local agents cannot be handed a credential the service itself issued.

## Solution Shape

A remote `workflow serve` is a collector. A person logs in with GitHub; the session opens the analytics dashboard and the profile. The profile creates tenants and issues tokens. A token belongs to one tenant, is `read` or `read_write`, and has an expiry the issuer set. `workflow login` is a second way onto that same login: it opens the collector in the browser, the device page asks which tenant and which grant and sets the lifetime, and the command writes the issued token into `client.toml`. Agents and devices send it as `Authorization: Bearer`. The session is not a bearer token, and a bearer token is not a session. Local loopback serve stays keyless. On the collector, `WORKFLOW_SERVE_KEYS` is not a credential. The collector runs as one fly.io machine with a persistent data directory.

### Domain: Identity and admission

- Owns: the GitHub OAuth app's login flow, the session, who counts as admin, and the collector-wide domain policy.
- Contract:
  - The collector is registered as one GitHub OAuth app. The process reads `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET`, and `WORKFLOW_PUBLIC_URL` (https origin, no path). Those three are required when the bind is not loopback, and they are never written into `client.toml` or a tenant ledger. A loopback bind is always local mode, including when all three are set: they are ignored, and the process still serves tenant `local` with no keys.
  - Authorize URL requests scopes `read:user` and `user:email`. `GET /oauth/login` redirects to GitHub with a `state` value the callback checks. `GET /oauth/callback` exchanges the code. A missing or mismatched `state`, or a failed exchange, sets no session.
  - The identity stored for the session is the GitHub user id (the stable owner id), the GitHub login, and the verified email addresses GitHub returned for that login. An unverified address does not count. The admin is the session whose verified addresses include `codyh@ctzns.net`.
  - Domain policy is one collector-wide record: `everyone`, or `allow_list` plus a set of domains. Default when no record exists: `everyone`. A domain is the host part of an email, compared case-insensitively, exact (`ctzns.net` does not admit `a.ctzns.net`).
  - A login gets a session only if policy is `everyone`, or any verified email's domain is on the allow list, or the login is the admin. Otherwise the callback sets no cookie and redirects to `/login?error=denied`. Login does not create a tenant.
  - The admin is admitted even when the allow list does not contain `ctzns.net`, so a bad list cannot remove the only person who can edit it.
  - Session cookie: name `workflow_session`, HttpOnly, SameSite=Lax, Secure when `WORKFLOW_PUBLIC_URL` is https. It expires 14 days after login and is not slid forward by activity. Each authenticated request re-reads policy against the emails stored for that session; a session that would now be denied is cleared and treated as logged out. Logout (`POST /logout`) clears the cookie and does not revoke tokens.
  - `PUT /v1/admin/policy` with a session that is not the admin is 403. Body: `{"mode":"everyone"|"allow_list","domains":["example.com"]}`. `domains` is the list when mode is `allow_list`, and is stored empty when mode is `everyone`.
  - Mutating session routes require `Content-Type: application/json` and an `Origin` equal to `WORKFLOW_PUBLIC_URL` (local mode: a loopback origin). Anything else is 403 and changes nothing. The device-code exchange is not a session route and is not subject to that `Origin` rule.
  - A dashboard login redirects to `/`, the analytics dashboard. A login started by `workflow login` returns to the device page. The OAuth callback itself does not create a tenant. Static files stay unauthenticated. Ledger data does not.
- Non-goals: more than one OAuth app; org or team SSO; letting a non-admin edit the policy; a GitHub device-code grant that never opens the collector.

### Domain: Tenancy and tokens

- Owns: which GitHub user owns which tenant, and the issued tokens. Does not own the fact ledger inside a tenant.
- Contract:
  - A tenant name matches the name rule serve already uses (`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`). Names are unique on the collector. The creating user owns it. There is no transfer and no delete.
  - `POST /v1/tenants` with `{"name":"<name>"}` and a session creates that tenant and returns 201 `{"name":"<name>"}`. A taken name is 409. A bearer token calling this route is 401.
  - A token belongs to exactly one tenant. Scope is `read` or `read_write`, chosen at creation, not changed later. `expires_at` is required, RFC3339 UTC, and must be strictly in the future. There is no token without an expiry and no sliding expiry.
  - `POST /v1/tokens` with `{"tenant","scope","expires_at"}` and a session that owns the tenant returns 201 `{"id","token","tenant","scope","expires_at"}`. `token` is the plaintext (`wk_` plus an unguessable body). On this profile route it appears only in this response. There is no server-side lifetime default: a missing or non-future `expires_at` creates no token. A tenant the caller does not own is 403.
  - `GET /v1/tokens` with a session returns that owner's tokens as `id`, `tenant`, `scope`, `expires_at`, `revoked`, `created_at`, and never `token`. `GET /v1/admin/tokens` returns every token with those same fields plus `github_id`. A non-admin's call to the admin list is 403. A bearer on either list is 401.
  - The registry stores the SHA-256 of the plaintext, not the plaintext. Comparison is constant time, with no early exit, and the plaintext and the hash are never logged.
  - `POST /v1/tokens/<id>/revoke` revokes that token before `expires_at`. The owner may revoke their own. The admin may revoke any. A second revoke of an already-revoked token is 204. Revoke takes effect on the next request, including in a process that has not restarted.
  - A domain-policy change does not revoke tokens.
  - The registry (owners, token hashes, policy, sessions' github id, github login, and verified emails) lives under `WORKFLOW_SERVE_DATA`, outside any tenant directory. Tenant facts stay at `WORKFLOW_SERVE_DATA/<tenant>/`. Restart loads the registry from that directory. Nothing about tokens is read from the environment.
  - The client scrub and the server precheck treat the `wk_` prefix as a secret, the same way they treat the other prefixes.
- Non-goals: editing scope or expiry in place; sharing a tenant with a second GitHub user; quotas; importing a `WORKFLOW_SERVE_KEYS` string into the registry.

### Domain: Request authorization

- Owns: how `/v1` chooses a tenant and whether the call may write. Does not own issuing.
- Contract:
  - Loopback is always local mode, whether or not the OAuth env is set. Local mode is empty of any requirement for a token: every request is tenant `local`, a bearer is ignored, a session is ignored, and a non-loopback bind without the OAuth env is refused at startup. `localGuard` stays. `WORKFLOW_SERVE_KEYS` set to anything but empty makes the process exit before it listens, on loopback or not, and the error names that variable.
  - Remote mode is only a non-loopback bind with the OAuth env set. Issued tokens are the only remote credentials. Remote mode still honors `WORKFLOW_SERVE_CORS_ORIGINS` for bearer reads: the exact origins listed, no wildcard, and no `Access-Control-Allow-Credentials`.
  - If the request has `Authorization: Bearer <token>`, the registry decides. Unknown, expired (`now >= expires_at`), or revoked is 401 `{"error":"unauthorized"}`. A `tenant` query that is present and differs from the token's tenant is 401. The session cookie is not consulted on a request that presented a bearer, so a session cannot widen a `read` token.
  - A valid `read` token may call the existing GET reads (`/v1/artifacts`, `/v1/checks`, `/v1/baselines`, `/v1/search`, `/v1/analytics/*`). `POST /v1/ingest` with a valid `read` token is 403 `{"error":"read-only token"}` and stores nothing. A valid `read_write` token may ingest and may call those GETs.
  - With no bearer, a session may call those GETs for a `tenant` query it owns, and may not call `POST /v1/ingest` (ingest is bearer-only). A missing `tenant`, or one the session does not own, is 403 `{"error":"no such tenant"}`.
  - No bearer and no session on a remote data route is 401 `{"error":"unauthorized: this service requires a token; sign in at <WORKFLOW_PUBLIC_URL>/login"}`. `workflow login` is the device path in client presentation. It is not a session, and the 401 does not name it.
  - On the collector origin the embedded site sends no `Authorization` header. It does not attach `workflow-analytics-key`. Its data GETs carry `?tenant=` taken from `GET /v1/me`. Pages `/settings` still stores a pasted bearer, sends that bearer, and does not send the session cookie.
  - `GET /v1/health` stays unauthenticated. Profile and admin routes reject a bearer with 401; they accept only a session, as the identity contract says.
  - `GET /v1/me` with a session returns `{"github_id","github_login","admin","tenants":[{"name"}]}`. `github_login` is the login stored on the session. Without a session it is 401.
- Non-goals: credentialed CORS (no `Access-Control-Allow-Credentials`); a bearer that names an arbitrary tenant; keyed local mode.

### Domain: Client presentation

- Owns: where a device or a remote agent gets the endpoint and the token it sends. Does not own issuing.
- Contract:
  - `clientconfig` resolution, used by the drain, by `workflow status`, and by `workflow mcp`:
    1. `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` both set: remote mode, those values. They win over `client.toml`.
    2. Exactly one of them set: bad config. `workflow drain`, `workflow mcp`, and `workflow status` fail before any request. They do not use `client.toml` and they do not contact loopback.
    3. Neither set, and `client.toml` present: `endpoint` and `key` as today.
    4. Neither set, and no file: local mode, `http://127.0.0.1:8770`, no bearer.
  - `WORKFLOW_CLIENT_CONFIG` still overrides only the file path.
  - The drain's ingest request stays `POST <endpoint>/v1/ingest` with `Authorization: Bearer <key>` when the resolved key is non-empty. The MCP shim's GETs use the same resolution.
  - A hand-written `client.toml` (`endpoint`, `key`) still works. A Claude or Codex remote agent that has no browser is configured by setting `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` in that agent's environment.
  - `workflow login` is how a person at a device points a client at the collector. It does not change local loopback serve, which still requires no keys.
  - `workflow login` takes an optional `--endpoint` (the collector origin, no path). When the flag is omitted, the `endpoint` already in `client.toml` is used. When the flag is omitted and there is no endpoint, the command exits without writing a key.
  - The command listens on loopback and opens the system browser to the collector's device page, carrying `state` and that loopback redirect. If the browser has no session, the collector sends it through GitHub login and back to the device page, not to `/`. The device page lists tenants this user owns and asks which tenant, which grant (`read` or `read_write`), and the lifetime (`expires_at`, RFC3339 UTC, strictly in the future). The collector does not fill those in. There is no server-side lifetime default. A submit that omits any of them creates no token.
  - The page does not silently choose among several tenants, and it does not silently choose the grant. It does not name a tenant from the GitHub login. If the user owns none, they type a name and the page creates it through `POST /v1/tenants`. Abandoning the page writes no token and leaves `client.toml` unchanged.
  - On submit the collector creates the token and redirects the browser only to the loopback URI from this login, and only with a one-time code plus `state`, never the plaintext. Any other redirect is refused and creates no token. The CLI checks `state`. Its exchange is not a session and is not subject to the collector `Origin` rule. The exchange returns the plaintext once; the code then dies. A second exchange is 401 and returns no token. The code is not `Authorization` and does not authorize any `/v1` data route. The command writes `endpoint` and `key` into `client.toml` and does not print the token. The code and the token are not logged. Writing the file does not revoke the previous token; that token stays valid until it expires or is revoked.
  - That token is an ordinary issued token: one tenant, the grant the user chose, the expiry the user set, revocable from the profile. Profile creation is unchanged: the profile still asks for tenant, scope, and expiry, and its create response is still the only profile response that contains the plaintext. The device page's create response to the browser does not contain the plaintext.
- Non-goals: the collector pushing `client.toml` onto a machine that did not run `workflow login`; `workflow init`; flags that skip the device page's questions; a silent default tenant, grant, or lifetime.

### Domain: Collector hosting

- Owns: the fly.io process that is the remote collector. Does not own a second replica.
- Contract:
  - One fly.io machine runs the `workflow serve` binary. A volume holds `WORKFLOW_SERVE_DATA`. The GitHub OAuth app's callback is `https://<collector>/oauth/callback`, and `WORKFLOW_PUBLIC_URL` is that origin. `WORKFLOW_SERVE_KEYS` is unset. The GitHub client secret is a fly secret, not a file in the repo.
  - After a restart, a token that was valid before the restart still authorizes, and a token revoked before the restart still does not.
  - Cloudflare Pages, if still used, remains a static site that sends a pasted bearer from `/settings`. It does not receive the session cookie. The fly app sets `WORKFLOW_SERVE_CORS_ORIGINS` to that Pages origin. Credentialed CORS stays off.
- Non-goals: more than one machine; putting the fact ledger on anything other than the volume's tenant directories.

## Architectural Implications

- Design 3's "registration, key issue and rotation are out of scope", the env-only key list, and the 1:1 key/tenant rule are replaced by this contract. Design 2's "not env vars" is narrowed: a remote agent's `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` are a supported client configuration, and hook environments that set neither are unchanged. Design 2 and design 5's "`workflow login` (not built yet)" becomes this command: it opens the collector's login, and the device page issues the token the command writes into `client.toml`. Design 7's "no user identity" and the unrotated pasted tenant key stop being the collector's dashboard auth. The pasted key remains the Pages path.
- `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` still describe plan 08 and the workflow-quality service. Design 1 already marks plan 08 superseded. This design does not take those two pages as the service contract, and it does not rewrite them.
- Plan 09's record says `workflow init` was built and writes `client.toml`. The command is absent on master, and this design does not add it. `workflow login` is the command that writes `client.toml`. A hand-written file and the remote-agent env pair remain valid.
- The 2026-10-11 cutover in design 7 is a local keyless systemd unit. It stays on the local-mode contract. A deployment that today depends on `WORKFLOW_SERVE_KEYS` has to have its clients re-issued tokens; there is no import.
- CORS stays credential-less. The session is same-origin on the collector. Pages cannot send the cookie. Remote bearer reads still require `WORKFLOW_SERVE_CORS_ORIGINS`.
- Phase count is four. `refine` is not skipped.

## Decisions

Interactive. The turn record is in `PROVENANCE.md`.

- One GitHub account; the user can create as many tenants as they want, and provide read only or read + write access with the token, plus set a lifetime on the token.
- Any GitHub user can log in. Admins are recognised as `codyh@ctzns.net`. The admin can configure which email domains are allowed (allow list or everyone).
- Session opens the analytics dashboard. Issued tokens replace `WORKFLOW_SERVE_KEYS`. Local still does not require keys.
- A token belongs to one tenant. Scope is read, or read and write. It has a lifetime. The profile can revoke it before the lifetime ends.
- The GitHub session authorizes the dashboard and the profile. Agents keep using `Authorization: Bearer`. A read token cannot ingest. A read+write token can ingest and read. Expired or revoked is unauthorized.
- On the remote collector there is no `WORKFLOW_SERVE_KEYS`. Local loopback stays keyless and still refuses a non-loopback bind.
- `workflow login` opens the collector. After GitHub auth, the device page asks which tenant and which grant (`read` or `read_write`), and the lifetime is set on that page. The command writes that token into `client.toml`. An automatic `read_write` grant, a 90-day default, a silently picked tenant, and a tenant named from the GitHub login are not part of this design.
- Held for the checkpoint, not re-asked: admin revoke of any token; policy change does not itself revoke tokens; admin can still log in when the allow list omits `ctzns.net`; default policy `everyone`; session length 14 days with no sliding renewal; exact domain match; `read` on ingest is 403 and expiry or revocation is 401; scope and expiry are not editable in place; env wins over `client.toml` when both pairs are present; the device page asks for tenant, grant, and lifetime with no silent default; all four phases are known.

## Assumption Ledger

None — see PROVENANCE.md.

## Open Questions

None.

## Phases

Ordered. The count is fixed at sign-off. A phase closes when its outcome is provably true. `refine` adds a Units list under a phase when it refines it; `execute` records the phase's outcome and carried items in IMPLEMENTATION.md.

### Phase 1 — GitHub login and admission

- Outcome: A non-loopback `workflow serve` with the OAuth env set and `WORKFLOW_SERVE_KEYS` unset starts and is not local mode. The same bind with `WORKFLOW_SERVE_KEYS` set, or with the OAuth env missing, exits before it listens. A dashboard GitHub login as a verified `codyh@ctzns.net` sets `workflow_session` and lands on `/`. That admin still gets a session when the allow list omits `ctzns.net`. A GitHub user who fails the allow list gets `/login?error=denied` and no cookie. On that bind, `GET /v1/analytics/summary` with no session is 401, not tenant `local`; `POST /v1/ingest` with no bearer stores nothing (401); `POST /v1/ingest` with a session and no bearer stores nothing. A session's summary request with no owned tenant is 403 `{"error":"no such tenant"}`, and the site does not treat that as a logged-out 401. The collector-origin site sends no stored bearer. The admin can `PUT /v1/admin/policy` to `allow_list` or back to `everyone`, and the next login follows it; a non-admin's `PUT` is 403. A session that the new policy would deny is cleared on its next request and then gets no dashboard data. Loopback serves `/` and `GET /v1/analytics/summary` for tenant `local` with no cookie and no bearer, including when the OAuth env is set. `docs/design/05-distribution.md` and `docs/design/07-analytics-site.md` describe this login and no longer say the dashboard has no user identity.
- Surfaces: `tools/workflow/internal/serve/serve.go` (`ConfigFromEnv`, `Handler`, new `/oauth/login`, `/oauth/callback`, `/logout`, `/v1/me`, `/v1/admin/policy`), `tools/workflow/internal/serve/site.go`, `packages/workflow-analytics/src/lib/api.ts`, `packages/workflow-analytics/src/routes/+layout.svelte`, new `/login` route in that site, `docs/design/05-distribution.md`, `docs/design/07-analytics-site.md`.
- Approach: known
- Depends on: nothing

#### Units

| Unit | Brief | Depends on | Alongside |
|---|---|---|---|
| Registry and remote mode config | [briefs/1-01-registry-remote-config.md](briefs/1-01-registry-remote-config.md) | nothing | nothing |
| OAuth, session, and remote request auth | [briefs/1-02-oauth-session-remote-auth.md](briefs/1-02-oauth-session-remote-auth.md) | 1-01 | nothing |
| Analytics site session mode | [briefs/1-03-analytics-session-site.md](briefs/1-03-analytics-session-site.md) | 1-02 | nothing |
| Design docs for login and admission | [briefs/1-04-design-docs-login.md](briefs/1-04-design-docs-login.md) | 1-02, 1-03 | nothing |

### Phase 2 — Issued tokens are the remote credential

- Outcome: A logged-in user `POST`s a tenant and a `read_write` token with a future `expires_at`, and the profile create response is the only profile response that contains the plaintext. `POST /v1/ingest` with `Authorization: Bearer` of that token stores a fact in that tenant; `GET /v1/analytics/summary` with it returns that tenant. The same tenant's `read` token gets 403 `read-only token` on ingest and stores nothing, and 200 on the summary. After the owner revokes, or after `expires_at`, the same POST is 401 and stores nothing. `GET /v1/tokens` lists the owner's tokens without `token`. `GET /v1/admin/tokens` lists every token without `token`. The admin revokes another user's token from that list, and the next ingest with it is 401 without a restart. Changing the domain policy does not revoke that token: it still ingests. A session `GET /v1/analytics/summary?tenant=<owned>` returns that tenant; a tenant the session does not own is 403. After login, with one owned tenant, `/` shows that tenant's summary from a cookie-only request whose `tenant` comes from `GET /v1/me`, and the site does not send a stored bearer. A submitted fact whose text contains a `wk_` token is stored without that secret. Restarting the process does not forget the token or the revocation. Starting with `WORKFLOW_SERVE_KEYS` set exits before listen. `docs/design/03-remote-service.md` states this and no longer says registration, key issue, or rotation are out of scope.
- Surfaces: `tools/workflow/internal/serve/serve.go` (`ConfigFromEnv`, `ParseKeys`, `auth`, `tenantFor`, `GET /v1/tokens`, `GET /v1/admin/tokens`), `tools/workflow/internal/serve/host.go` (`tenantForKey`), the registry under `WORKFLOW_SERVE_DATA`, `packages/workflow-analytics` `/` and `/profile`, `packages/workflow-analytics/src/lib/api.ts`, `tools/workflow/internal/secrets/secrets.go`, `docs/design/03-remote-service.md`.
- Approach: known
- Depends on: Phase 1

#### Units

| Unit | Brief | Depends on | Alongside |
|---|---|---|---|
| Registry, tenancy, and bearer authorization | [briefs/2-01-registry-tenancy-bearer.md](briefs/2-01-registry-tenancy-bearer.md) | Phase 1 | nothing |
| `wk_` workflow token secret scrub | [briefs/2-02-wk-secret-scrub.md](briefs/2-02-wk-secret-scrub.md) | 2-01 | 2-03, 2-04 |
| Profile UI, collector overview, and e2e setup | [briefs/2-03-analytics-profile-e2e.md](briefs/2-03-analytics-profile-e2e.md) | 2-01 | 2-02, 2-04 |
| Design doc for issued remote credentials | [briefs/2-04-design-docs-remote-tokens.md](briefs/2-04-design-docs-remote-tokens.md) | 2-01 | 2-02, 2-03 |

### Phase 3 — Devices and remote agents present a token

- Outcome: With `WORKFLOW_ENDPOINT` set to the collector and `WORKFLOW_KEY` set to a live `read_write` token, and with no `client.toml`, `workflow drain` delivers a spooled fact (`POST /v1/ingest` succeeds) and `workflow mcp` reads with that bearer. A `client.toml` of `endpoint` and `key`, with those two env vars unset, does the same. Neither file nor env is local mode and sends no bearer. Setting exactly one of `WORKFLOW_ENDPOINT` or `WORKFLOW_KEY` makes `workflow drain`, `workflow mcp`, and `workflow status` fail before any request; they do not use the file and they do not contact loopback. `workflow login --endpoint <collector>` opens the browser and, after GitHub auth, returns to the device page. That page issues no token until the user has chosen a tenant, a grant (`read` or `read_write`), and an expiry, and it does not invent a lifetime. If the user has no tenant, they type a name and the page creates it. The browser is sent only to that login's loopback URI, with a one-time code and `state`, and the page response contains no plaintext. The CLI exchange, which is not under the collector `Origin` rule, writes `endpoint` and `key` into `client.toml` and prints no token. A drain using a `read_write` token from that file delivers. A `read` token from that file leaves ingest 403 and storing nothing, and `workflow mcp` reads succeed. The previous token still authorizes until it expires or is revoked. Quitting the page writes nothing. A hand-written `client.toml` still works. Loopback serve still answers with no keys. `docs/design/02-edge-capture.md` and `docs/design/05-distribution.md` describe this command and this resolution. `workflow init` is not added.
- Surfaces: `tools/workflow/cmd/workflow/main.go`, `tools/workflow/internal/clientconfig/clientconfig.go`, `tools/workflow/internal/drain/cli.go`, `tools/workflow/internal/drain/http.go`, `tools/workflow/internal/mcp/feedback.go`, the device page on the collector (`tools/workflow/internal/serve/serve.go`, `packages/workflow-analytics`), `tools/hooklog/README.md`, `docs/design/02-edge-capture.md`, `docs/design/05-distribution.md`.
- Approach: known
- Depends on: Phase 2

#### Units

| Unit | Brief | Depends on | Alongside |
|---|---|---|---|
| Client config and env resolution | [briefs/3-01-clientconfig-env-resolution.md](briefs/3-01-clientconfig-env-resolution.md) | Phase 2 | 3-02 |
| Device authorization server | [briefs/3-02-device-auth-server.md](briefs/3-02-device-auth-server.md) | Phase 2 | 3-01 |
| Device page | [briefs/3-03-device-page.md](briefs/3-03-device-page.md) | 3-02 | 3-04, 3-05 |
| workflow login CLI | [briefs/3-04-workflow-login-cli.md](briefs/3-04-workflow-login-cli.md) | 3-02 | 3-03, 3-05 |
| Design docs for client login | [briefs/3-05-design-docs-client-login.md](briefs/3-05-design-docs-client-login.md) | 3-01, 3-02, 3-04 | 3-03 |

### Phase 4 — The collector runs on fly.io

- Outcome: The fly app's public https origin answers `GET /v1/health` with no bearer and `GET /oauth/login` with a redirect to GitHub. The OAuth app callback is that origin's `/oauth/callback`. `WORKFLOW_SERVE_KEYS` is unset on the app. A `read_write` token that ingested before a machine restart ingests into the same tenant after it, and a token revoked before the restart does not. With `WORKFLOW_SERVE_CORS_ORIGINS` set to the Pages origin, a browser on that origin can `GET /v1/analytics/summary` with a bearer, a browser on any other origin cannot, and the response has no `Access-Control-Allow-Credentials`. `docs/design/07-analytics-site.md` names this fly collector as the remote host and leaves the Pages pasted-token path as a static client.
- Surfaces: new `fly.toml`, `docs/design/07-analytics-site.md` hosting section. The binary and registry are the Phase 2 surfaces, unchanged in role.
- Approach: known
- Depends on: Phase 2

#### Units

| Unit | Brief | Depends on | Alongside |
|---|---|---|---|
| Fly collector manifest | [briefs/4-01-fly-collector-manifest.md](briefs/4-01-fly-collector-manifest.md) | Phase 2 | nothing |
| Fly collector deploy | [briefs/4-02-fly-collector-deploy.md](briefs/4-02-fly-collector-deploy.md) | 4-01 | nothing |
| Fly collector outcome verify | [briefs/4-03-fly-collector-outcome-verify.md](briefs/4-03-fly-collector-outcome-verify.md) | 4-02 | 4-04 |
| Design docs for fly hosting | [briefs/4-04-design-docs-fly-hosting.md](briefs/4-04-design-docs-fly-hosting.md) | 4-01 | 4-03 |

## Provenance Notes

The current `ParseKeys` rule (one key, one tenant, loaded once from the environment) is what makes issuing, scopes, lifetimes, and revoke unexpressible. The replacement is a registry the request path reads, not a longer env string.

The dashboard uses the session because that is what was asked. Design 7's "later, a short-lived browser token" is not this design. Agents stay on bearer tokens because a GitHub session cannot be configured into a Claude or Codex remote agent.

`workflow login` opens the collector and writes the token the device page issued. It is not a silent issuer: the page asks for the tenant, the grant, and the lifetime. The earlier automatic `read_write`, 90-day, and GitHub-login tenant defaults are not in the contract. A missing bearer on a remote data route points at the login page, not at the command. The login page from phase 1 is still how the dashboard session starts.

Pages keeps the pasted token because the cookie is same-origin and CORS stays without credentials. Teaching Pages to send the session would be a different design.

All four phases are marked known: GitHub's code flow, a persisted token registry, the existing bearer header, and one fly machine with a volume are settled approaches. None is open.
