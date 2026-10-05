# Brief: 3-02 — Release build embeds the site; Pages output

Consumer: a worker dispatched by the plan 10 phase 3 orchestrator, after 3-01 is committed. The orchestrator verifies the phase outcome by running this unit's hosted spec against a `build.sh` binary.
Owned paths: `tools/release/build.sh`, `tools/release/test_release.py` (only `BuildTests` and the `env()` helper, as below), `packages/workflow-analytics/package.json` and `package-lock.json` (one dependency, below), new `packages/workflow-analytics/wrangler.toml`, new `packages/workflow-analytics/playwright.hosted.config.ts`, new `packages/workflow-analytics/tests/hosted/`. Plus `docs/plans/10-workflow-analytics/reports/3-02-release-build.md`. Touch nothing else — not `tools/workflow/` (3-01 owns the handler; a defect there is reported, not fixed), not `src/`, not `tests/e2e/`, not `svelte.config.js` or `vite.config.ts`, and never `bin/SHA256SUMS`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/3-02-release-build.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-01 (committed on this branch: `site/` placeholder, embedded handler).
Runs alongside: nothing.
Budget: 12 files to read, about 300 lines to write including the spec, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — "Domain: Hosting" (lines 189-196), Phase 3 Outcome (line 305), Assumption 5 (Pages project is an operator action). Binding.
2. `docs/plans/10-workflow-analytics/reports/3-01-serve-site.md` — routing and cache rules as built, how the placeholder is detected.
3. `tools/release/build.sh` (whole, 34 lines) and `tools/release/test_release.py` — `Base.env()` and `BuildTests.test_7_build_sh`.
4. `packages/workflow-analytics/package.json`, `svelte.config.js` (output `build/`, fallback `index.html`), `playwright.config.ts`.
5. `packages/workflow-analytics/tests/e2e/global-setup.ts`, `tests/e2e/fixture.ts` (by `grep -n export`), `tests/e2e/overview.spec.ts`, `tests/e2e/quality.spec.ts` (test ids) — the idioms to copy for the hosted spec.

Node/npm come from nvm (`command -v npm`); Go is at `~/.local/go/bin`. Read ranges and grep; do not read a whole file to find one section, and truncate long tool output.

## Goal

A release build always embeds the real site, so `workflow serve` on loopback hosts it at `/`; the same static build is declared as the Cloudflare Pages output.

## Contract

Quoted from DESIGN.md "Domain: Hosting":

- "The site build output is copied to `tools/workflow/internal/serve/site` before `go build` embeds it. `tools/release/build.sh` runs that site build first and fails if `index.html` is missing."
- "The package's static build is also the Cloudflare Pages artifact (Pages-compatible output directory declared in the package). Deploying a project and attaching a hostname is an operator action, not a step this change can perform."
- Phase 3 Outcome: "after `tools/release/build.sh`, `workflow serve` bound to loopback answers `GET /` with the built `index.html` (`Content-Type: text/html`, no placeholder marker) and `GET /v1/health` with the existing JSON. Loading `http://127.0.0.1:<port>/` in a browser shows the overview counts from the same origin with no token configured. A client-side route such as `/quality` refreshes to the quality view rather than a JSON 404. `GET /v1/not-a-route` stays JSON 404."

Decisions settled at refine (do not re-derive):

1. **build.sh order:** find `npm` (`command -v npm`, else exit 1 with `build.sh: no Node toolchain`); in `packages/workflow-analytics` run `npm ci` only when `node_modules/` is absent, then `npm run build`; fail (non-zero, message naming the path) if `build/index.html` is missing or still contains `workflow-analytics-placeholder`. Then replace the contents of `tools/workflow/internal/serve/site/` with the contents of `build/`, run the existing four `go build`s, and write sums as today.
2. **Tree stays clean:** a `trap … EXIT` restores `site/` to exactly the committed placeholder (save a copy of `site/index.html` to a temp dir before copying; on exit remove everything in `site/` and put it back), whether the build succeeded or failed. After any `build.sh` run, `git status --porcelain tools/workflow/internal/serve/site` is empty. Do not add a `.gitignore` inside `site/` (it would be embedded and served).
3. **test_release.py:** `test_7_build_sh` runs `build.sh` with `PATH` = Go + `/usr/bin:/bin`, so it no longer finds Node. Add the directory of the outer environment's `npm` (`shutil.which("npm")`) to that test's `PATH`, and pass through whatever npm needs to avoid a network install under the temp `HOME` (e.g. `npm_config_cache` from the real home) — only in `BuildTests`/`env()` extras. Add one assertion to `test_7`: `git status --porcelain tools/workflow/internal/serve/site` is empty after the run. The embedded site's content is proved by the hosted spec, not here.
4. **Pages output:** `packages/workflow-analytics/wrangler.toml` with `name = "workflow-analytics"` and `pages_build_output_dir = "./build"`. No account id, no routes, no secrets, no deploy script. The build has no `404.html`, so Pages treats it as a single-page app and serves `index.html` for client routes; keep it that way.
5. **Carried dependency (Phase 2 Carried item 3):** add `@perspective-dev/server` to `dependencies` at the same version as the installed `@perspective-dev/client` (`npm install @perspective-dev/server@^<that version>`), so `/explore` no longer resolves it only transitively. The lockfile change is limited to that.
6. **Hosted spec:** `npm run test:hosted` (new script) runs Playwright with `playwright.hosted.config.ts`. It requires `WORKFLOW_BIN` (absolute path to a binary built by `build.sh`; fail fast naming the variable when unset). Its global setup starts that binary with `serve` in local mode (`WORKFLOW_SERVE_ADDR=127.0.0.1:<free port>`, fresh `WORKFLOW_SERVE_DATA`, `WORKFLOW_CHECKS_DIR` = repo `tools/quality`, `TYPESAFE_API_KEY` empty), posts `FACTS` from `tests/e2e/fixture.ts`, waits until `/v1/health` `pending` is 0, and uses that serve as `baseURL`. No `vite preview`, no `localStorage` setup: the page uses its default same-origin `/v1`. Import from `tests/e2e/` but do not modify it.

### Keep untouched

`build.sh`'s `VERSION`/`COMMIT` ldflags, `OUT_DIR`/`SUMS_FILE` overrides, Go probing, and four-target matrix. The existing e2e suite (`npm run test:e2e`) and `playwright.config.ts`.

## Done evidence

Write the hosted spec first and run it against a binary from today's (placeholder) build to show it fails; report the output before and after. Why: these are the outcome's hosting clauses — a release binary carries the real site, client routes survive a refresh on the same origin, `/v1` stays JSON, and Pages gets the same build.

- `OUT_DIR=$T/dist SUMS_FILE=$T/SUMS bash tools/release/build.sh` (with `$T` a temp dir; never the default `SUMS_FILE`) → exit 0, four binaries; then `git status --porcelain tools/workflow/internal/serve/site bin` → empty.
- With `build/` removed and `npm run build` made to fail (e.g. `PATH` without npm), `build.sh` exits non-zero and `site/` is still the placeholder.
- `WORKFLOW_BIN=$T/dist/workflow-linux-<arch> npm run test:hosted` → passes, with at least:
  - `GET /` → 200, `content-type` starts with `text/html`, body lacks `workflow-analytics-placeholder`, `cache-control: no-cache`; `GET /v1/health` → 200 JSON with its existing keys; `GET /v1/not-a-route` → 404 JSON `{"error":"not found"}`;
  - `page.goto('/')` with empty `localStorage` shows the fixture's overview numbers (`summary-*` test ids, `SUMMARY_ALL`), and every `/v1/` request the page made went to the serve's own origin with no `authorization` header;
  - `page.goto('/quality')` then `page.reload()` shows the quality view (its `quality-kind-*` buttons and `q-row` rows), not JSON;
  - a `/_app/immutable/` asset fetched by the page has `cache-control: public, max-age=31536000, immutable`;
  - `/explore` renders `perspective-viewer` with `explore-count` equal to the fixture's explore row count (WASM loads from the binary).
- `npm run test:e2e` → still passes (26/26 or more). `python3 -m unittest tools.release.test_release.BuildTests -v` from the repo root → passes.
- `wrangler.toml` exists with `pages_build_output_dir = "./build"`, and `npm run build` writes `build/index.html` there.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence (including in 3-01's handler or phase 1/2 code): report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
