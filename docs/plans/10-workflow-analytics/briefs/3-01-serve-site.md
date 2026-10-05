# Brief: 3-01 — Serve the embedded site

Consumer: a worker dispatched by the plan 10 phase 3 orchestrator. Unit 3-02 builds the real bundle on top of this handler; the orchestrator verifies the phase outcome against both.
Owned paths: `tools/workflow/internal/serve/site/` (new: the placeholder `index.html` only), a new `tools/workflow/internal/serve/site.go`, `tools/workflow/internal/serve/site_test.go`, and in `tools/workflow/internal/serve/serve.go` only the `Handler` function's catch-all `/` registration. Plus `docs/plans/10-workflow-analytics/reports/3-01-serve-site.md`. Touch nothing else — not `tools/release/`, not `packages/`, not the `/v1` handlers, `cors`, `localGuard`, `auth`, or `method`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/3-01-serve-site.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing (phases 1 and 2 are on this branch).
Runs alongside: nothing (3-02 needs this handler to verify its build).
Budget: 6 files to read, about 250 lines to write including tests, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — "Domain: Hosting" (lines 189-196) and the Phase 3 Outcome (line 305). Binding. "Browser access" (175-179) for the CORS and `localGuard` behavior that must keep wrapping the new handler.
2. `tools/workflow/internal/serve/serve.go` — `Handler` (line ~387), `cors` (~415), `localGuard` (~450), `writeJSON` (~471), `method` (~477).
3. `tools/workflow/internal/serve/serve_test.go` — by `grep -n "^func Test\|httptest\|newTestServer\|func new"` first, for how tests build a `Server` and call `Handler()`.

Go is at `~/.local/go/bin`. Run Go commands from `tools/workflow`. Read ranges and grep; do not read a whole file to find one section, and truncate long tool output.

## Goal

`workflow serve` hosts the analytics site at `/` from files embedded in the binary, without ever answering a `/v1` path with HTML, and keeps a placeholder-only build (no Node) answering a JSON 404.

## Contract

Quoted from DESIGN.md "Domain: Hosting":

- "The site build output is copied to `tools/workflow/internal/serve/site` before `go build` embeds it. … A placeholder `index.html` in that directory contains the exact marker `workflow-analytics-placeholder`. While that marker is present, `GET /` and other non-file routes stay 404 `{"error":"analytics bundle not embedded"}`, so `go test` does not need Node."
- "When the marker is absent, `workflow serve` serves the embedded files at `/`. Unknown paths that do not start with `/v1/` return `index.html` (client-side routes). `/v1/*` is never HTML. `index.html` is `Cache-Control: no-cache`. Files under the Vite asset directory are `Cache-Control: public, max-age=31536000, immutable`."
- Analytics reads: "Unknown routes under `/v1/` stay JSON 404. Error body stays `{"error":"<text>"}`."

Decisions settled at refine (do not re-derive):

1. **Embed:** `//go:embed all:site` in `site.go`. The `all:` prefix is required: SvelteKit's output lives under `_app/`, and a plain pattern skips files starting with `_` or `.`.
2. **Testable seam:** the site handler is built from an `fs.FS` argument (rooted at the site directory, e.g. via `fs.Sub`), so tests drive both modes with `testing/fstest.MapFS` and no Node. `Handler()` passes the embedded FS by default; tests may override it through an unexported field or package variable. No change to `Config`, `New`, or any exported signature.
3. **Mode:** decided once when the handler is built: the site is "not embedded" when `index.html` is missing or contains the bytes `workflow-analytics-placeholder`.
4. **Routing** (replaces today's catch-all `/` that answers `{"error":"not found"}`):
   - A path equal to `/v1` or starting with `/v1/` that no `/v1` route matched → JSON 404 `{"error":"not found"}`, exactly as today, in both modes.
   - Not embedded: every other path → JSON 404 `{"error":"analytics bundle not embedded"}`.
   - Embedded: only `GET` and `HEAD`; any other method → JSON 405 `{"error":"method not allowed"}` with `Allow: GET, HEAD`. A path naming an existing regular file in the FS is served with its type from the extension (`http.ServeContent` or `http.FileServer`-equivalent; `.wasm` must be `application/wasm`, `.js` a JavaScript type). `/`, `/index.html`, and any path that is not an existing file (including directories) → `index.html`'s bytes, `200`, `Content-Type: text/html; charset=utf-8`. Do not let `http.FileServer` redirect `/index.html` → `/` or list directories.
   - `Cache-Control`: `no-cache` on every `index.html` response (including fallbacks); `public, max-age=31536000, immutable` on files under `_app/immutable/` (SvelteKit's hashed Vite asset directory); no `Cache-Control` set on other files (e.g. `_app/version.json`, `favicon`).
5. **Wrapping:** the site handler sits behind the existing `cors` and, in local mode, `localGuard`, exactly as the catch-all does now. Keyed mode serves the site without auth (static files carry no tenant data; data reads stay behind `auth`).
6. **Placeholder file:** `site/index.html` is a minimal HTML page whose text contains `workflow-analytics-placeholder` and one sentence saying the analytics bundle is built by `tools/release/build.sh`. It is the only committed file in `site/`.

### Keep untouched

Every `/v1` registration and its middleware order; `cors`, `localGuard`, `auth`, `method`, `writeJSON`. Existing tests must pass unchanged.

## Done evidence

Write the failing tests first and report their output before and after. Why: these are the outcome's routing clauses — the site never shadows `/v1`, client routes survive a refresh, and a placeholder build cannot pretend to host the site.

- `go test ./internal/serve/ -run 'Site' -v` → passes, with at least (via `httptest` against the handler built from a `fstest.MapFS`, and through `Server.Handler()` for the embedded placeholder):
  - placeholder FS (and the real embedded `site/`): `GET /` and `GET /quality` → 404, `Content-Type: application/json`, body `{"error":"analytics bundle not embedded"}`; `GET /v1/not-a-route` → 404 `{"error":"not found"}`; `GET /v1/health` → 200 JSON.
  - built FS (`index.html` without the marker, `_app/immutable/x.js`, `_app/version.json`, `p.wasm`): `GET /` → 200 `text/html`, body is that `index.html`, `Cache-Control: no-cache`; `GET /quality` and `GET /quality/` → same body and headers; `GET /_app/immutable/x.js` → 200, JavaScript type, `Cache-Control: public, max-age=31536000, immutable`; `GET /_app/version.json` → 200 with no `Cache-Control`; `GET /p.wasm` → `application/wasm`; `GET /v1/not-a-route` and `GET /v1` → 404 JSON `{"error":"not found"}`, never `text/html`; `POST /` → 405 JSON; `HEAD /` → 200 with no body.
  - local mode through `Handler()` with the built FS: a request whose `Host` is not loopback still gets 403 from `localGuard`.
- `go vet ./... && go test ./... && gofmt -l .` in `tools/workflow` → all ok, `gofmt` prints nothing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
