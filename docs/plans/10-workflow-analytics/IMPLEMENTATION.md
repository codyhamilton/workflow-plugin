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
