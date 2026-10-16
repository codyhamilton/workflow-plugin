# Implementation

- Tool: Cursor
- Session: 93e8d765-46ab-4867-b484-c51b2ec7f579
- Start: 2026-10-16T12:21:49Z
- Branch: plan/14-analytics-ui

## Phase 1 — Solarized shell

### 1-01-solarized-shell

- Built: solarized light and dark tokens, a system/light/dark control stored at `workflow-analytics-theme`, `data-theme` on the document root, chart refresh when that attribute changes, and stylesheet hexes replaced with those tokens. Shell padding and control gaps use the 4/8/16/24/32 scale.
- Surfaces: the files in commit `fb401e4`.
- Deviations: `+layout.svelte` sets `data-theme` from an inline script before hydration, because `app.html` was outside the owned paths and a late effect left the light tokens up through first paint.
- Agent: Composer, agent `6a48cb2a-3ab9-4b1f-ae15-459428a689e3`. The harness did not report turn count or final context size. Status `done`, commit `fb401e4`.

### Verification

Checked against the phase outcome, not the report.

- A scan of `<style>` blocks under `packages/workflow-analytics/src/**/*.svelte` found no hex color.
- `theme.css` and `DEFAULT_TOKENS` (series via `LIGHT_SERIES`) contain only the theme contract's hex values. The series list matches the contract order.
- Shell `padding` and `gap` use `--space-1` through `--space-5`, defined as 4px, 8px, 16px, 24px, and 32px.
- `npm test -- src/lib/charts/theme.test.ts` in `packages/workflow-analytics`: 7 passed.
- `npx playwright test tests/e2e/shell.spec.ts`: 13 passed. With no stored key and dark mode, `/` and `/settings` compute `--bg` `#002b36`, `--text` `#839496`, and the series list. Choosing Light sets `--bg` `#fdf6e3` and `--text` `#657b83` without a reload, and a reload keeps it. Choosing System, then switching the emulated scheme to dark, sets `--bg` to `#002b36`.

### Feedback

`artifact_feedback` on `docs/plans/14-analytics-ui/reports/1-01-solarized-shell.md` and `docs/plans/14-analytics-ui/briefs/1-01-solarized-shell.md` returned not delivered. Nothing is queued for either file.

### Carried

None.

## Phase 2 — Distribution, score series, and run aggregates

Refined in `1773214` into six units. Refine agent `d742ac97-355e-4334-8c57-c8076a6ee14b` returned Proceed. `artifact_feedback` on the six briefs was not delivered; nothing was queued.

### 2-01-distribution-read

- Built: `GET /v1/analytics/distribution` — call and conversation grain, optional `model` dimension, fixed bins, top-N without `__other__`, unpriced cost excluded from percentiles and bins.
- Surfaces: `tools/workflow/internal/store/distribution.go`, `distribution_test.go`, `percentile.go`; `tools/workflow/internal/serve/analytics_distribution.go`, `analytics_distribution_test.go`, `serve.go`, `analytics_bench_test.go`. Commit `f66b9db`.
- Deviations: the serve shape test sees `rows: []` on `queryFixture` because that fixture has no usage facts. Store tests cover the populated cases.
- Agent: Composer, agent `9b0236d1-8c6a-41bb-bd43-323df3157d3d`. The harness did not report turn count or final context size. Status `done`.
- Check: `go test ./internal/store/ -run TestDistribution -count=1` and `go test ./internal/serve/ -run 'TestDistribution|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow`, both ok.

### 2-05-conversation-window

- Built: `GET /v1/analytics/conversation` keeps the full event list, `totals` covers the whole run past the event cap, and `window_totals` is present only when `from` or `to` is set. `from` after `to` is 400 `{"error":"from after to"}`.
- Surfaces: `tools/workflow/internal/store/conversation.go`, `conversation_test.go`; `tools/workflow/internal/serve/analytics_conversation.go`, `analytics_conversation_test.go`, `analytics_bench_test.go`. Commit `0d836e5`.
- Deviations: none.
- Agent: Composer, agent `fb7bdfd1-c41d-466a-aa61-912a7a547d43`. The harness did not report turn count or final context size. Status `done`.
- Check: `go test ./internal/store/ -run TestConversation -count=1` and `go test ./internal/serve/ -run TestConversation -count=1` from `tools/workflow`, both ok.

### 2-02-score-series-read

- Built: `GET /v1/analytics/score-series`. A bucket uses the latest score of a content hash inside that bucket. A bucket with no scores is omitted.
- Surfaces: `tools/workflow/internal/store/score_series.go`, `score_series_test.go`; `tools/workflow/internal/serve/analytics_score_series.go`, `analytics_score_series_test.go`, `serve.go`, `analytics_bench_test.go`. Commit `5d340d9`.
- Deviations: none.
- Agent: Composer, agent `181d15dd-ad7a-4dd1-88ff-50483e632968`. The harness did not report turn count or final context size. Status `done`.
- Check: `go test ./internal/store/ -run TestScoreSeries -count=1` and `go test ./internal/serve/ -run 'TestScoreSeries|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow`, both ok.

### 2-03-executions-shape-series

- Built: repeatable `shape` filters executions rows and the cursor only. `counts` stay the window totals. Optional `bucket` adds `series` with keys `complete`, `unreported`, `started` in that order.
- Surfaces: `tools/workflow/internal/store/analytics.go`, `analytics_test.go`; `tools/workflow/internal/serve/analytics.go`, `analytics_test.go`, `analytics_bench_test.go`. Commit `8fd0807`.
- Deviations: none.
- Agent: Composer, agent `0c5692ac-6817-4c4f-9e17-0c7e5f7a69e1`. The harness did not report turn count or final context size. Status `done`.
- Check: `go test ./internal/store/ -run 'TestAnalyticsExecutions|TestExecutionsPage|TestExecutions.*Series' -count=1` and `go test ./internal/serve/ -run 'TestExecutions|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow`, both ok.

### 2-04-conversations-usage-fields

- Built: conversation list rows include `model`, `model_calls`, `unpriced_calls`, `cost_usd`, `tokens_in`, and `tokens_out`. `model` is the most frequent in-window call model, ties to the smaller name.
- Surfaces: `tools/workflow/internal/store/analytics.go`, `analytics_test.go`; `tools/workflow/internal/serve/analytics.go`, `analytics_test.go`. Commit `dfe6722`.
- Deviations: none.
- Agent: Composer, agent `758fa3ca-e1d6-400f-b777-25715ccf47e6`. The harness did not report turn count or final context size. Status `done`.
- Check: `go test ./internal/store/ -run 'TestAnalyticsConversations|TestConversationsPage' -count=1` and `go test ./internal/serve/ -run 'TestAnalytics.*Conversation|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow`, both ok.

### 2-06-analytics-site-reads-doc

- Built: `docs/design/07-analytics-site.md` states `GET /v1/analytics/distribution`, `GET /v1/analytics/score-series`, executions `shape` and `series`, conversation-list usage fields, and conversation `window_totals`. It states that existing `/query` fields are unchanged, and the same for `/schema`, `/summary`, `/series`, `/scores`, and `/baselines`.
- Surfaces: `docs/design/07-analytics-site.md`. Commit `c0e120f`.
- Deviations: none.
- Agent: Composer, agent `203856de-1428-4702-9425-9e69f07075cd`. The harness did not report turn count or final context size. Status `done`.

### Verification

Checked against the phase outcome, not the reports.

- `go test ./internal/serve/ -run TestAnalyticsBenchSmoke -count=1` from `tools/workflow` passed. The smoke cases include `distribution/cost`, `distribution/tokens`, `score-series/`, `executions/shape`, `executions/shape-bucket`, `conversations/`, and `conversation/` with `from` and `to`. The smoke route list requires a `distribution` case and a `score-series` case.
- Store and serve tests named in each unit's done evidence were re-run and passed, as recorded on the units above.
- `docs/design/07-analytics-site.md` contains the distribution and score-series routes, `window_totals`, and the sentence that existing `/query` fields are unchanged.

### Feedback

`artifact_feedback` on the six phase-2 briefs and the six phase-2 reports returned not delivered. Nothing is queued for any of them.

### Carried

- `docs/design/07-analytics-site.md` open issue 12 still says conversation totals cover only the returned events when a timeline is truncated. The new contract on that same page says `totals` is the whole run and `truncated` applies to `events` only. The next edit of that file should replace the stale clause.

## Phase 3 — Model and volume reports

Refined in `1a39fdf` into eight units. Refine agent `7b649bbb-44a8-4ff8-b39c-d8fa60faca15` returned Proceed. `artifact_feedback` was not called: the workflow feedback namespace was not available in that session. Nothing is queued for the eight briefs.

The Phase 2 carried item is not a Phase 3 surface. It stays for the Phase 5 edit of `docs/design/07-analytics-site.md`.

### 3-01-filter-bar-ten-dims

- Built: the filter bar lists all ten shared dimensions. Conversation exclude is called out as unsupported.
- Surfaces: `packages/workflow-analytics/src/lib/components/FilterBar.svelte`, `packages/workflow-analytics/tests/e2e/filter-bar.spec.ts`. Commit `6a19e68`.
- Deviations: `mapFacets` was already mapping the missing dimensions, so `view.svelte.ts` was not edited.
- Agent: Composer, agent `2577f7a0-db11-4436-be7a-f352a4f14777`. The harness did not report turn count or final context size. Status `done`.

### 3-02-overview-kpi-links

- Built: overview KPI tiles link to the owning reports and keep the query string. Trends links set `metric`.
- Surfaces: `packages/workflow-analytics/src/routes/+page.svelte`, `packages/workflow-analytics/tests/e2e/overview.spec.ts`. Commit `0edf140`.
- Deviations: the existing `overview shows the fixture numbers` check fails with `unpriced_calls` 1 against fixture 2, with this unit's diff stashed as well. Sparkline `pointer-events` were set to `none` so the tile link receives the click.
- Agent: Composer, agent `10650bf9-beff-468d-9c36-199661c50379`. The harness did not report turn count or final context size. Status `done`.

### 3-03-time-chart-interactions

- Built: `TimeChart` takes optional `filterDim` and `onseries`. Series and legend clicks drill, including shift to exclude. Brush is unchanged.
- Surfaces: `packages/workflow-analytics/src/lib/charts/TimeChart.svelte`, `docs/plans/14-analytics-ui/reports/3-03-time-chart-interactions.md`. Commit `7863bbe`.
- Deviations: none.
- Agent: Composer, agent `7de7ac2e-d375-4b0f-a70b-190e613f450f`. The harness did not report turn count or final context size. Status `done`.

### 3-06-repos-cost-rank

- Built: `/repos` can rank by `cost_usd`. The default rank stays `hook_events`. A repo click filters.
- Surfaces: `packages/workflow-analytics/src/routes/repos/+page.svelte`, `packages/workflow-analytics/tests/e2e/repos.spec.ts`. Commit `23e98ba`.
- Deviations: the cost e2e compares live API values rather than the hand-counted `USAGE_ALL.cost_usd` constant, because per-repo totals use read-time pricing.
- Agent: Composer, agent `7137a2a7-1e34-4735-8ab5-8190d62c979a`. The harness did not report turn count or final context size. Status `done`.

### 3-08-builder-scalar-heatmap

- Built: zero dimensions with bucket `none` shows the scalar. Heatmap cells drill a filter dimension. Weekday and hour cells do not.
- Surfaces: builder route, `builder.ts`, `BuilderChart.svelte`, `Heatmap.svelte`, `packages/workflow-analytics/tests/e2e/builder.spec.ts`. Commit `279d0bd`.
- Deviations: none.
- Agent: Composer, agent `2233c0bc-b93b-48a3-bd4b-2bb3da7d0c8f`. The harness did not report turn count or final context size. Status `done`.

### 3-04-trends-stacked-drill

- Built: `/trends` drills a grouped series through `TimeChart`, and a control switches the multi-key split to a stacked area. The chart choice is in the URL.
- Surfaces: `packages/workflow-analytics/src/routes/trends/+page.svelte`, `packages/workflow-analytics/tests/e2e/trends.spec.ts`. Commit `b3d0898`.
- Deviations: the e2e drill clicks ECharts SVG paths because the brush layer blocks legend hits. The fixture series that drills is qwen.
- Agent: Composer, agent `91b452c4-e44a-47d2-8e97-bdfc2d69da5b`. The harness did not report turn count or final context size. Status `done`.

### 3-05-usage-distribution

- Built: `/usage` shows cost and token totals by model, a cost time series and a token time series split by model, and a per-call histogram for `cost_usd` and each token measure in the distribution contract. Model click and shift-click filter. Brush sets the window.
- Surfaces: `packages/workflow-analytics/src/routes/usage/+page.svelte`, `packages/workflow-analytics/src/lib/types.ts`, `packages/workflow-analytics/src/lib/charts/DistributionChart.svelte`, `distribution.ts`, `distribution.test.ts`, `packages/workflow-analytics/tests/e2e/usage.spec.ts`. Commit `84c4ae0`.
- Deviations: the histogram control lists the six contract measures. The brief said seven. Usage e2e sets `timezoneId: 'UTC'`. Three existing usage tests still fail because `claude-opus-5-5` is priced in the store while the e2e fixture still expects it unpriced. `tests/e2e/fixture.ts` was outside this unit's paths.
- Agent: Composer, agent `50c36eaf-4724-476c-a667-701590b6a8f0`. The harness did not report turn count or final context size. Status `done`.

### 3-07-hooks-timeseries

- Built: `/hooks` draws `GET /v1/analytics/query` with `measure=hook_events`, a time bucket, and a dimension of `norm_event` or `tool`. Brush sets the window. A treemap leaf still drills.
- Surfaces: `packages/workflow-analytics/src/routes/hooks/+page.svelte`, `packages/workflow-analytics/tests/e2e/hooks.spec.ts`. Commit `f973e59`.
- Deviations: the brief's Playwright `-g "fixture counts"` matches no test title. The static bar fixture test still runs in the full spec.
- Agent: Composer, agent `6732f0c0-1a98-4e2a-bf2d-d1563932e1a6`. The harness did not report turn count or final context size. Status `done`.

### Verification

Checked against the phase outcome, not the reports. From `packages/workflow-analytics`.

- `npm test -- src/lib/charts/distribution.test.ts src/lib/charts/options.test.ts src/lib/builder.test.ts`: 41 passed.
- `E2E_PORT=4401 npx playwright test` on `filter-bar.spec.ts`, `overview.spec.ts`, `trends.spec.ts`, `usage.spec.ts`, `repos.spec.ts`, `hooks.spec.ts`, and `builder.spec.ts`: 66 passed, 5 failed.
- Passing cases cover the outcome: the filter bar exposes all ten dimensions; overview KPI tiles keep `repo_id` and the trends tile sets `metric`; `/trends` series click filters and shift-click excludes, and stacked area lists series columns; `/repos` cost ranking orders the bars and a repo click filters; `/hooks` requests `measure=hook_events` with a time bucket and split dim, brush narrows the window, and a treemap leaf drills; `/usage` switches the distribution measure, requests tokens over time with `dim=model`, brush sets `from`/`to`, and a model bar click filters; the builder shows a scalar for zero dimensions with bucket `none`, and a model heatmap cell adds a chip while weekday and hour cells do not.
- The five failures are the existing unpriced-opus expectations: overview `unpriced_calls` is 1 not 2 and cost is `$0.16, 1 unpriced` not `$0.02, 2 unpriced`; usage expects `claude-opus-5-5` to read `unpriced` and receives `$0.13`. Those assertions are not the phase outcome.

### Feedback

`artifact_feedback` was not called on the eight briefs or eight reports. The workflow feedback namespace is not available in this session. Nothing is queued.

### Carried

- `docs/design/07-analytics-site.md` open issue 12 still says conversation totals cover only the returned events when a timeline is truncated. The contract on that page says `totals` is the whole run and `truncated` applies to `events` only. Phase 5 edits that file and should replace the stale clause.
- Overview and usage e2e still expect `claude-opus-5-5` to be unpriced (`unpriced_calls` 2, cost `$0.02, 2 unpriced`, opus cost `unpriced`). The API prices that model, so the page shows 1 unpriced call and `$0.13` for opus. The next edit of `tests/e2e/fixture.ts` or those specs should match the priced fixture.

## Phase 4 — Quality and runs

Refined in `c809570` into six units. Refine agent `82a4ce38-8c57-4f4d-9b55-97613c94d3ea` returned Proceed. `artifact_feedback` was not called: the workflow feedback namespace is not loaded in this session. Nothing is queued for the six briefs.

The design 7 open-issue-12 carried item stays for Phase 5. The priced-opus e2e mismatch is unit 4-06.

### 4-01-quality-score-series

- Built: `/quality` fetches score series per kind, draws a median line and a p25–p75 band per check with points, draws the all-time baseline median, leaves a gap where a bucket has no point, keeps the box plot, reloads both when kind changes, and brush sets the custom window.
- Surfaces: `packages/workflow-analytics/src/routes/quality/+page.svelte`, `types.ts`, `params.ts`, `ScoreBandChart.svelte`, `score-series.ts`, `score-series.test.ts`, `tests/e2e/quality.spec.ts`. Commit `7404a65`.
- Deviations: quality e2e sets `timezoneId: 'UTC'`. The kind-refetch test waits for the score-series request.
- Agent: Composer, agent `2ebfdc9a-73d0-4fe8-a8b6-b1d581b7d610`. The harness did not report turn count or final context size. Status `done`.

### 4-05-explore-usage-columns

- Built: the Explore table columns include `model`, `cost_usd`, and `norm_event`.
- Surfaces: `packages/workflow-analytics/src/routes/explore/+page.svelte`, `tests/e2e/explore.spec.ts`. Commit `de59898`.
- Deviations: none.
- Agent: Composer, agent `7f8d8580-a5be-4fd0-8fca-34586d038e4e`. The harness did not report turn count or final context size. Status `done`.

### 4-06-e2e-pricing-fixture

- Built: e2e expectations match priced `claude-opus-5-5` (`$0.13` per call, one unpriced qwen call).
- Surfaces: `tests/e2e/fixture.ts`, `overview.spec.ts`, `usage.spec.ts`, `interactions.spec.ts`. Commit `1b94b7a`.
- Deviations: unpriced-only cases filter qwen with `model=` because Opus under `harness=claude` is priced. Interactions repos fan-out expects five queries. The `$0` guard is limited to the usage table so histogram bin labels do not fail it.
- Agent: Composer, agent `f01d08db-d85f-4d48-a2f4-090615e94a2f`. The harness did not report turn count or final context size. Status `done`.
