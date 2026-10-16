# Brief: 3-02 — Device authorization server

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 3.
Owned paths: `tools/workflow/internal/serve/device.go` (new), `tools/workflow/internal/serve/registry.go` (device-code persistence only), `tools/workflow/internal/serve/serve.go` (route registration for device exchange only), `tools/workflow/internal/serve/serve_test.go` (device flow tests), `docs/plans/13-client-registration/reports/3-02-device-auth-server.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/3-02-device-auth-server.md` and include it in the commit.
Depends on: phase 2 (closed).
Runs alongside: 3-01.
Budget: 14 files to read, about 900 lines to change including tests, 70 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Client presentation (device page, redirect, exchange, no plaintext in browser response), Domain: Identity and admission (`Origin` rule; device exchange not a session route).
2. `docs/plans/13-client-registration/reports/2-01-registry-tenancy-bearer.md` — `CreateToken`, registry persist, session-only profile routes.
3. `tools/workflow/internal/serve/tokens.go` — `POST /v1/tokens` session handler.
4. `tools/workflow/internal/serve/oauth.go` — `workflow_oauth_return` cookie pattern.
5. `tools/workflow/internal/serve/session.go` — `originGuard`, `sessionOnly`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Add collector-side device authorization: a session-authenticated create path used by the device page that mints a one-time code bound to a loopback redirect and `state`, plus a code exchange endpoint that returns the issued `wk_` plaintext once and is not subject to the collector `Origin` rule.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Client presentation**

- "On submit the collector creates the token and redirects the browser only to the loopback URI from this login, and only with a one-time code plus `state`, never the plaintext. Any other redirect is refused and creates no token."
- "The CLI checks `state`. Its exchange is not a session and is not subject to the collector `Origin` rule. The exchange returns the plaintext once; the code then dies. A second exchange is 401 and returns no token. The code is not `Authorization` and does not authorize any `/v1` data route."
- "The device page's create response to the browser does not contain the plaintext."
- "There is no server-side lifetime default. A missing or non-future `expires_at` creates no token."
- "That token is an ordinary issued token: one tenant, the grant the user chose, the expiry the user set, revocable from the profile."

**Identity and admission**

- "Mutating session routes require `Content-Type: application/json` and an `Origin` equal to `WORKFLOW_PUBLIC_URL` … The device-code exchange is not a session route and is not subject to that `Origin` rule."

**Tenancy and tokens** (reuse existing issue rules)

- "`POST /v1/tokens` with `{\"tenant\",\"scope\",\"expires_at\"}` and a session that owns the tenant returns 201 … `token` is the plaintext (`wk_` plus an unguessable body). On this profile route it appears only in this response."

Device create may be a new route (e.g. session + JSON body including `redirect_uri`, `state`, `tenant`, `scope`, `expires_at`) or extend profile create with device fields — choose one shape, document it in the report, and keep exchange separate from profile plaintext-in-JSON.

## Changes

- Persist short-lived device codes in the registry (hashed or opaque id → token id + redirect binding + state + expiry). Refuse redirect URIs that are not loopback http(s).
- Session-authenticated handler: validate tenant ownership, scope, and future `expires_at`; call existing token issue; store code; respond with 302/303 to the allowed loopback URI with `code` and `state` query params only (no `token` in URL fragment or body).
- Exchange handler: `POST` with `code`, `state`, and the same `redirect_uri` the CLI registered; constant-time code lookup; on match return JSON `endpoint` (collector origin) and `token` once; delete or invalidate code; second attempt 401.
- Register routes on remote mode only; loopback local mode need not expose device exchange (tests may use remote handler fixture).
- **Carried item 2 (`Server.New` panic)**: keep current panic-on-registry-failure behavior; do not add graceful degradation.
- **Carried item 4 (profile expiry prefill)**: server must still reject missing/non-future `expires_at` on device create; no server default.

### Keep untouched

- `packages/workflow-analytics` (unit 3-03).
- `workflow login` CLI (unit 3-04).
- Profile `POST /v1/tokens` response shape for dashboard create (plaintext in JSON remains profile-only).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/serve/ -run Device -count=1` → pass, covering: session create issues token + redirect with code; exchange returns plaintext once; second exchange 401; wrong `state` or non-loopback redirect refused; exchange works without `Origin` header; code does not authorize `GET /v1/analytics/summary`.
- `cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/serve/ -count=1` → full package pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
