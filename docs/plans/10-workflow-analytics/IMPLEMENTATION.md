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
