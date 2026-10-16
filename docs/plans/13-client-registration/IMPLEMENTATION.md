# Client registration implementation

Tool: Cursor (Grok 4.7 orchestrator).
Run identity: https://cursor.com/agents/bc-3f650f40-1066-5daa-b196-4a4ab11ffc43
Started: 2026-10-16T11:35:03Z
Branch: `cursor/client-registration-3d44`
Starting HEAD: `33f90be`

Phase 1 is closed (`aa3c971`, `Workflow-Phase: client-registration:1`).

## Phase 2 — Issued tokens are the remote credential

Tool: Cursor (Grok 4.7 orchestrator).
Run identity: https://cursor.com/agents/bc-6714af74-e997-5724-81fe-38570d576092
Started: 2026-10-16T12:08:00Z
Resuming HEAD: `aa3c971`

Phase 2 only. Later phases are not started.

Refined into four units, committed in `3423391`. 2-01 first. After it, 2-02, 2-03, and 2-04 have disjoint paths. Phase 1 carried items: the e2e keyed setup and the overview `tenant` query go to 2-03; the registry-open panic stays as 2-01 left it.

artifact_feedback on the four phase 2 briefs: quality service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### 2-01-registry-tenancy-bearer

- Built: tenant create, issued `wk_` tokens stored as SHA-256, profile and admin token routes, bearer scope checks (read ingest is 403, revoked or expired is 401), and remote `tenantForKey` from the registry. A restart reloads the registry. A policy change does not revoke tokens.
- Surfaces: `tools/workflow/internal/serve/registry.go`, `tools/workflow/internal/serve/tokens.go`, `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/host.go`, `tools/workflow/internal/serve/session.go`, `tools/workflow/internal/serve/serve_test.go`.
- Commit: `a8cc689`. `go test ./internal/serve/` passed, including the token, tenant, and bearer tests.
- Deviations: token lists are a JSON array, not an object with a `tokens` field. `session.go` was edited; the brief's owned paths did not name it.
- Agent: Composer, harness did not report turns or final context.

### 2-02-wk-secret-scrub

- Built: the shared secret scanner treats `wk_` plus a 32-character body as `workflow_api_token` and redacts it.
- Surfaces: `tools/workflow/internal/secrets/secrets.go`, `tools/workflow/internal/secrets/secrets_test.go`.
- Commit: `11509e0`. `go test ./internal/secrets/` passed. `TestScanPatterns` failed before the pattern existed and passed after.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### 2-03-analytics-profile-e2e

- Built: `/profile` creates a tenant and a token, shows the plaintext once, lists tokens without it, and revokes. Admin sessions also load `GET /v1/admin/tokens`. Collector posts send the session cookie and no bearer. E2e global-setup no longer sets `WORKFLOW_SERVE_KEYS`; it starts a remote serve with a registry-seeded `wk_` bearer.
- Surfaces: `packages/workflow-analytics/src/lib/api.ts`, `packages/workflow-analytics/src/lib/api.test.ts`, `packages/workflow-analytics/src/routes/+layout.svelte`, `packages/workflow-analytics/src/routes/profile/+page.svelte`, `packages/workflow-analytics/tests/e2e/global-setup.ts`.
- Commit: `d0cc49a`. `npm test` passed (166). Playwright `session.spec.ts` and `settings.spec.ts` (excluding `@slow`) passed, 4 tests, after previously exiting because of `WORKFLOW_SERVE_KEYS`.
- Deviations: the e2e bearer is written into `registry.json` before serve starts, not issued through OAuth and `POST /v1/tokens`. Other analytics routes still omit `tenant`.
- Agent: Composer, harness did not report turns or final context.

### 2-04-design-docs-remote-tokens

- Built: `docs/design/03-remote-service.md` describes issued `wk_` tokens, GitHub session login, and a non-empty `WORKFLOW_SERVE_KEYS` refusing startup. It no longer says registration, key issue, or rotation are out of scope.
- Surfaces: `docs/design/03-remote-service.md`.
- Commit: `bf25bde`. A search of that file finds no `out of scope` and no `tenant=key` credential line. It names `wk_` and GitHub.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### Phase 2 verification

Outcome holds.

- A logged-in session `POST`ed tenant `acme` and a `read_write` token. The create response carried the `wk_` plaintext. `GET /v1/tokens` and `registry.json` did not. `POST /v1/ingest` with that bearer stored the fact under `acme`, and `GET /v1/analytics/summary?tenant=acme` returned 200. The same tenant's `read` token got 403 `read-only token` and stored nothing, and 200 on the summary.
- A fact whose text contained the `wk_` token was rejected by precheck and the plaintext was absent from the data directory. The same text after `Redact` was accepted and stored without the token.
- After the owner revoked, the next ingest was 401 and stored nothing. An in-process reload kept the token valid, and the revocation after that reload stuck. A separate OS restart of `workflow serve` on the same data directory still accepted the live token (`duplicate` for the fact stored before the restart) and still returned 401 for the revoked token. The plaintext was not on disk.
- A session summary for the owned tenant was 200; another tenant was 403 `no such tenant`. Tightening the domain policy left the bearer able to ingest.
- `go test` covering `TestToken`, `TestRegistryTenant`, `TestRegistryRestart`, and `TestBearerTenant` passed, including admin list without `token` and admin revoke of another user's token. `go test ./internal/secrets/` passed. `npm test` passed (166).
- Chromium on the collector origin, with a stored `wk_` key: `/` requested `GET /v1/analytics/summary?...&tenant=acme` with an empty `Authorization` and showed that summary (`4242` conversations). `/profile` created a token, showed the plaintext once, and the list table did not contain it. The create `POST /v1/tokens` sent no bearer.
- Starting with `WORKFLOW_SERVE_KEYS` set exited before listen, and the error names that variable. `docs/design/03-remote-service.md` has no `out of scope` and no `tenant=key` credential line.

artifact_feedback on the four phase 2 briefs and four reports: service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### Carried

1. Collector-mode `tenant` is still only on `/`. Other analytics routes omit it.
2. `Server.New` panics if the registry cannot be opened or persisted.
3. E2e global-setup seeds `registry.json` instead of logging in and calling `POST /v1/tokens`.
4. The profile expiry field is prefilled to three months in the browser. The device page must not copy that. The server still has no default.

## Phase 1 — GitHub login and admission

Refined into four sequential units, committed in `7dd001f`. Nothing runs in parallel: 1-01, then 1-02, then 1-03, then 1-04.

artifact_feedback on the four phase 1 briefs: quality service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### 1-01-registry-remote-config

- Built: `registry.json` under `WORKFLOW_SERVE_DATA` (policy, sessions, reserved owners and token hashes), `Local()` / `Remote()`, and `ConfigFromEnv` that refuses a non-empty `WORKFLOW_SERVE_KEYS`, ignores OAuth on loopback, and requires the OAuth trio plus a valid `WORKFLOW_PUBLIC_URL` on a non-loopback bind. `New` opens the registry when remote.
- Surfaces: `tools/workflow/internal/serve/registry.go`, `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/serve_test.go`, `tools/workflow/cmd/workflow/main_test.go`.
- Commit: `3191ce2`. `go test` on `internal/serve` and `cmd/workflow` passed (`TestServeOutcome` now covers OAuth refusal, keys refusal on loopback, and loopback local ingest).
- Deviations: the keys refusal lives in `ConfigFromEnv` only, not a second check in `runServe`. `New` panics if the registry cannot be opened or persisted. Tests for the registry landed in `serve_test.go` rather than a new `registry_test.go`. `main.go` was not edited.
- Agent: Composer, harness did not report turns or final context.

### 1-02-oauth-session-remote-auth

- Built: GitHub OAuth login, callback, and logout; `workflow_session` with a policy re-check; admin `PUT /v1/admin/policy`; `GET /v1/me`; remote `/v1` auth that treats ingest as bearer-only and leaves loopback on `localGuard`. Unknown bearers are `unauthorized` until phase 2 issues tokens.
- Surfaces: `tools/workflow/internal/serve/oauth.go`, `tools/workflow/internal/serve/session.go`, `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/serve_test.go`.
- Commit: `40b81f7`. `go test ./internal/serve/` passed, including `TestOAuthSessionRemoteAuth`, `TestRemoteSessionIngestAndTenant`, `TestRemotePolicyAdmin`, and `TestLoopbackUnchangedWithOAuthEnv`.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### 1-03-analytics-session-site

- Built: collector-origin fetches send the session cookie and no bearer; the overview appends `tenant` from `GET /v1/me`; `/login` exists, including the denied-admission message; a 403 `no such tenant` is not treated as a logged-out 401.
- Surfaces: `packages/workflow-analytics/src/lib/api.ts`, `packages/workflow-analytics/src/lib/api.test.ts`, `packages/workflow-analytics/src/routes/+layout.svelte`, `packages/workflow-analytics/src/routes/+page.svelte`, `packages/workflow-analytics/src/routes/login/+page.svelte`, `packages/workflow-analytics/tests/e2e/session.spec.ts`.
- Commit: `fd91d15`. `npm test` passed (163 tests). Playwright `--grep 'session|login'` did not run: e2e global-setup starts a keyed `workflow serve` with `WORKFLOW_SERVE_KEYS`, and that process now exits before listen.
- Deviations: none from the brief. Other analytics routes still omit `tenant` in collector mode.
- Agent: Composer, harness did not report turns or final context.

### 1-04-design-docs-login

- Built: `docs/design/05-distribution.md` and `docs/design/07-analytics-site.md` describe the collector GitHub session, `/login`, and `workflow_session`. They no longer say the dashboard has no user identity, and they no longer say `workflow login` is the way remote mode is opted into.
- Surfaces: `docs/design/05-distribution.md`, `docs/design/07-analytics-site.md`.
- Commit: `aa6dd93`. A search of those two files finds no `no user identity`, no `WORKFLOW_SERVE_KEYS=tenant`, and no `workflow login (not built yet)`.
- Deviations: none. The docs name bearer tokens as the client credential before phase 2 issues them.
- Agent: Composer, harness did not report turns or final context.

### Phase 1 verification

Outcome holds.

- A non-loopback `workflow serve` with the OAuth env set and `WORKFLOW_SERVE_KEYS` unset listened, wrote `registry.json`, and answered `GET /v1/analytics/summary` with 401 `sign in at https://collector.example/login`. The same bind with `WORKFLOW_SERVE_KEYS` set, a loopback bind with that variable set, and a non-loopback bind missing the OAuth env each exited 1 before the port accepted a connection. The keys error names `WORKFLOW_SERVE_KEYS`.
- Against the handler and a mock GitHub: a verified `codyh@ctzns.net` login set `workflow_session` (HttpOnly, SameSite=Lax, Secure) and redirected to `/`. The same admin still got a session when the allow list was `allowed.example`. A verified `x@denied.example` login redirected to `/login?error=denied` with no session cookie. `PUT /v1/admin/policy` to `allow_list` and back to `everyone` was 200 for the admin and 403 for a non-admin; `everyone` stored an empty domain list. After the list was tightened, the member's next summary was 401 and the cookie was cleared. The stranger's next login then landed on `/` with a session. A session with no owned tenant got 403 `{"error":"no such tenant"}`. `POST /v1/ingest` with no bearer, and with a session and no bearer, was 401 and left no `ledger.db`.
- The live binary's `/oauth/login` redirected to `https://github.com/login/oauth/authorize`. The binary has no mock GitHub base, so the cookie was checked on the handler, not against github.com.
- Loopback with the OAuth env set served `/` (200, built site) and `GET /v1/analytics/summary` (200) with no cookie. A bearer on that summary was ignored (200).
- Chromium on the collector origin, with `workflow-analytics-key` set to a `wk_` value: `/login` showed Sign in with GitHub; `/login?error=denied` showed the denial. With `/v1/me` returning no tenants and summary returning 403 `no such tenant`, the page said "You do not have a tenant yet" and did not offer the logged-out sign-in link. Every `/v1` request had an empty `Authorization` header.
- `npm test` in `packages/workflow-analytics`: 163 passed. `go test ./internal/serve/` passed. The first `go test ./cmd/workflow` failed because those servers still set `WORKFLOW_SERVE_KEYS` and exited before listen. `52dfcf0` starts them without that variable and expects tenant `local`. `main_test.go` still expects the refusal. After that commit, `go test ./cmd/workflow/` passed.
- `docs/design/05-distribution.md` and `docs/design/07-analytics-site.md` have no `no user identity`, no `WORKFLOW_SERVE_KEYS=tenant`, and no `workflow login (not built yet)`.

artifact_feedback on the four phase 1 briefs and four reports: service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### Carried

1. `packages/workflow-analytics` e2e global-setup still sets `WORKFLOW_SERVE_KEYS`, so the keyed server exits before listen and `tests/e2e/session.spec.ts` did not run.
2. Collector-mode `tenant` is appended on the overview only. Other analytics routes still omit it.
3. `Server.New` panics if the registry cannot be opened or persisted.
