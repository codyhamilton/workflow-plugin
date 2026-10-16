# Client registration implementation

Tool: Cursor (Grok 4.7 orchestrator).
Run identity: https://cursor.com/agents/bc-3f650f40-1066-5daa-b196-4a4ab11ffc43
Started: 2026-10-16T11:35:03Z
Branch: `cursor/client-registration-3d44`
Starting HEAD: `33f90be`

Phase 1 only. Later phases are not started.

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
