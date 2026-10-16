# Brief: 2-01 — Registry, tenancy, and bearer authorization

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 2.
Owned paths: `tools/workflow/internal/serve/registry.go`, `tools/workflow/internal/serve/tokens.go` (new, if you split handlers from `serve.go`), `tools/workflow/internal/serve/serve.go` (routes and `authorizeRequest` / ingest auth only — do not change OAuth or site), `tools/workflow/internal/serve/host.go` (`tenantForKey` only), `tools/workflow/internal/serve/serve_test.go` (token, tenant, bearer scope, persistence tests), `docs/plans/13-client-registration/reports/2-01-registry-tenancy-bearer.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/2-01-registry-tenancy-bearer.md` and include it in the commit.
Depends on: phase 1 (closed).
Runs alongside: nothing.
Budget: 14 files to read, about 1100 lines to change including tests, 75 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Tenancy and tokens (full contract), Domain: Request authorization (full contract), Phase 2 outcome (HTTP and persistence portions).
2. `docs/plans/13-client-registration/reports/1-02-oauth-session-remote-auth.md` — `authorizeRequest`, `sessionOnly`, `originGuard` as built.
3. `tools/workflow/internal/serve/registry.go` — current `owners`, `TokenHashRecord` placeholder.
4. `tools/workflow/internal/serve/session.go` — `authorizeRequest`, `handleMe`.
5. `tools/workflow/internal/serve/host.go` — `tenantForKey`.
6. `tools/workflow/internal/serve/serve_test.go` — `mockGitHub`, `loginRemote`, `newRemoteServer` patterns.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Implement tenant ownership, issued API tokens in the registry, profile/admin HTTP routes, and remote bearer authorization (including `read` vs `read_write` on ingest) so the phase 2 outcome holds for API and persistence without the analytics site or `wk_` scrub changes.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Tenancy and tokens**

- "A tenant name matches the name rule serve already uses (`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`). Names are unique on the collector. The creating user owns it. There is no transfer and no delete."
- "`POST /v1/tenants` with `{\"name\":\"<name>\"}` and a session creates that tenant and returns 201 `{\"name\":\"<name>\"}`. A taken name is 409. A bearer token calling this route is 401."
- "A token belongs to exactly one tenant. Scope is `read` or `read_write`, chosen at creation, not changed later. `expires_at` is required, RFC3339 UTC, and must be strictly in the future. There is no token without an expiry and no sliding expiry."
- "`POST /v1/tokens` with `{\"tenant\",\"scope\",\"expires_at\"}` and a session that owns the tenant returns 201 `{\"id\",\"token\",\"tenant\",\"scope\",\"expires_at\"}`. `token` is the plaintext (`wk_` plus an unguessable body). On this profile route it appears only in this response. There is no server-side lifetime default: a missing or non-future `expires_at` creates no token. A tenant the caller does not own is 403."
- "`GET /v1/tokens` with a session returns that owner's tokens as `id`, `tenant`, `scope`, `expires_at`, `revoked`, `created_at`, and never `token`. `GET /v1/admin/tokens` returns every token with those same fields plus `github_id`. A non-admin's call to the admin list is 403. A bearer on either list is 401."
- "The registry stores the SHA-256 of the plaintext, not the plaintext. Comparison is constant time, with no early exit, and the plaintext and the hash are never logged."
- "`POST /v1/tokens/<id>/revoke` revokes that token before `expires_at`. The owner may revoke their own. The admin may revoke any. A second revoke of an already-revoked token is 204. Revoke takes effect on the next request, including in a process that has not restarted."
- "A domain-policy change does not revoke tokens."
- "The registry (owners, token hashes, policy, sessions' github id, github login, and verified emails) lives under `WORKFLOW_SERVE_DATA`, outside any tenant directory. … Restart loads the registry from that directory. Nothing about tokens is read from the environment."

**Request authorization**

- "If the request has `Authorization: Bearer <token>`, the registry decides. Unknown, expired (`now >= expires_at`), or revoked is 401 `{\"error\":\"unauthorized\"}`. A `tenant` query that is present and differs from the token's tenant is 401. The session cookie is not consulted on a request that presented a bearer, so a session cannot widen a `read` token."
- "A valid `read` token may call the existing GET reads … `POST /v1/ingest` with a valid `read` token is 403 `{\"error\":\"read-only token\"}` and stores nothing. A valid `read_write` token may ingest and may call those GETs."
- "With no bearer, a session may call those GETs for a `tenant` query it owns, and may not call `POST /v1/ingest` (ingest is bearer-only). A missing `tenant`, or one the session does not own, is 403 `{\"error\":\"no such tenant\"}`."
- "`GET /v1/health` stays unauthenticated. Profile and admin routes reject a bearer with 401; they accept only a session, as the identity contract says."
- "`WORKFLOW_SERVE_KEYS` set to anything but empty makes the process exit before it listens, on loopback or not, and the error names that variable." (unchanged from phase 1; confirm still true.)

**Phase 2 outcome (this unit)**

- Session creates tenant and `read_write` token; bearer ingest and summary for that tenant; `read` token ingest 403 and summary 200; revoke and expiry → ingest 401; lists omit plaintext; admin revokes another user's token; policy change does not invalidate token; session GET summary for owned vs unowned tenant; restart retains token and revocation.

Decisions for this unit:

- **Token id**: opaque string (UUID or random hex) stable in registry; URL path `/v1/tokens/<id>/revoke` uses it.
- **Plaintext shape**: `wk_` + at least 32 bytes of URL-safe randomness (exact length is implementation detail; must be unguessable).
- **`tenantForKey`**: on `cfg.Remote()`, look up only the registry hash table (not `cfg.Keys`). On `cfg.Local()`, keep ignoring bearer for tenant resolution (local mode unchanged). Tests that still pass `Config.Keys` for keyed httptest servers may keep env-key comparison until those tests are migrated; production remote servers have empty `Keys`.
- **Bearer wins**: when `Authorization: Bearer` is present, ignore session for data routes (already true); attach resolved scope to request context for ingest check.
- **Profile routes**: `POST /v1/tenants`, `POST /v1/tokens`, `GET /v1/tokens`, `GET /v1/admin/tokens`, `POST /v1/tokens/<id>/revoke` — session-only + `originGuard` on mutating routes (same Origin rule as `PUT /v1/admin/policy`).
- **Tenant creation** does not open ledger until first ingest (existing `tenant()` lazy open is fine).

## Changes

- Flesh out `TokenHashRecord` and registry CRUD: owners map, create/list/revoke/lookup by hash, persist on each mutating change.
- Implement handlers for tenant and token routes; wire in `Handler`.
- Extend `authorizeRequest` (or ingest `auth` wrapper) for registry bearer lookup, scope, tenant query mismatch, and `read-only token` on ingest.
- Replace remote `tenantForKey` body to use registry constant-time compare across all stored hashes.
- Add tests: full phase 2 HTTP matrix with `mockGitHub` + `loginRemote`; reload registry from disk in test to prove restart; tighten policy after token issue and show ingest still works.

### Keep untouched

- `packages/workflow-analytics` (unit 2-03).
- `tools/workflow/internal/secrets` (unit 2-02).
- OAuth flow files except route registration lines in `serve.go` if unavoidable.
- **`Server.New` panics** if the registry cannot be opened or persisted (phase 1 carried item — do not soften to error return).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/serve/ -run 'Token|Tenant|Bearer|Registry' -count=1` → pass (new tests covering issue, ingest scopes, revoke, expiry, admin list/revoke, policy non-revocation, restart load).
- `cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/serve/ -count=1` → pass full package.
- Observable: remote httptest with session `POST /v1/tokens` returns 201 JSON containing `token` prefix `wk_`; same token bearer `POST /v1/ingest` → 200; `read` scope ingest → 403 body contains `read-only token`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
