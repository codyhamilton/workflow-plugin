# Implementation — 10 workflow analytics

Run identity: Claude Code headless background job `6d6a67ca` (Opus 5.5 orchestrator), worktree branch `worktree-analytics-phase1`, started 2026-10-05T15:28Z from master @ 95f41f7. Refine commit 77d8701.

## Phase 1 — Analytics reads

Units: 1-01 and 1-02 dispatched in parallel (Sonnet), then 1-03 (Sonnet).

Refine feedback (artifact_feedback, all delivered, screen pass): `b.ac_why` below p25 on all three briefs and `b.goal_is_outcome` at p25 on 1-02 → addressed before commit (a why line in each Done evidence, 1-02 goal restated as an outcome).

### 1-01-browser-access — done (3ce9ae2)

- Built: `Config.CORSOrigins` from `WORKFLOW_SERVE_CORS_ORIGINS`; `(*Server).cors` middleware (localGuard → cors → mux); loopback-origin rule in local mode, exact allowlist in keyed mode; allowed OPTIONS → 204 before auth; no credentials/max-age. Tests `TestCORSLocalMode`, `TestCORSKeyedMode`, `TestCORSConfig`.
- Surfaces: `internal/serve/serve.go`, `internal/serve/serve_test.go`, `reports/1-01-browser-access.md`.
- Deviations: keyed-GET test uses `/v1/checks` rather than `/v1/artifacts` (the latter needs `repo_id`/`path` to return 200); middleware is path-independent.
- Agent: Sonnet, 21 tool uses, ~56k tokens, 2.5 min.

### 1-02-store-analytics — done with concerns (f139e02)

- Built: `store/analytics.go` with the brief's API unchanged (`Facets`, `Summary`, `Series`, `WindowScores`, `Executions`, `Conversations`, `Explore`), `wf_kind`/`wf_plan` SQLite functions; migration 3 `facts_ts` index; seven `TestAnalytics*` tests over a hand-counted fixture.
- Surfaces: `internal/store/analytics.go`, `internal/store/analytics_test.go`, `internal/store/store.go`, `reports/1-02-store-analytics.md`.
- Deviations: migration 3 is `CREATE INDEX IF NOT EXISTS` — `TestAdvisoryReads/backfill` resets `user_version` to 1 and re-runs later migrations. Explore tie-break: `row_hash` for facts, `rej-<20-digit id>` for rejections.
- Concerns: `Facets` applies the whole filter it is given; `Conversations` aggregates in Go and `Executions` uses a per-brief correlated `EXISTS` — neither measured on a large tenant.
- Brief amendment: 1-03 decision 10 (facets called with the window only, per the contract's "in the window").
- Agent: Sonnet, 21 tool uses, ~99k tokens, 5.8 min.

### 1-03-analytics-routes — done with concerns (0932914)

- Built: `serve/analytics.go` (shared filter parser, seven handlers, base64url cursor, `exploreCap`), seven registrations in `Handler`; `TestAnalyticsOutcome` (fixture via `POST /v1/ingest`, 9 subtests) and `TestAnalyticsEmptyTenant`.
- Surfaces: `internal/serve/analytics.go`, `internal/serve/analytics_test.go`, `internal/serve/serve.go`, `reports/1-03-analytics-routes.md`.
- Deviations: scores fixture uses a local `qaScorer` (catalog-named checks) since `contentScorer` files under `q.a`, absent from the catalog; nested brief paths are not executions (store lists `briefs/<stem>.md` only) and count under summary `other`.
- Concerns: paging slices the store's full sorted set in Go (no offset in the store API); facets `plans` includes `""`. Both follow the contract; noted for phase 2.
- Agent: Sonnet, 24 tool uses, ~112k tokens, 5.8 min.
- Orchestrator follow-up: `gofmt -w` on 1-02's two store files (c19262f, formatting only).

### Verification

Cheap-tier check by the orchestrator, against the Phase 1 Outcome:

- `go vet ./... && go test ./...` in `tools/workflow`: all packages ok; `gofmt -l .` clean after c19262f.
- Live: built `workflow serve`, ran it in local mode on `127.0.0.1:18765` with a fresh data dir, posted a 7-fact fixture (2 repos, 2 harnesses, 3 conversations, one precheck-rejected hook event) through `POST /v1/ingest`, then asserted over HTTP — 22/22 pass: summary counts (hook_events 2, artifact_versions 3, commits 1, conversations 2, precheck 1, by_kind brief 2/report 1, screens settling to unscreened 3); executions shapes complete/started, a `limit=1` two-page walk equal to the one-page result with `next` absent on the last page, `cursor mismatch` on a changed `repo_id`; facets, series (hook_events/day/tool), scores, conversations, explore all 200; explore 7 rows `truncated:false`; `kind required`; `range too wide`; `Origin: http://127.0.0.1:5173` GET and OPTIONS (204, empty body) carry the origin and no credentials header; `Origin: https://evil.example` gets no `Access-Control-*`; `/v1/health` and `/v1/artifacts` keep their shapes; `/v1/analytics/nope` JSON 404. Keyed-mode CORS and `truncated:true` are covered by `TestCORSKeyedMode` and `TestAnalyticsOutcome`.
- Result: phase outcome holds.

Feedback (artifact_feedback): reports 1-01 and 1-03 delivered, screen pass, no check below p25. Report 1-02: not delivered (the service has no version and nothing queued; the worker's write did not reach the hook) — recorded, not rewritten. Brief 1-03 (amended, v3): delivered, nothing below p25. Briefs 1-01/1-02: see refine feedback above.

### Carried

1. Executions and conversations paging loads the full sorted set from the store and slices in Go; `Conversations` aggregates in Go and `Executions` uses a per-brief correlated `EXISTS`. Unmeasured at scale — measure on a large tenant before relying on it remotely.
2. `/facets` `plans` (and `repos`/`harnesses`/`events`) include `""`; phase 2's filter controls decide whether to hide or label the empty value.
3. Report `reports/1-02-store-analytics.md` never reached the feedback service; re-deliver it (touch through the hook) if its scores are wanted.

## Phase 2 — Report views

Run identity: Claude Code headless background job `1cc7d595` (Opus 5.5 orchestrator), worktree branch `worktree-analytics-phase-2`, started 2026-10-06 from master @ c931ae5. Refine commit 66c47de.

Units: 2-01, then 2-02, 2-03, 2-04 one at a time (shared e2e build dir and ports). Sonnet workers.

Refine feedback (artifact_feedback, all four delivered, screen pass): `b.ac_why` below p25 on 2-02 → addressed before commit (per-check why lines; re-scored 0.64). Nothing else below p25.

### 2-01-site-shell — done with concerns (8e761df)

- Built: `packages/workflow-analytics` (Svelte 5.57 / Kit 2.70 / adapter-static 3, SPA fallback `index.html`, output `build/`); `src/lib/{api,filters,types,format}.ts`, `FilterBar.svelte` (empty facet values hidden — carried item 2), layout with nav and error panel, overview `/`, `/settings`; `scripts/check-bundle.mjs`; Playwright harness (local + keyed `workflow serve` seeded with `tests/e2e/fixture.ts`, vite preview). Deps for the whole phase installed (layerchart 2.5.1, @perspective-dev/* 5.5.1, @playwright/test 1.63.0).
- Checks: `npm test` 7 pass; `npm run test:e2e` 6 pass; `check:bundle` ok and fails on a planted string.
- Deviations: build + bundle check run inside the Playwright `webServer` command (`scripts/e2e-build.mjs`) because webServer starts before globalSetup; global setup clears `TYPESAFE_API_KEY` so the fixture never reaches the live screening service; vitest limited to `src/**/*.test.ts`.
- Concern (phase-1 store, not fixed): `rejWhere` in `tools/workflow/internal/store/analytics.go` (~line 114) matches rejection rows' `repo_id`/`harness` against the filter, and precheck rejection rows carry empty values, so any `repo_id`/`harness` filter drops rejections to 0.
- Agent: Sonnet, 62 tool uses, ~114k tokens, 6.7 min.

### 2-02-chart-reports — done (844a6ef)

- Built: `/trends` (metric/bucket/group controls limited to the contract's pairings), `/repos` (per-repo summaries in parallel), `/hooks` (event/tool/harness from grouped series) with LayerChart wrappers in `src/lib/charts/`; specs `trends`, `repos`, `hooks` (7 tests).
- Checks: the 7 specs failed first, then pass; whole e2e suite 13/13; build + `check:bundle` ok.
- Deviations: series are sparse, so a filtered-out day has no cell (spec asserts absence, not `0`); `by_kind` test ids are `repo-<repo>-by_kind-<kind>`.
- Open: chart rendering not visually checked (specs read the tables); `svelte-check` not installed.
- Agent: Sonnet, 26 tool uses, ~81k tokens, 3.9 min.

### 2-03-table-reports — done (2d8f783)

- Built: `Pager.svelte` (in-memory cursor, same params plus `cursor`, hidden without `next`, stale responses dropped on filter change); `/quality` (first valid `kind`, default `design`, multi-kind note, kind buttons; scores and `/v1/baselines?kind=` in parallel, GET only; window and all-time baseline columns, blank baseline cells when absent); `/executions` (three count tiles, `exec-row` table, Pager); `/conversations` (`conv-row` table, `conv-<id>-<field>` counts, Pager); `limit` URL param passed through. Specs `quality`, `executions`, `conversations` (9 tests).
- Checks: the 9 specs failed first, then pass; whole e2e suite 22/22; build ok; `check:bundle` passed inside the e2e webServer command.
- Deviations: no chart on `/quality` (optional per brief); the stubbed quality spec adds `access-control-allow-origin: *` to fulfilled responses (cross-origin page and serve); table rows keyed by index (no unique field).
- Agent: Sonnet, 20 tool uses, ~73k tokens, 3.3 min.

### 2-04-explore — done with concerns (1d083ab)

- Built: `/explore` dynamically imports Perspective client, viewer, datagrid and theme on mount (WASM via `?url`), builds a 14-column table (`ts` datetime, rest string), `table.replace` on filter change; `explore-count`, and an `explore-truncated` banner only when `truncated`. Spec `explore` (4 tests: 17 rows unfiltered, `repo_id=r1` → 12 surviving reload, stubbed `truncated:true` banner, `/` requests no Perspective or `.wasm`).
- Checks: 3 of 4 failed first (the no-Perspective-on-`/` test passes trivially), then 4 pass; whole e2e suite 26/26; build ok; `check:bundle` ok (79 files).
- Deviations: none; `vite.config.ts` unchanged.
- Concerns: `@perspective-dev/server` is imported by path but only resolves transitively through `@perspective-dev/client` (not in `package.json`); the `r1` count of 12 reflects the `rejWhere` quirk 2-01 reported.
- Agent: Sonnet, 17 tool uses, ~60k tokens, 2.5 min.

### Verification

Cheap-tier check by the orchestrator, against the Phase 2 Outcome, from `packages/workflow-analytics`:

- `npm test`: 7/7. `npm run test:e2e` (whole suite, which builds and runs `check:bundle` with the live tenant key and token as `E2E_FORBIDDEN` before previewing `build/`): 26/26, covering `/`, `/trends`, `/repos`, `/hooks`, `/quality`, `/executions`, `/conversations`, `/explore` against local and keyed phase-1 serves seeded with the fixture, URL filters surviving reload, `/quality` window beside `/v1/baselines` with GET-only requests, `/explore` Perspective plus `truncated`, `/settings` localStorage keys and bearer header.
- `npm run build`: emits `build/index.html` and `build/_app/` (HTML/JS/CSS). Perspective appears in one route node chunk only; LayerChart is imported only through `src/lib/charts/` by the fixed routes.
- Result: phase outcome holds.

Feedback (artifact_feedback): not run — the `workflow` MCP server failed to connect in this session (ENOENT on its binary), so reports 2-01..2-04 and the four briefs were not scored at close, and Phase 1 carried item 3 (re-deliver report 1-02) was not done. Refine-time brief feedback is recorded above.

### Carried

1. `rejWhere` in `tools/workflow/internal/store/analytics.go` (~line 114) matches precheck rejection rows' empty `repo_id`/`harness` against the filter, so any `repo_id` or `harness` filter drops rejections to 0 (summary `precheck`, explore rows). Phase-1 store bug; needs a contract decision on whether rejections belong to a repo.
2. Executions and conversations paging loads the store's full sorted set and slices in Go (Phase 1 carried item 1). Unmeasured at scale; the site's Pager follows the cursor unchanged.
3. `@perspective-dev/server` is used by `/explore` but not declared in `package.json`; add it as a direct dependency.
4. Chart rendering is not visually checked (specs read the tables); `svelte-check` is not installed.
5. `artifact_feedback` for phase 2 reports and briefs, and report 1-02's re-delivery, are outstanding because the feedback server was unreachable.

## Phase 3 — Local serve hosts the site

Run identity: Claude Code headless background job `88c3a6c8` (Opus 5.5 orchestrator), worktree branch `worktree-wa-phase3`, started 2026-10-06 from master @ 5178686. Refine commit b13ae9f.

Units: 3-01, then 3-02 (sequential). Sonnet workers.

Refine feedback (artifact_feedback): brief 3-01 delivered, screen pass, no check below p25. Brief 3-02 delivered, awaiting screen at refine time.

### 3-01-serve-site — done (a09e962)

- Built: `serve/site.go` (`//go:embed all:site`, `siteHandler(fs.FS)`, package var `siteFS` as the test seam); catch-all `/` in `Handler` is now the site handler behind `cors`/`localGuard`; placeholder `site/index.html`; `site_test.go` (5 tests: placeholder, missing index, built FS in local and keyed mode, real embedded placeholder via `Handler()`, localGuard 403).
- Surfaces: `internal/serve/site.go`, `internal/serve/site_test.go`, `internal/serve/site/index.html`, `internal/serve/serve.go` (one line), `reports/3-01-serve-site.md`.
- Checks: tests failed to build first (`undefined: siteFS`), then pass; `go vet`, `go test ./...`, `gofmt -l` clean.
- Deviations: none. Note: in local mode a non-JSON `POST /` is 415 from `localGuard` before the site's 405.
- Agent: Sonnet, 14 tool uses, ~54k tokens, 3.7 min.

### 3-02-release-build — done (06f17bc)

- Built: `build.sh` finds `npm` (else `build.sh: no Node toolchain`), `npm ci` only without `node_modules/`, `npm run build`, fails on missing or placeholder `build/index.html`, copies `build/` into `site/` before the four `go build`s, `trap … EXIT` restores the placeholder; `test_7_build_sh` gets npm on `PATH` plus `npm_config_cache` and asserts a clean `site/`; `wrangler.toml` (`pages_build_output_dir = "./build"`); `@perspective-dev/server@^5.5.1` declared (Phase 2 Carried item 3); `test:hosted` script, `playwright.hosted.config.ts`, `tests/hosted/` (global setup + 6 tests).
- Surfaces: `tools/release/build.sh`, `tools/release/test_release.py`, `packages/workflow-analytics/{package.json,package-lock.json,wrangler.toml,playwright.hosted.config.ts,tests/hosted/}`, `reports/3-02-release-build.md`.
- Checks: hosted spec against a placeholder binary 5 fail / 1 pass, then 6/6 against `build.sh`'s `workflow-linux-amd64`; `test:e2e` 26/26; `BuildTests` ok; stub-failing `npm` → `build.sh` exit 1 with `site/` still the placeholder.
- Deviations: failure path tested with a stub `npm` (host has `/usr/bin/npm`), so the `no Node toolchain` branch is unexercised; hosted `baseURL` set via `test.use` from `HOSTED_BASE`. Worker rewrote `bin/SHA256SUMS` once while probing and restored it (not committed).
- Agent: Sonnet, 43 tool uses, ~86k tokens, 4.0 min.
