# Provenance: Client registration

Interactive posture only. Headless runs carry intent, the assumption ledger, and decisions in `DESIGN.md` alone.

## Session

- Session: Initial design (October 16, 2026)
- Timestamp: 2026-10-16T11:05:00Z
- CWD: /workspace

## Initial Request (verbatim)

> Important next step for this workflow service is to be able to run it as a collector on fly.io, so that both cloud and local agents can post events. Key item we are missing is client registration, which will be via keys we issue from the service. I'm wondering if we can do it like this - we register this as a github oauth app. We have a login page on the service, which logs the user in with github. On the user profile page we let them create api tokens, which then can be configured in various places - user device, claude / codex remote agent env etc for submitting events and getting data. feasible? /design

## Design Conversation

### Turn 1

**User responded:** The collector should run on fly.io so cloud and local agents can post events. Registration is the missing piece, via keys the service issues. The shape he proposed: register the service as a GitHub OAuth app; a login page logs the user in with GitHub; a profile page lets them create API tokens; those tokens are configured on a user device and in Claude/Codex remote agent env for submitting events and getting data.

**Agent decisions:**

- Treat that shape as the design, not as a question to re-litigate. Ground first against the serve auth path and the stable docs.

### Turn 2

**User responded:**

- One GitHub account; the user can create as many tenants as they want, and provide read only or read + write access with the token, plus set a lifetime on the token.
- Any GitHub user can log in. Admins are recognised as codyh@ctzns.net. The admin can configure which email domains are allowed (allow list or everyone).
- Session opens the analytics dashboard. Issued tokens replace WORKFLOW_SERVE_KEYS. Local still does not require keys.

Boundaries given with those answers: a token belongs to one tenant; scope is read, or read and write; it has a lifetime; the profile can revoke it before the lifetime ends. The GitHub session authorizes the dashboard and the profile. Agents keep using Authorization: Bearer. A read token cannot ingest. A read+write token can ingest and read. Expired or revoked is unauthorized. Local loopback stays keyless and still refuses a non-loopback bind. On the remote collector, issued tokens are the credentials and there is no WORKFLOW_SERVE_KEYS. Admin is the verified GitHub email codyh@ctzns.net. Domain policy is allow-list or everyone, edited by that admin. Logins that fail the policy get no session.

**Agent decisions:**

- Do not re-open those. Record the revoke-before-lifetime rule as part of the contract, correctable at the checkpoint.
- Identity is one GitHub user id per account. That user may own many tenants, and a tenant may have many tokens. Each token has one tenant, one scope, and one expiry.
- The session is the person's credential for the dashboard and the profile. It is not sent as a bearer, and it cannot ingest.
- `WORKFLOW_SERVE_KEYS` is not kept as a hidden admin path. If it is set, the process refuses to start.
- All four phases are known.

### Turn 3

**User responded:** could `workflow login` automatically open the website, then when the user authenticates it creates a token which is then stored in config (effectively an automatic api token created and saved).

The contract sent with that sentence: the command opens the system browser, listens on loopback, and after GitHub auth writes one token into `client.toml`. The automatic token was `read_write`, lifetime 90 days, revocable from the profile. No tenant yet meant create one named from the GitHub login; exactly one meant that tenant; more than one meant the page asks. Flags `--tenant`, `--scope`, and `--expires` would override those defaults.

**Agent decisions:**

- Not written into the design. The next turn superseded it before it landed.

### Turn 4

**User responded:** "The device code creation page can ask for which tenancy and grant for the device."

That supersedes the automatic token. `workflow login` still opens the website and, after GitHub auth, writes the issued token into `client.toml`. The page that creates that device credential asks which tenant and which grant (`read` or `read_write`). Lifetime is set on that same page. If the user has no tenant yet, that page can create one. It does not silently choose among several tenants, and it does not silently choose the grant. Profile token creation is unchanged. Remote agents with no browser still use `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY`. Local loopback still needs no keys.

**Agent decisions:**

- Drop automatic `read_write`, the 90-day default, a silently picked tenant, and a tenant named from the GitHub login. Do not keep the override flags that existed only to change those defaults.
- Keep the loopback one-time code: the browser comes back with a code, the command exchanges it, writes `client.toml`, and does not print or log the token.
- The device page is where tenant, grant, and lifetime are chosen. Phase 3's outcome includes `workflow login`. Phase 1 stays the GitHub session.

### Turn 5

**User responded:** Apply the adversarial findings. Keep the device page (tenant, grant, lifetime; no silent defaults). Do not add a fifth phase.

**Agent decisions:**

- These came from the adversarial pass and were applied. The pass had read the store copy from before the device page; findings that only said to add `workflow login` were already in the contract and stayed.
- The HTTP 401 points at the login page, not at the command. `workflow init` stays out.
- A dashboard login lands on `/`. A device login returns to the device page. Zero tenants means the user types a name. There is no server-side lifetime default. Abandoning the page writes nothing.
- The handoff is a loopback one-time code plus `state`. The exchange is not under the collector `Origin` rule. Plaintext goes only to the CLI. The redirect is only that loopback URI. The code is not a data credential. Login does not revoke the previous token. A `read` token in `client.toml` makes ingest 403, and `workflow mcp` still reads.
- Collector-origin data calls are cookie-only, with `?tenant=` from `GET /v1/me`. The site does not send a stored bearer. Pages still pastes a bearer.
- Phase 1: unauthenticated and session-only `POST /v1/ingest` store nothing. The admin can log in when the allow list omits `ctzns.net`. A session the policy would now deny is cleared.
- `GET /v1/tokens` is the owner's list. `GET /v1/admin/tokens` is every token. Phase 2 shows admin revoke without a restart, and a policy change leaves an existing token valid. A `wk_` token is scrubbed before it is stored.
- Remote mode still honors `WORKFLOW_SERVE_CORS_ORIGINS`. Credentialed CORS stays off.
- Exactly one of `WORKFLOW_ENDPOINT` or `WORKFLOW_KEY` fails before any request.
- The session stores the GitHub login, so `GET /v1/me` may return `github_login`.
- Loopback is always local mode and ignores the OAuth env.

## Agent Decisions

- **Admin lockout**: the verified admin email can log in even when the allow list does not include `ctzns.net`. Rationale: otherwise the only person who can edit the policy can remove themselves.
- **Default policy**: `everyone`, until the admin changes it. Rationale: "any GitHub user can log in" is the starting rule; the allow list is a later tightening.
- **Policy versus existing tokens**: changing the domain policy does not revoke tokens. The admin can revoke any token; the owner can revoke their own. Rationale: he tied the policy to logins getting no session, not to credentials already issued, and a locked-out user's token would otherwise keep working with no one able to stop it.
- **Session length**: 14 days from login, not renewed by activity. Rationale: a length has to be checkable; he did not name one.
- **Domain match**: exact host part, case-insensitive. Rationale: "email domains" with no mention of subdomains.
- **Read token on ingest**: 403 `read-only token`. Unknown, expired, or revoked: 401 `unauthorized`. Rationale: he reserved "unauthorized" for expired or revoked; a read token is a valid credential that must not write.
- **Scope and expiry**: not editable. A different access is a new token. Rationale: he described setting them when the token is created, and revoke covers taking one back.
- **Env versus file**: `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` together win over `client.toml`. Exactly one of them is bad config. Rationale: he asked for remote-agent env, and design 2's objection was hook environments that are not a deliberate client config. A hook that sets neither is unchanged.
- **`workflow login`**: the command opens the collector and writes the token the device page issued into `client.toml`. The page asks for the tenant, the grant, and the lifetime. Rationale: he asked for the command, then replaced a silent automatic token with that page. `workflow init` is still not added.
- **Pages**: the pasted token on `/settings` stays for a cross-origin static site. The collector dashboard uses the session. Rationale: CORS has no credentials, and he did not ask to retire Pages.
- **Plan number**: `docs/plans/13-client-registration/`. Rationale: 12 is the highest prefix; 11 is an unused gap.
