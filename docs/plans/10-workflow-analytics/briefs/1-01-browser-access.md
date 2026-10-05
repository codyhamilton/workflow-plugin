# Brief: 1-01 — Browser access (CORS) on `workflow serve`

Consumer: a Sonnet worker dispatched by the plan 10 phase 1 orchestrator. Its middleware is what
the phase 2 site relies on to call `/v1` from the Vite dev server and from a Pages origin; 1-03
registers its routes behind it.
Owned paths: `tools/workflow/internal/serve/serve.go` (`Config`, `ConfigFromEnv`, `Handler`,
`localGuard`'s comment, and a new CORS middleware in that file),
`tools/workflow/internal/serve/serve_test.go`,
`docs/plans/10-workflow-analytics/reports/1-01-browser-access.md` (new). Touch nothing else; in
particular not `reads.go`, `internal/store/`, `go.mod`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/1-01-browser-access.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 1-02 (disjoint paths).
Budget: 5 files to read, about 180 lines to change including tests, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — "Domain: Analytics reads" contract paragraph and its env table (lines 49-60), and "#### Browser access" (lines 175-179). Binding.
2. `docs/plans/10-workflow-analytics/DESIGN.md` — Phase 1 Outcome (line 277), the CORS sentences.
3. `tools/workflow/internal/serve/serve.go` — `Config`, `ConfigFromEnv`, `loopbackHost` (lines 30-80); `Handler`, `localGuard`, `method` (lines 377-435).
4. `tools/workflow/internal/serve/serve_test.go` — `do`, `newServer` (lines 21-36), `TestLocalModeConfig`, `TestLocalModeHTTP` (lines 151-206).

Go is at `~/.local/go/bin` (add it to `PATH`). Run tests from `tools/workflow`. Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Let a browser on an allowed origin read `/v1` from `workflow serve`, and nothing else: loopback origins in local mode, an exact allowlist in keyed mode.

## Contract

Quoted from DESIGN.md "Browser access" (settled):

> - Local mode (no `WORKFLOW_SERVE_KEYS`): if the request `Origin` host is loopback (`localhost`, `127.0.0.1`, `::1`), the response includes `Access-Control-Allow-Origin` set to that exact origin, `Access-Control-Allow-Headers: Authorization, Content-Type`, `Access-Control-Allow-Methods: GET, OPTIONS`, and `Vary: Origin`. `OPTIONS` returns 204. Any other origin gets no CORS headers. [...] `localGuard` (loopback `Host`, JSON-only POST) stays as in design 3.
> - Keyed mode: the same CORS headers are sent only when `Origin` is listed exactly in `WORKFLOW_SERVE_CORS_ORIGINS` (comma-separated). Unset or empty means no CORS headers. No wildcard and no reflected arbitrary origin.
> - No cookies. [...] `Access-Control-Allow-Credentials` is not set.

Env table: `WORKFLOW_SERVE_CORS_ORIGINS` — "Comma-separated exact origins allowed to read a keyed server from a browser. Unset or empty: no CORS headers. Ignored in local mode, which uses the loopback-origin rule below."

Outcome sentences this unit makes true: "A `GET` and an `OPTIONS` from `Origin: http://127.0.0.1:<any port>` in local mode include that origin in `Access-Control-Allow-Origin`, and the `OPTIONS` returns 204. A `GET` from `Origin: https://evil.example` includes no CORS header. A keyed server sends those CORS headers only for an origin listed in `WORKFLOW_SERVE_CORS_ORIGINS`. `GET /v1/artifacts` and `GET /v1/health` keep their current shapes."

## Changes

- `Config` gains `CORSOrigins []string`. `ConfigFromEnv` reads `WORKFLOW_SERVE_CORS_ORIGINS`, splits on commas, trims spaces, drops empty entries. No further validation; it never errors.
- One middleware in `serve.go` wraps the mux for every path (the site also reads `/v1/checks` and `/v1/baselines`). Order in `Handler`: `localGuard` stays outermost in local mode, the CORS middleware inside it, the mux innermost.
- Origin allowed: local mode → `Origin` parses as a URL with scheme `http` or `https` and `loopbackHost(u.Hostname())`; keyed mode → the `Origin` string equals an entry of `CORSOrigins` exactly. No `Origin` header, or `Origin: null` → not allowed.
- Allowed origin: set the four headers above before the inner handler writes; `Vary: Origin` via `Header().Add`. A request with method `OPTIONS` is answered 204 with no body and never reaches `auth` (a preflight carries no `Authorization`).
- Not allowed: no `Access-Control-*` header, and the request reaches the mux unchanged — an `OPTIONS` there keeps today's answer (405 from `method`, or the JSON 404 for an unknown path).
- `POST /v1/ingest` stays closed to browsers: `Allow-Methods` names only `GET, OPTIONS`, so a preflight for a POST still fails in the browser. Update `localGuard`'s comment, which says the service never answers a preflight, to say it answers one only for GET.
- No `Access-Control-Allow-Credentials`, no `Access-Control-Max-Age`.

### Keep untouched

`localGuard`'s Host and JSON-POST checks, `auth`, `tenantFor`, every existing route and response body, and the existing tests (they pass unchanged).

## Done evidence

Write the failing tests first and report their output before and after. Why each matters: the loopback cases are what the phase 2 dev server needs; the evil-origin and keyed-mismatch cases are the guard that a public page cannot read a keyless loopback ledger; the 204-without-auth case is what lets a browser preflight succeed at all; the config test pins the env parsing the operator relies on.

- `go test ./internal/serve/ -run CORS -v` → passes, covering at least: local mode GET `/v1/health` with `Origin: http://127.0.0.1:5173` → `Access-Control-Allow-Origin: http://127.0.0.1:5173`, the allow-headers and allow-methods values above, `Vary: Origin`; local OPTIONS `/v1/artifacts` from `http://localhost:4000` → 204, those headers, empty body; local GET from `https://evil.example` → no `Access-Control-*` header; local `http://[::1]:9000` allowed; keyed mode with `CORSOrigins: ["https://wf.pages.dev"]` → that origin gets the headers on a keyed GET and 204 on an unkeyed OPTIONS, while `https://other.pages.dev` and `http://127.0.0.1:5173` get none; keyed mode with no `CORSOrigins` → none; `Access-Control-Allow-Credentials` never present.
- A config test shows `WORKFLOW_SERVE_CORS_ORIGINS=" https://a.example, ,https://b.example"` parses to exactly the two origins.
- `go vet ./... && go test ./...` from `tools/workflow` → all pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
