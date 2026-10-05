# Report: 1-01 Browser access (CORS) on `workflow serve`

Status: done.

## Done against the brief

- `Config.CORSOrigins` added; `ConfigFromEnv` reads `WORKFLOW_SERVE_CORS_ORIGINS` (split on commas, trimmed, empties dropped, never errors). Pinned by `TestCORSConfig`: `" https://a.example, ,https://b.example"` gives exactly the two origins.
- New `(*Server).cors` middleware in `tools/workflow/internal/serve/serve.go` wraps the mux for every path. `Handler` order: `localGuard` outermost (local mode), `cors`, mux.
- Allowed origin: local mode is scheme http/https plus loopback hostname; keyed mode is exact match against `CORSOrigins`; empty or `null` never allowed. Allowed responses carry `Access-Control-Allow-Origin` (the exact origin), `Allow-Headers: Authorization, Content-Type`, `Allow-Methods: GET, OPTIONS`, and `Vary: Origin`. An allowed `OPTIONS` returns 204 with no body and never reaches `auth`. Not-allowed requests reach the mux unchanged (an evil-origin `OPTIONS` still gets 405). No `Allow-Credentials`, no `Max-Age`.
- `localGuard` comment updated: it answers a preflight only for GET, so a POST preflight still fails.

## Evidence

- Before: `go test ./internal/serve/ -run CORS` failed to compile (`unknown field CORSOrigins`, `c.CORSOrigins undefined`).
- After: `TestCORSLocalMode`, `TestCORSKeyedMode`, `TestCORSConfig` all PASS. Covered: local GET `/v1/health` from `http://127.0.0.1:5173`; local OPTIONS `/v1/artifacts` from `http://localhost:4000` and `http://[::1]:9000` give 204 and empty body; `https://evil.example`, `null`, no Origin, `http://localhost.evil.example`, `ftp://127.0.0.1` get no `Access-Control-*`; keyed with `https://wf.pages.dev` gets headers on a keyed GET and 204 on an unkeyed OPTIONS, while `https://other.pages.dev`, a suffix-lookalike, `null` and `http://127.0.0.1:5173` get none; keyed with no `CORSOrigins` gets none; `Allow-Credentials` is asserted absent.
- `go vet ./...` and `go test ./...` from `tools/workflow`: all packages pass (including `internal/store` at the time of the run).

## Departures

- The keyed-mode GET test uses `/v1/checks` rather than `/v1/artifacts`: today's `/v1/artifacts` returns 400 without `repo_id` and `path`, which would not exercise the happy path. The middleware is path-agnostic, so coverage is the same. 1-03 changes `/v1/artifacts`; no action needed here.
- Contradictions between the brief and the cited contracts: none found.

## Unfinished and known problems

None.
