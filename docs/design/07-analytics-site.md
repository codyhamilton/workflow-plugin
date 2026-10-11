# Design Intent 7: Analytics Site

The person-facing view of one tenant's workflow ledger: read-only aggregate routes on `workflow
serve`, and a static Svelte site that renders them. Part of
[system-architecture.md](system-architecture.md); it reads the service in
[03-remote-service.md](03-remote-service.md) and is a separate surface from the agent's
[04-advisory-surface.md](04-advisory-surface.md).

## Shape

`packages/workflow-analytics` is a SvelteKit site built with the static adapter to `build/` (HTML,
CSS, JS; no SSR). Locally, `workflow serve` embeds that build and serves it on the same origin as
`/v1`. Remotely, the same build is a Cloudflare Pages site that calls a keyed `workflow serve` with a
browser-supplied bearer token. Aggregation stays in SQLite; the browser receives JSON aggregates and
one capped tabular slice. The site never receives hook bodies. Analytics is HTTP for a person, not an MCP tool: a dashboard does not
change what the agent does in a run (principle 2).

| Route | Report | Lens |
|---|---|---|
| `/` | Overview | KPI tiles with sparklines (conversations, hooks, artifacts, commits, cost, tokens), an hour-of-day × weekday heatmap |
| `/trends` | Time series | volumes by bucket, split by one dimension; brush to zoom |
| `/usage` | Usage and cost | tokens and cost by model, harness and repo, plus the cost trend |
| `/repos` | Repo comparison | the same volumes per `repo_id` |
| `/hooks` | Hook usage | harness → `norm_event` and `norm_event` → tool treemaps |
| `/quality` | Score distributions | per check, for one artifact kind, as box plots beside the all-time baseline |
| `/executions` | Design → brief → commit → report | derived execution shape, per brief, as a sankey and a table |
| `/conversations` | Agent runs | one row per `conversation_id`, virtualised |
| `/conversation` | One run | timeline of its events with token and cost totals |
| `/explore` | Pivot | the capped fact table in Perspective |
| `/builder` | Chart builder | any measure, up to two dimensions and a bucket |
| `/dashboards` | Dashboards | ordered grids of saved views |
| `/settings` | Connection | API base URL and bearer token for a cross-origin deployment |

Every report except `/settings` shares one filter set held in the page URL: window, `repo_id`,
`harness`, `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`. The
URL is the view: filters, window, active view and every chart configuration (measure, dimensions,
bucket, chart type, top) serialise into the query string, so pasting it reproduces the view, and
filters survive navigation between views. There is no server-side saved-view store (the ledger has no
user identity to own one).

What the request's words mean on the ledger: an **agent** is a `conversation_id`; a **hook** is a
`hook_event` split by `event` and `payload.tool_name` (no cross-harness tool taxonomy); **build /
design usage** is the design → brief → commit → report shape, not CI or driver cost; **usage and
cost** are the model calls, tokens and cost the harnesses report; an **analysis
type** is the artifact kind plus its check distributions.

## Analytics reads

Additive `/v1` routes. Every analytics `GET` resolves the tenant exactly as `GET /v1/artifacts`
does: local mode maps to tenant `local` and ignores any token; keyed mode requires `Authorization:
Bearer <key>`. `GET /v1/health` stays unauthenticated and is not an analytics route. Unknown routes
under `/v1/` are JSON 404; errors are `{"error":"<text>"}`. The routes read only the ledger's columns: no payload bodies (the ledger holds none, design 1), no
artifact text and no search snippets. Model, token and cost fields are served as aggregates and as
per-call rows in the conversation timeline.

### Shared filter

- `from`, `to`: RFC3339, inclusive. Omitted `to` is now; omitted `from` is `to` minus 30 days
  (**judgement**: a default, not a measured workflow length). `all=1` replaces `from` and means the
  whole ledger (`/query` only; the other routes reject windows over 400 days, so the site clamps All
  time to 399 days there and says so).
- `tz`: IANA name, default `UTC`. Bucket boundaries and the `hour_of_day` and `weekday` dimensions
  use it; an unknown name is 400 `{"error":"invalid tz"}`.
- More than 400 buckets of the requested unit is 400 `{"error":"range too wide"}` (**judgement**: a
  response-size cap).
- `repo_id`, `harness`, `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`,
  `conversation_id`: repeatable; OR within a parameter, AND across. `kind` is `design`, `brief` or
  `report`, else 400. `/scores` instead requires exactly one `kind` (else 400 `{"error":"kind
  required"}`).
- On `/query`, a filter on a dimension the requested measure does not carry is ignored and its key is
  listed in `ignored_filters`, instead of silently dropping the measure to zero.
- `kind` and `plan` are columns filled at ingest from the path with the rules of `keys.Kind`:
  `docs/plans/<plan>/DESIGN.md`, `docs/plans/<plan>/briefs/<file>.md`,
  `docs/plans/<plan>/reports/<file>.md`. Nested brief paths have no kind and count as `other`.
- Usage clocks use `facts.ts` (event time). Rejection counts and rejection rows use `rejections.at`.
- Reads use indexed columns and, for whole interior hours of a time-only window, the hourly rollup
  tables ([design 3](03-remote-service.md#tables)); the two partial edge hours read base rows, so the
  result equals aggregating base rows alone. While the ledger is uncompacted (`/v1/health`
  `compaction` is `required`), `/query` responses carry `"partial": true`.

### Routes

- `GET /v1/analytics/facets` — `{"repos","harnesses","kinds","plans","events","norm_events","models","tools":[{"name","n"}],"checks":[{"kind","name"}]}`.
  Distinct values on in-window facts (called with the window only); `tools` is the 100 most frequent
  `tool` on hook events; `checks` is the whole catalog from `GET /v1/checks`.
- `GET /v1/analytics/summary` — `from`, `to`, `conversations` (distinct), `hook_events`,
  `artifact_versions`, `distinct_content`, `by_kind {design,brief,report,other}`, `by_source
  {worktree,commit}`, `commits`, `rejections {precheck,screen}`, `screens {pass,unscreened}`
  (distinct in-window content hashes by latest screen verdict), and the usage totals `model_calls`,
  `unpriced_calls`, `cost_usd` and `tokens_*`. Health's `pending` and
  `screen_gaps` stay point-in-time gauges.
- `GET /v1/analytics/series` — `metric` and `bucket` (`day`, or `week` = ISO Monday, UTC) required;
  `group` defaults to `none` (one series keyed `"all"`). Allowed pairings, anything else 400:
  `hook_events`: `harness`, `repo_id`, `event`, `tool`; `artifact_versions`: `harness`, `repo_id`,
  `kind`, `plan`, `source`; `commits`: `harness`, `repo_id`; `conversations` (distinct per bucket):
  `harness`; `rejections`: `stage`. Missing values key as `""`. Series are sparse: a bucket with no
  rows has no point; the site zero-fills between the first and last bucket when charting.
  Response `{"bucket","series":[{"key","points":[{"t","n"}]}]}`.
- `GET /v1/analytics/scores` — `{"kind","checks":[{"name","n","min","p25","median","p75","max"}]}`,
  one object per catalog check for the kind. Population: distinct in-window content hashes of that
  kind, latest score per `(content_hash, check)`. Percentiles use the baseline method (sorted values,
  position `(n-1)*q` with linear interpolation, rounded to 3 places); empty is all zeros. This never
  writes or replaces `GET /v1/baselines`, which stays all-time; `/quality` shows the two side by side.
- `GET /v1/analytics/executions` — grain is one brief `(repo_id, conversation_id,
  docs/plans/<plan>/briefs/<stem>.md)` with an in-window version. `shape` is `complete` (the
  conversation has a commit in that repo and a version of `reports/<stem>.md` exists in that repo),
  `unreported` (commit, no report) or `started` (no commit); commit and report facts count even
  outside the window. Response `{"counts":{complete,unreported,started},"rows":[{repo_id,plan,conversation_id,brief_path,harness,shape,ts}],"next"}`.
  This is [design 1](01-event-model-and-ingest.md)'s derived execution view applied per brief and
  computed at read time; it is not an ingest-side table.
- `GET /v1/analytics/conversations` — conversations with any in-window fact; counts and
  `first_ts`/`last_ts` from in-window facts only; `harness` is the most frequent (ties to the smaller
  name); `repos` and `kinds` distinct. Ordered `last_ts` desc, `conversation_id` asc.
- Paging (executions, conversations) is keyset in SQL: `limit` default 100, max 500 (**judgement**), `cursor` from a
  previous `next`; `next` absent on the last page. Executions order `ts` desc, `conversation_id`,
  `brief_path` asc. The cursor is opaque, bound to the route, the filters and the first page's
  resolved window; a cursor used with different filters is 400 `{"error":"cursor mismatch"}`.
- `GET /v1/analytics/explore` — one row per in-window fact plus in-window rejections (`type`
  `rejection`), newest first, with only the columns `type`, `ts`, `harness`, `repo_id`, `plan`,
  `kind`, `event`, `norm_event`, `tool`, `model`, `cost_usd`, `path`, `conversation_id`, `source`,
  `sha`, `screen_verdict`, `rejection_stage`. At most 20,000 rows (**judgement**: browser memory), `truncated` true when more
  matched. Paths and tool names are not redacted: this is the same trust boundary as the other tenant
  reads.
- `GET /v1/analytics/query` — the generic aggregate. `measure` is required; `dim` is given 0 to 2
  times; `bucket` is `none` (default), `hour`, `day`, `week` (ISO Monday) or `month`; `top` defaults
  to 20, max 100, and ranks each dimension's keys independently by the measure's total over the
  window. Keys outside the top N fold into `"__other__"`, which is not a valid filter value. Response
  `{"measure","bucket","dims":[…],"rows":[{"t"?,"k":[…],"v"}],"ignored_filters"?,"partial"?,"truncated"?}`,
  capped at 20,000 rows (**judgement**); rows are sparse and `t` is RFC3339 in `tz`. An unsupported
  measure × dimension pairing is 400 `{"error":"unsupported dimension <d> for <measure>"}`.
- `GET /v1/analytics/schema` — the matrix below, verbatim: `{"measures":[{"name","unit","dims":[…]}],"buckets":[…]}`.
  The builder is driven only by this, so it cannot offer a pairing the server rejects.

  | Measure | Dimensions |
  |---|---|
  | `hook_events` | `harness`, `repo_id`, `norm_event`, `event`, `tool`, `conversation_id` |
  | `conversations` (distinct) | `harness`, `repo_id`, `model` |
  | `artifact_versions`, `distinct_content` | `harness`, `repo_id`, `kind`, `plan`, `source`, `conversation_id` |
  | `commits` | `harness`, `repo_id`, `conversation_id` |
  | `rejections` | `stage` |
  | `model_calls`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`, `cost_usd`, `unpriced_calls` | `harness`, `repo_id`, `model`, `conversation_id` |

  Every measure also takes `hour_of_day` and `weekday`.
- `GET /v1/analytics/conversation` (`id` required; unknown id is 404) — `{"conversation_id","harness","repos","models","first_ts","last_ts","totals":{tokens…,cost_usd},"events":[{"ts","type","norm_event","event","tool","model","path","kind","source","sha","tokens"?,"cost_usd"?}]}`
  in time order, capped at 5,000 events (**judgement**) with `truncated`. It returns no bodies.

**Count semantics.** `hook_events` counts stored hook events. Events on the ingest policy's `remove`
list are never stored, so they are not counted; a streamed message part counts once, through its
`message.part.updated` event. A model call is counted once (a Claude message ID repeated across
transcript lines counts once).

**Cost.** `cost_usd` is computed at read time: a call's reported cost when the harness gave one,
otherwise its tokens × the model's price in a pricing table that `serve` embeds, generated from
`tools/transcript/pricing.json` (a test asserts the two are equal). A call with neither is counted in
`unpriced_calls` and adds 0; the site shows such cost as unpriced, never as `$0`. Repricing needs
only a new binary. Codex input tokens include cached input, so cached tokens are not charged twice.

**Performance bound.** A committed benchmark (`analytics_bench_test.go`, run against any ledger path
via `WORKFLOW_BENCH_DIR`) times every route, each preset (24h, 7d, 30d, 90d, all time), every measure
with 0, 1 and 2 dimensions and every bucket within the cap. The bound is p95 under 500 ms per case, met
on a compacted copy of the real ledger.

### Browser access

- Local mode: when the request `Origin` host is loopback (`localhost`, `127.0.0.1`, `::1`), the
  response carries that exact origin in `Access-Control-Allow-Origin`, plus `Allow-Headers:
  Authorization, Content-Type`, `Allow-Methods: GET, OPTIONS` and `Vary: Origin`; `OPTIONS` is 204.
  Other origins get no CORS headers, so a public page cannot read a keyless loopback ledger.
  `localGuard` (loopback `Host`, JSON-only POST) runs first.
- Keyed mode: the same headers only for an origin listed exactly in `WORKFLOW_SERVE_CORS_ORIGINS`
  ([design 3](03-remote-service.md#configuration-first-round)). No wildcard, no reflected origin.
- No cookies and no `Access-Control-Allow-Credentials`. The site sends `Authorization` only when a
  token is configured.

## The site

- `/settings` stores an API base URL and a bearer token in `localStorage` under
  `workflow-analytics-base` and `workflow-analytics-key`. An empty base means same-origin `/v1`. The
  token is sent only as `Authorization: Bearer` and never written into the build or the repo; the
  build's bundle check fails if a key appears in it.
- That token is as sensitive as the tenant key and is not rotated or expired: any script on the
  origin can read it. A later design may issue a short-lived browser token; the routes keep
  accepting `Authorization: Bearer`.
- Charts render with Apache ECharts, tree-shaken, with one colour token set in light and dark themes
  following the system preference. Each chart has a data-table toggle, and the site works down to
  1024 px wide. `/explore` alone loads Perspective (client, viewer, server WASM) and says when the
  slice is capped. No second chart grammar, no SQL editor, no BI shell (Evidence, Observable Framework, Rill, Grafana, Metabase, Superset,
  Lightdash, Cube and Tinybird each need a build-time snapshot or a second always-on service).
- **Window.** Presets Today, 24h, 7d, 30d, 90d, This month, YTD and All time, a custom range, and
  brush-to-zoom on any time-axis chart. Presets stay relative in a shared URL. Times display in the
  browser's zone, which is sent as `tz`. Each chart uses the finest bucket within the cap unless one
  is set.
- **Data layer.** One client module issues every request. It debounces filter changes, aborts
  superseded requests and caches responses for the session by normalised query, so the UI never
  renders a superseded result. It shows `partial` and `ignored_filters` as notices. The server has
  no exclude parameter, so an exclude chip is sent as the complement of the facet values; an
  exclude on `conversation_id` is unsupported and marked so.
- **Drill-down.** Every chart mark and table row for a dimension value applies it as a filter
  (shift-click excludes it); `__other__` is not clickable. Active filters show as removable chips.
  Any conversation ID opens its timeline, and counts link to the filtered explore slice.
- **Chart builder.** `/builder` is driven only by `/v1/analytics/schema`: any measure, up to two
  dimensions and a bucket. Chart types are line, stacked area, bar, stacked bar, heatmap, treemap
  and small multiples, offered only where the shape fits; an unsupported pairing cannot be selected.
- **Saved views and dashboards.** A named saved view is a stored URL; a dashboard is an ordered grid
  of saved views, rendered as framed `embed=1` pages and exportable and importable as JSON. Both
  live in `localStorage` under the prefix `workflow-analytics-views`.
- A response that is not JSON (a static host answering `/v1` with HTML) is a connection error
  pointing at `/settings`.

## Hosting

- The site's build output is copied into `tools/workflow/internal/serve/site/` before `go build`
  embeds it (`//go:embed all:site`). `tools/release/build.sh` builds the site first and fails if
  `index.html` is missing or is the placeholder, then restores the committed placeholder on exit.
- The committed placeholder `index.html` contains the marker `workflow-analytics-placeholder`. While
  it is embedded, every non-`/v1` path is 404 `{"error":"analytics bundle not embedded"}`, so `go
  test` needs no Node.
- With the real build embedded: `GET`/`HEAD` only (else 405). An existing file is served with its
  type; `/`, `/index.html` and any non-file path return `index.html` (client routes) with
  `Cache-Control: no-cache`; files under `_app/immutable/` are `public, max-age=31536000,
  immutable`. `/v1` and `/v1/*` are never HTML. In keyed mode the static files need no key; they
  carry no tenant data.
- `packages/workflow-analytics/wrangler.toml` declares `pages_build_output_dir = "./build"`, the same
  build. With no `404.html`, Pages serves it as a single-page app. Creating the Pages project,
  attaching a hostname and setting `WORKFLOW_SERVE_CORS_ORIGINS` to that origin are operator
  actions.

## Open issues

1. Precheck rejection rows carry empty `repo_id`/`harness`, so any `repo_id` or `harness` filter
   drops rejections to zero in `summary` and `explore` (`rejWhere`,
   `tools/workflow/internal/store/analytics.go`). `/query` reports the filter in `ignored_filters`
   instead, but the other routes still need a decision on whether a rejection belongs to a repo (for
   example through its conversation's facts).
2. The hosted site sends no `X-Frame-Options` / `frame-ancestors`; a framed remote `/settings` could
   be clickjacked into redirecting the stored token.
3. `cors` sets `Vary: Origin` only for allowed origins (a shared cache could serve a header-less
   response to an allowed origin); `WORKFLOW_SERVE_CORS_ORIGINS` entries are never validated, so a
   trailing slash silently never matches.
4. `build.sh` runs `npm ci` only when `node_modules/` is absent, so a release can embed stale
   dependencies; a SIGKILLed run leaves the built site in `site/`, which the next run then saves as
   its "placeholder".
5. Cursor window bounds use `UnixNano`, which overflows outside 1678–2262.
6. Site: `/settings` does not warn on an `http:` remote base or strip a trailing `/v1`; `/explore`
   keeps stale rows beside its error panel after a failed re-fetch.
7. `svelte-check` is not installed, so component types are unchecked (charts are exercised by
   Playwright). Perspective's viewer carries an opt-in LLM-chat feature that could send explore rows
   to a third-party provider if a user supplies a key.
8. Live Claude usage is not deduplicated: only backfilled facts carry the message id, so a repeated live `message_id` is counted twice. Fix: capture the id into a column at ingest and dedupe on it.
9. Usage measures aggregate in Go over every kept row, so an All-time window is unbounded in memory and the usage read sorts and parses JSON per row (benchmark headroom is 464 ms of 500 ms). Fix: group in SQL or add a usage rollup.
10. Compaction and the archive: `Read` stops at a torn frame until `Repair` runs; compaction re-archives already-slim rows as lossy lines; the `complete` shortcut can skip rows before `compact_cursor`; the disk check ignores the VACUUM copy.
11. The OpenCode `config` hook is captured and is not on the remove list, and it can carry provider keys. Decide whether to add it to the remove list in ingest and the plugin.
12. `partial` is emitted only by `/query`; conversation totals cover only the returned events when a timeline is truncated; `time/tzdata` is not imported in serve, `tz=Local` is accepted, filter value counts and `top` are unbounded, and the locked-tenant 503 echoes the tenant path.
13. Builder: zero dimensions with bucket `none` renders a chart with no valid type; `data-ready` is true while the previous chart is still shown. Dashboards: import bypasses the 12-tile cap, a fragment in a saved URL drops `embed=1`, the saved-view store does not validate stored entries on read, and `/dashboards` has no settle signal.
14. The Executions sankey filters client-side over the loaded first page, so counts trail the totals until the user pages on.
15. Pricing rates for Claude and Codex are missing from `tools/transcript/pricing.json` and `internal/store/pricing_table.json`, so most calls are unpriced. A `serve` built without the site build first reports "analytics bundle not embedded".
