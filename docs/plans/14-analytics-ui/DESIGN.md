# Analytics UI

## Intent

User request, verbatim:

> /design improvements to the analytics UI. it's extremely basic at the moment, needing:
> - Cleaner style, make it minimalistic but clean, well spaced and modern. Go with a solarized inspired theme (light/dark modes)
> - All charts and reports should be interactive where reasonable, with drill down and time window selection, dynamic filtering
> - Have separate subagents look at each of the pages and dashboards and reimagine them. We want to be able to compare model against model, trend changes and visualise distributions using appropriate graph types, it should be rich and interactive

## Problem

The analytics site is a flat link bar, a generic gray palette, and a set of reports that only partly do what [design 7](../../design/07-analytics-site.md) already describes. A person can filter and, on some bars, drill. They cannot reliably compare models, see a measure move, or read a distribution, and several charts ignore clicks and brushes that the neighbouring page already implements.

What is on screen today:

- Theme tokens are neutral grays and a blue accent. Dark mode follows the system scheme only. Overview tiles and the quality table hard-code their own grays. Type is `system-ui` with tight, inconsistent spacing.
- Overview's KPI tiles and its weekday×hour heatmap do not drill, and the tiles do not link anywhere. Trends is a multi-series line with brush and no series click, and no stacked comparison. Usage is a model table, a cost bar, a stacked cost series, and one aggregate token series, with no brush and no spread. Repos is hook-event volume for the top repos. Hooks are six static count panels. Quality is a five-number box per check against an all-time median, with a kind switch and nothing else. The executions sankey filters the loaded page in the browser, so the table trails the funnel. The conversation list has no model and no cost. One conversation is a text scroller of the whole run, and the shell hides the window control there. Explore's table omits `model`, `cost_usd`, and `norm_event` even though the API returns them. The builder's heatmap does not drill, and zero dimensions with no bucket draws an empty chart.
- Dashboards are iframes of saved URLs (`embed=1`), each a full copy of a page.

The read API cannot answer the rest. `GET /v1/analytics/query` returns sums. `GET /v1/analytics/scores` returns one window-level percentile row per check, not a series. Executions expose window totals and a paged list, with no `shape` parameter and no time buckets. Conversation rows have no usage fields. Per-call cost and tokens are not summarized as a distribution. There is no latency column on the ledger, and this design does not add one.

This is the gap the request names. Plan 12 already shipped the shell, the filters, and ECharts. The work here is the presentation, the missing interactions, and the read aggregates those views need.

## Solution Shape

The site stays one static SvelteKit app on the current tree, served as it is today. It gains a solarized light and dark theme with an explicit override, one spacing and type scale, and report interactions that match the data: drill on a real filter value, brush on a time axis, and the existing URL filter set surfaced in the filter bar. Model comparison, trend, and distribution views are first-class on the reports that own those questions. The new numbers come from read-time aggregates on the existing ledger, under the same tenant auth as the other analytics GETs. No ingest, no new tables, no second chart library.

Dashboards stop being iframes. A saved view is a chart configuration. A dashboard is an ordered grid of those configurations, rendered as components in the same document, under the one filter bar and window in the dashboard URL.

### Domain: Theme

- Owns: the color, type, and space tokens, and the theme override.
- Contract:
  - Storage key `workflow-analytics-theme` in `localStorage`. Values: `system`, `light`, `dark`. An absent key means `system`.
  - The document root carries `data-theme="light"` or `data-theme="dark"`. `system` resolves through `prefers-color-scheme` and follows later OS changes. `light` and `dark` do not.
  - Charts read computed tokens. They do not hard-code a color.
  - Light surfaces: background `#fdf6e3`, surface `#eee8d5`, text `#657b83`, muted `#586e75`, border `#93a1a1`. Dark surfaces: background `#002b36`, surface `#073642`, text `#839496`, muted `#93a1a1`, border `#586e75`. Both modes: accent `#268bd2`, danger `#dc322f`.
  - Series order, both modes: `#268bd2`, `#859900`, `#b58900`, `#cb4b16`, `#dc322f`, `#d33682`, `#6c71c4`, `#2aa198`.
  - Body type stays `system-ui`. The space scale is 4, 8, 16, 24, 32. The shell uses it for its own padding and its control gaps. A route's own section gap is outside this contract.
  - A notice, warning, or error uses `danger`, `surface`, `text`, and `border`. It does not add a hex.
- Non-goals: a downloaded font, a per-page palette, a third theme, a new color token.

### Domain: Report interaction

- Owns: the URL as the filter and window state, drill, brush, and the filter bar.
- Contract:
  - Shared filter keys stay `repo_id`, `harness`, `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`. The filter bar offers every one of them. Exclude stays the facet complement. Exclude on `conversation_id` stays unsupported and labelled so.
  - Window presets stay Today, 24h, 7d, 30d, 90d, This month, YTD, All time, plus a custom range. Brush on a time axis sets the custom range. `/conversation` shows that window control. Dimension filters are not sent to `GET /v1/analytics/conversation`.
  - Clicking a mark whose key is a shared filter value includes it. Shift-click excludes it. `__other__` and the empty key are not clickable. `hour_of_day`, `weekday`, and check names are not filters.
  - `shape` is an executions page parameter (`complete`, `unreported`, `started`), not a shared filter. Other reports do not send it.
  - Each overview KPI links to the report that owns the measure, keeping the current query string. The link sets `measure` only when the target is `/trends`: `artifact_versions`, `distinct_content`, or `commits`, one per tile. Conversations → `/conversations`. Hook events → `/hooks`. Model calls, tokens, cost, and unpriced calls → `/usage`.
  - The site zero-fills a gap only on count series (`/query` measures whose unit is a count, and the executions shape series). A score series leaves the gap.
- Non-goals: server-side exclude, `hour_of_day` and `weekday` as URL filters, a prior-window delta on the KPI tiles, linking overview counts to `/explore`.

### Domain: Analytics reads

- Owns: the new and extended analytics GETs. Tenant resolution and error shape are unchanged from design 7. The shared filter keys are unchanged.
- Contract:
  - **`GET /v1/analytics/distribution`**. `measure` is required and is one of `cost_usd`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`. An unknown measure is 400 `{"error":"unknown measure <m>"}`. `grain` is `call` (default) or `conversation`. An unknown grain is 400 `{"error":"unknown grain <g>"}`. `dim` is omitted or `model`. Any other dimension is 400 `{"error":"unsupported dimension <d> for <measure>"}`.
    - Call grain: one value per model call in the window, the same call identity `model_calls` uses. Conversation grain: one value per conversation, the sum of that measure over its calls. The conversation's `model` is the most frequent model on those calls, ties broken to the smaller name, `""` when it has none. That is the same rule the conversation list uses.
    - For `cost_usd`, `n` is priced calls, `unpriced` is the rest, and percentiles and bins use priced calls only. For a token measure, `unpriced` is 0 and every call is in `n` and in the bins.
    - `repo_id`, `harness`, `model`, and `conversation_id` apply. `kind`, `plan`, `norm_event`, `event`, `tool`, and `source` are ignored and listed in `ignored_filters`.
    - Response: `{"measure","grain","dim","rows":[{"k","n","unpriced","min","p25","median","p75","p95","max","bins":[{"lo","hi","n"}]}],"truncated"?,"ignored_filters"?}`. `k` is the model, or `"all"` when `dim` is omitted. `top` defaults to 20, maximum 100, and orders rows by `n` descending. There is no `__other__` row. `truncated` is true when keys were dropped.
    - Percentiles use the `/scores` method: sorted values, position `(n-1)*q`, linear interpolation. Cost is rounded to 6 decimal places. Token measures are rounded to 1 decimal place.
    - Bin edges are fixed, so models share an axis. Tokens: a zero bin; then `[2^i, 2^(i+1))` for `i` from 0 through 19; then overflow at `2^20`. Cost: a zero bin; a bin for `(0, 10^-4)`; then `[10^i, 10^(i+1))` for `i` from -4 through 1; then overflow at `100`. `lo` is inclusive, `hi` exclusive, except the overflow bin which has no `hi`.
    - The read scans existing columns. It does not read the hourly rollup and it does not emit `partial`. Wider than 400 days is 400 `{"error":"range too wide"}`. The site clamps All time to 399 days and says so.
  - **`GET /v1/analytics/score-series`**. `kind` is required and is exactly one of `design`, `brief`, `report`. `bucket` is required and is `day`, `week`, or `month`. Wider than 400 days, or more than 400 buckets, is 400 `{"error":"range too wide"}`.
    - `t` is the bucket start, RFC3339 in `tz`. `week` starts Monday and `month` starts on the first, both in `tz`. The same `t` rule applies to the executions `series`.
    - A point's population is the distinct content hashes with a version timestamp in that bucket. Several versions of one hash in the bucket contribute the latest. A hash can appear in more than one bucket. This does not sum to `GET /v1/analytics/scores`, which is the latest score per hash over the whole window. The page does not present them as the same population.
    - Response: `{"kind","bucket","checks":[{"name","points":[{"t","n","p25","median","p75"}]}]}`. Points are sparse. Checks with no points are omitted. Percentiles use the `/scores` method, rounded to 3 decimal places. The route does not emit `partial`. The quality chart leaves a gap where a bucket has no point.
  - **`GET /v1/analytics/executions`**. Accepts repeatable `shape` (`complete`, `unreported`, `started`; anything else 400 `{"error":"unknown shape <s>"}`). Repeatable values are OR'd. No `shape` means all rows. `shape` filters `rows` and the cursor only. `counts` stays the three window totals with `shape` ignored. Other filters apply to both. An optional `bucket` of `day`, `week`, or `month` adds `series` of exactly three objects, `key` `complete`, `unreported`, `started`, in that order, each with sparse `points` of `{"t","n"}`. `shape` does not change `series`. The cursor binds `shape` and `bucket` the same way it already binds the other filters.
  - **`GET /v1/analytics/conversations`**. Each row gains `model`, `model_calls`, `unpriced_calls`, `cost_usd`, `tokens_in`, `tokens_out`. `model` uses the most-frequent rule above, over in-window calls. Counts are in-window. Order stays `last_ts` desc, `conversation_id` asc.
  - **`GET /v1/analytics/conversation`**. Optional `from` and `to`, RFC3339, inclusive. `from` after `to` is 400 `{"error":"from after to"}`. `events` stays the whole run in time order, capped at 5,000. `from` and `to` do not drop events. `totals` is the whole conversation, including events past the cap. `truncated` applies to `events` only. When `from` or `to` is present, `window_totals` is that range's full totals, not the capped slice. When both are omitted, `window_totals` is absent.
  - Existing fields on existing routes stay. `/query`, `/schema`, `/summary`, `/series`, `/scores`, and `/baselines` are not redefined.
  - `go test` of `TestAnalyticsBenchSmoke` covers the new routes and the new executions parameters with status 200 on the synthetic fixture. The env-gated benchmark (`WORKFLOW_BENCH_DIR`, bound p95 under 500 ms) includes the same cases. It stays skipped when the variable is unset.
- Non-goals: histograms of arbitrary measures, a distribution dimension other than `model`, statistical tests, a latency measure, raw per-call dumps beyond `/explore`, an additive rollup table, ingest or compaction changes, `all=1` on the new routes, `partial` on the new routes.

### Domain: Dashboards

- Owns: saved report configurations and the dashboard grid, in the browser only.
- Contract:
  - Storage prefix stays `workflow-analytics-views`.
  - A view is `{"id","name","report","params"}`. `report` is one of `overview`, `trends`, `usage`, `repos`, `hooks`, `quality`, `executions`, `conversations`, `explore`, `builder`. `params` holds that report's chart controls only (`measure`, `dim`, `bucket`, `chart`, `top`, `kind`, `metric`, `group`, `grain`). It does not hold the window or the shared filters.
  - A dashboard is `{"id","name","tiles":[{"viewId","w"}]}`. The grid is two columns and `w` is the column span, `1` or `2`. At most 12 tiles. Add refuses a tile past 12. Import keeps the first 12 tiles of each dashboard, drops the rest, and states how many tiles were dropped.
  - The dashboard page renders each tile as a component in the same document. There is no iframe and no `embed=1`. Every tile uses the dashboard URL's window and shared filters. Changing that window updates every tile.
  - Export and import are JSON of these objects. A stored URL becomes a view when its path is a known report. Known chart keys are copied into `params`. Window and filter keys on that URL are not copied. A stored entry whose path is not a known report is dropped, and the page states how many were dropped.
  - The single-number builder case (no dimension, bucket `none`) renders the scalar. It is a valid saved view.
- Non-goals: a server-side view store, a per-tile window, a second filter bar inside a tile, pinning a filter into a saved view, `embed=1`.

## Architectural Implications

- Design 7's site section changes where this plan says so: the theme is no longer system-only, dashboards are no longer framed `embed=1` pages, executions gain `shape` and `bucket`, and the new reads exist. Overview counts link as in the interaction contract, not to `/explore`. The empty key, `__other__`, `hour_of_day`, `weekday`, and check names are not clickable. Zero-fill applies to count series only. Phase 2 writes the read contracts into `docs/design/07-analytics-site.md`. Phase 5 writes the theme, the dashboard pivot, and these three site-section exceptions. Until those edits land, this design is the authority for the delta.
- The binary and the embedded site stay at `tools/workflow`. Plan 13 (`docs/plans/13-monorepo-restructure/`) moves that tree and rebases onto this work. This design does not wait for it and does not name `packages/workflow`.
- Aggregation stays in SQLite at read time. The distribution and score series are not additive, so they do not extend the hourly rollup and they do not report `partial`. They scan the existing columns inside the 400-day cap. An uncompacted ledger does not make these two routes partial.
- The URL remains the way one report is shared. A dashboard share is the dashboard URL plus the local configs, which do not travel with the URL. That is the same locality design 7 already accepted for saved views, with the saved payload changed from a URL to a config.
- ECharts remains the only chart grammar. Perspective remains only on Explore. Box plots, histograms, bands, and stacked series are ECharts types the site already depends on.

## Decisions

- **Reads, not a site-only reskin.** The distribution route, the score series, the executions shape filter and shape series, and the conversation-list usage fields are in scope. Ingest is not. Decided in the design session. `window_totals` on one conversation is an agent decision, recorded in PROVENANCE, so a window on that page has a denominator the event cap cannot fake.
- **Current tree.** Surfaces are `packages/workflow-analytics` and `tools/workflow`. Plan 13 rebases. Decided in the design session.
- **Dashboards are in-document components under one window.** The session rejected iframes, then chose one filter bar and one window for every tile. A saved view stores the chart only. There is no `embed=1`.
- **No second chart grammar.** Design 7 already forbids it, and the chart types these reports need are in ECharts.
- **No `__other__` on a distribution.** A folded bucket has no honest percentile.
- **Heatmap cells do not filter.** Weekday and hour are not filter keys.
- **Phase 1 owns every stylesheet color.** The phase outcome forbids a hex color in a stylesheet outside `theme.css` and `theme.ts`. The surfaces are every file that sets one today. The outcome is not narrowed to a subset of pages. A test stub is not a stylesheet color.
- **`totals` on one conversation is the whole run.** The event cap truncates the list, not the totals.

## Assumption Ledger

None — see PROVENANCE.md.

## Open Questions

None.

## Phases

Ordered. The count is fixed at sign-off. This design does not skip refine: phases 2 through 5 each cross more than one surface. A one-unit phase is briefed inline by execute. Each bullet of an outcome is required.

### Phase 1 — Solarized shell

One unit. Execute briefs it inline. The change is the same token replacement in every file that sets a color.

- Outcome: With no stored theme and the OS in dark mode, `/` and `/settings` use background `#002b36` and text `#839496`, and every chart series color is taken from the series list above. Choosing Light in the shell switches `/` to background `#fdf6e3` and text `#657b83` without a reload, and a reload keeps Light. Choosing System follows a later OS change. A scan of `<style>` blocks in `packages/workflow-analytics/src/**/*.svelte` finds no hex color. `theme.css` and `DEFAULT_TOKENS` in `theme.ts` use only the theme contract's hex values. A `*.test.ts` file may stub a computed color with another hex. The shell's own padding and its control gaps are multiples of the space scale.
- Surfaces: `packages/workflow-analytics/src/lib/theme.css`; `packages/workflow-analytics/src/lib/charts/theme.ts`; `packages/workflow-analytics/src/lib/charts/theme.test.ts`; the chart components `BarChart.svelte`, `BoxChart.svelte`, `BuilderChart.svelte`, `DataTable.svelte`, `GroupedBar.svelte`, `Heatmap.svelte`, `SankeyChart.svelte`, `SmallMultiples.svelte`, `TimeChart.svelte`, and `Treemap.svelte` in that same directory; `packages/workflow-analytics/src/lib/components/FilterBar.svelte`; `packages/workflow-analytics/src/routes/+layout.svelte`, `+page.svelte`, `settings/+page.svelte`, `quality/+page.svelte`, `builder/+page.svelte`, `conversation/+page.svelte`, `conversations/+page.svelte`, `executions/+page.svelte`, `explore/+page.svelte`, and `repos/+page.svelte`; `packages/workflow-analytics/tests/e2e/`.
- Approach: known
- Depends on: nothing

### Phase 2 — Distribution, score series, and run aggregates

- Units:
  - **2-01-distribution-read** — `briefs/2-01-distribution-read.md`. Depends on: nothing. Runs alongside: 2-05-conversation-window.
  - **2-02-score-series-read** — `briefs/2-02-score-series-read.md`. Depends on: 2-01-distribution-read. Runs alongside: nothing.
  - **2-03-executions-shape-series** — `briefs/2-03-executions-shape-series.md`. Depends on: 2-02-score-series-read. Runs alongside: nothing.
  - **2-04-conversations-usage-fields** — `briefs/2-04-conversations-usage-fields.md`. Depends on: 2-03-executions-shape-series. Runs alongside: nothing.
  - **2-05-conversation-window** — `briefs/2-05-conversation-window.md`. Depends on: nothing. Runs alongside: 2-01-distribution-read (coordinate `analytics_bench_test.go` if both touch it in one wave).
  - **2-06-analytics-site-reads-doc** — `briefs/2-06-analytics-site-reads-doc.md`. Depends on: 2-01 through 2-05. Runs alongside: nothing.
- Outcome:
  - `TestAnalyticsBenchSmoke` returns 200 for `GET /v1/analytics/distribution`, `GET /v1/analytics/score-series`, `GET /v1/analytics/executions` with `shape` and `bucket`, `GET /v1/analytics/conversations`, and `GET /v1/analytics/conversation` with `from` and `to`, on the synthetic fixture.
  - A distribution fixture shows a cost row whose `n` excludes an unpriced call, whose `unpriced` counts it, and whose bins and percentiles ignore it; a token row whose `unpriced` is 0; two models sharing the fixed cost edges; a dropped key setting `truncated` with no `__other__` row.
  - A score-series fixture shows a bucket using the latest version of a hash inside that bucket, and a missing bucket omitted rather than sent as a zero.
  - An executions fixture shows `shape=complete` narrowing `rows` and leaving `counts` unchanged, and `series` always three keys in the order `complete`, `unreported`, `started`.
  - A conversations fixture shows a row's `model` equal to the most-frequent rule.
  - A conversation fixture shows `totals` equal to the uncapped run when `events` is truncated, `window_totals` equal to the requested range, `events` still containing an event outside that range, and no `window_totals` field when `from` and `to` are omitted.
  - `docs/design/07-analytics-site.md` states these routes and states that existing `/query` fields are unchanged.
- Surfaces: `tools/workflow/internal/serve/` (analytics handlers and `analytics_bench_test.go`), `tools/workflow/internal/store/` (analytics, query, and usage reads), `docs/design/07-analytics-site.md`.
- Approach: known
- Depends on: nothing

### Phase 3 — Model and volume reports

- Units:
  - **3-01-filter-bar-ten-dims** — `briefs/3-01-filter-bar-ten-dims.md`. Depends on: nothing. Runs alongside: 3-02, 3-03, 3-06, 3-08.
  - **3-02-overview-kpi-links** — `briefs/3-02-overview-kpi-links.md`. Depends on: nothing. Runs alongside: 3-01, 3-03, 3-06, 3-08.
  - **3-03-time-chart-interactions** — `briefs/3-03-time-chart-interactions.md`. Depends on: nothing. Runs alongside: 3-01, 3-02, 3-06, 3-08.
  - **3-04-trends-stacked-drill** — `briefs/3-04-trends-stacked-drill.md`. Depends on: 3-03-time-chart-interactions. Runs alongside: 3-05, 3-07.
  - **3-05-usage-distribution** — `briefs/3-05-usage-distribution.md`. Depends on: 3-03-time-chart-interactions. Runs alongside: 3-04, 3-07.
  - **3-06-repos-cost-rank** — `briefs/3-06-repos-cost-rank.md`. Depends on: nothing. Runs alongside: 3-01, 3-02, 3-03, 3-08.
  - **3-07-hooks-timeseries** — `briefs/3-07-hooks-timeseries.md`. Depends on: 3-03-time-chart-interactions. Runs alongside: 3-04, 3-05.
  - **3-08-builder-scalar-heatmap** — `briefs/3-08-builder-scalar-heatmap.md`. Depends on: nothing. Runs alongside: 3-01, 3-02, 3-03, 3-06.
- Outcome:
  - On `/usage`, with the seeded e2e window, the page shows cost and token totals by model, a time series of cost split by model, and a time series of tokens split by model. A control draws the per-call histogram for `cost_usd` and for each token measure in the distribution contract, on that measure's bin edges. Clicking a model filters every panel to it. Shift-click excludes it. Brushing either time series sets the window in the URL and every panel follows.
  - On `/trends`, clicking a series key sets that dimension as a filter. A control draws a multi-key split as a stacked area.
  - On `/repos`, a control ranks the repos by `cost_usd`. A repo click filters.
  - On `/hooks`, the time series is `GET /v1/analytics/query` with `measure=hook_events`, a time bucket, and one dimension of `norm_event` or `tool`. Brush sets the window. A treemap leaf still drills.
  - On `/`, each KPI link lands on the report named in the interaction contract, with the query string kept, and the trends links set the measure named there.
  - The filter bar lists all ten shared dimensions.
  - The builder heatmap drills a filter dimension. Zero dimensions with bucket `none` shows the scalar.
- Surfaces: `packages/workflow-analytics/src/routes/+page.svelte`, `trends/+page.svelte`, `usage/+page.svelte`, `repos/+page.svelte`, `hooks/+page.svelte`, `builder/+page.svelte`, `packages/workflow-analytics/src/lib/components/FilterBar.svelte`, `packages/workflow-analytics/src/lib/charts/`, `packages/workflow-analytics/src/lib/query.ts`, `packages/workflow-analytics/tests/e2e/`.
- Approach: known
- Depends on: Phase 1, Phase 2

### Phase 4 — Quality and runs

- Units:
  - **4-01-quality-score-series** — `briefs/4-01-quality-score-series.md`. Depends on: nothing. Runs alongside: 4-05-explore-usage-columns, 4-06-e2e-pricing-fixture.
  - **4-02-executions-shape-series** — `briefs/4-02-executions-shape-series.md`. Depends on: 4-01-quality-score-series. Runs alongside: 4-03-conversations-cost-distribution, 4-04-conversation-window-timeline.
  - **4-03-conversations-cost-distribution** — `briefs/4-03-conversations-cost-distribution.md`. Depends on: 4-01-quality-score-series. Runs alongside: 4-02-executions-shape-series, 4-04-conversation-window-timeline.
  - **4-04-conversation-window-timeline** — `briefs/4-04-conversation-window-timeline.md`. Depends on: 4-01-quality-score-series. Runs alongside: 4-02-executions-shape-series, 4-03-conversations-cost-distribution.
  - **4-05-explore-usage-columns** — `briefs/4-05-explore-usage-columns.md`. Depends on: nothing. Runs alongside: 4-01-quality-score-series, 4-06-e2e-pricing-fixture.
  - **4-06-e2e-pricing-fixture** — `briefs/4-06-e2e-pricing-fixture.md`. Depends on: nothing. Runs alongside: 4-01-quality-score-series, 4-05-explore-usage-columns.
- Outcome:
  - On `/quality`, for one kind, each check with points shows a median line and a p25–p75 band over the window, and the all-time baseline median is drawn on that panel. A bucket with no point is a gap, not a zero. The box plot against the baseline remains. Switching kind reloads both. Brushing the band sets the custom window in the URL and the panel follows.
  - On `/executions`, clicking a sankey edge sets `shape` in the URL. The next page of rows matches that shape. The funnel counts stay the window totals. A stacked series of the three shapes over the window is on the page. Brushing that series sets the window and the series follows.
  - On `/conversations`, each loaded row shows model and cost, a model click filters, and the page shows the distribution of per-conversation cost for the window.
  - On `/conversation`, the window control is visible. Events inside `from`/`to` are marked, events outside that range stay listed, and `window_totals` are shown beside `totals`.
  - On `/explore`, the table columns include `model`, `cost_usd`, and `norm_event`.
- Surfaces: `packages/workflow-analytics/src/routes/quality/+page.svelte`, `executions/+page.svelte`, `conversations/+page.svelte`, `conversation/+page.svelte`, `explore/+page.svelte`, `packages/workflow-analytics/src/routes/+layout.svelte`, `packages/workflow-analytics/src/lib/charts/`, `packages/workflow-analytics/tests/e2e/`.
- Approach: known
- Depends on: Phase 1, Phase 2

### Phase 5 — In-document dashboards

- Units:
  - **5-01-view-store-config** — `briefs/5-01-view-store-config.md`. Depends on: nothing. Runs alongside: 5-03-remove-embed-chrome, 5-07-analytics-site-doc.
  - **5-02-save-view-config** — `briefs/5-02-save-view-config.md`. Depends on: 5-01-view-store-config. Runs alongside: 5-03-remove-embed-chrome, 5-04-dashboard-tile-render (after 5-01).
  - **5-03-remove-embed-chrome** — `briefs/5-03-remove-embed-chrome.md`. Depends on: nothing. Runs alongside: 5-01-view-store-config, 5-07-analytics-site-doc.
  - **5-04-dashboard-tile-render** — `briefs/5-04-dashboard-tile-render.md`. Depends on: 5-01-view-store-config. Runs alongside: 5-03-remove-embed-chrome.
  - **5-05-dashboard-page-grid** — `briefs/5-05-dashboard-page-grid.md`. Depends on: 5-01-view-store-config, 5-04-dashboard-tile-render, 5-03-remove-embed-chrome. Runs alongside: nothing.
  - **5-06-dashboard-e2e** — `briefs/5-06-dashboard-e2e.md`. Depends on: 5-02-save-view-config, 5-05-dashboard-page-grid. Runs alongside: 5-07-analytics-site-doc.
  - **5-07-analytics-site-doc** — `briefs/5-07-analytics-site-doc.md`. Depends on: nothing. Runs alongside: 5-01-view-store-config, 5-03-remove-embed-chrome, 5-06-dashboard-e2e.
- Outcome:
  - Saving a view on `/usage` stores a config with no window and no filter keys. Adding it to a dashboard renders it in the dashboard page, not an iframe. Changing the dashboard window changes the tile's numbers. A second tile on the same dashboard uses that same window.
  - `embed=1` is not generated, and the layout no longer has an embed branch.
  - Import of a 13-tile document keeps 12 and states how many tiles were dropped.
  - A previously stored URL whose path is `/usage` and whose query carries a measure becomes a config that keeps the measure and drops the window and filter keys. A stored entry whose path is not a report is dropped and counted in the notice.
  - `docs/design/07-analytics-site.md` describes the theme override, the in-document dashboard, the overview links, the non-clickable marks, and zero-fill for count series only.
- Surfaces: `packages/workflow-analytics/src/lib/views.ts`, `packages/workflow-analytics/src/lib/components/SaveView.svelte`, `packages/workflow-analytics/src/routes/dashboards/+page.svelte`, `packages/workflow-analytics/src/routes/+layout.svelte`, `packages/workflow-analytics/tests/e2e/dashboards.spec.ts`, `docs/design/07-analytics-site.md`.
- Approach: known
- Depends on: Phase 1, Phase 3, Phase 4

## Provenance Notes

Ground was a pass per page group plus the analytics handlers. The pages and the API disagree with the request in different places: most comparison and trend charts are a client composition of `/query`, and the distributions, the score drift, and the run shape over time are not.

Rejected: a second chart library; replacing the route set; waiting for plan 13; `__other__` as a distribution row; weekday and hour as filters; a prior-window badge on the KPI tiles (the time series are the trend); an ingest-time sketch or a new rollup table; `partial` on reads that do not use the rollup; fixing the design 7 open issues that these outcomes do not touch (rejection attribution, CORS, release `npm ci`, cursor overflow, the `config` hook, live Claude message-id dedupe, the usage JSON scan, the explore stale-row bug).

The usage distribution scans extracted columns, not hook JSON. It does not take on open issue 9's rewrite of the existing usage aggregate.

Phase 1's first surface list could not make its color outcome true: stylesheet hexes also lived on conversation, conversations, executions, explore, repos, builder, the filter bar, and the chart components' `var()` fallbacks. The outcome stays whole-site. The surfaces are those files. Narrowing the outcome to Overview and Settings was rejected, because the request is the analytics UI, not two routes.

A page-per-phase split was considered and rejected. Five phases, each bullet of the outcome required, is the cut that can sign off.

Phase 3 refine (2026-10-16) coarse-checked phases 3–5: surfaces locatable in `packages/workflow-analytics` and `docs/design/07-analytics-site.md` where listed; contracts and outcomes stated in this design; dependency order Phase 3 on 1–2, Phase 4 on 1–2, Phase 5 on 1–3–4. No bounce.
