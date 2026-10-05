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
one capped tabular slice. Analytics is HTTP for a person, not an MCP tool: a dashboard does not
change what the agent does in a run (principle 2).

| Route | Report | Lens |
|---|---|---|
| `/` | Overview counts for the window | conversations, hooks, artifacts by kind, commits, rejections, screens |
| `/trends` | Time series | those volumes by day or week, split by one dimension |
| `/repos` | Repo comparison | the same volumes per `repo_id` |
| `/hooks` | Hook usage | `event` and `tool_name` distributions, plus harness |
| `/quality` | Score distributions | per check, for one artifact kind, against the all-time baseline |
| `/executions` | Design → brief → commit → report | derived execution shape, per brief |
| `/conversations` | Agent runs | one row per `conversation_id` |
| `/explore` | Pivot | the capped fact table in Perspective |
| `/settings` | Connection | API base URL and bearer token for a cross-origin deployment |

Every report except `/settings` shares one filter set held in the page URL: window, `repo_id`,
`harness`, `kind`, `plan`. The URL is the report; there is no saved-report store (the ledger has no
user identity to own one).

What the request's words mean on the ledger: an **agent** is a `conversation_id`; a **hook** is a
`hook_event` split by `event` and `payload.tool_name` (no cross-harness tool taxonomy); **build /
design usage** is the design → brief → commit → report shape, not CI or driver cost; an **analysis
type** is the artifact kind plus its check distributions.

## Analytics reads

Additive `/v1` routes. Every analytics `GET` resolves the tenant exactly as `GET /v1/artifacts`
does: local mode maps to tenant `local` and ignores any token; keyed mode requires `Authorization:
Bearer <key>`. `GET /v1/health` stays unauthenticated and is not an analytics route. Unknown routes
under `/v1/` are JSON 404; errors are `{"error":"<text>"}`. The routes read only fields the ledger
already stores: no payload bodies, artifact text, search snippets, model, token or cost fields.

### Shared filter

- `from`, `to`: RFC3339, inclusive. Omitted `to` is now; omitted `from` is `to` minus 30 days
  (**judgement**: a default, not a measured workflow length).
- More than 400 `day` buckets, or 400 `week` buckets with `bucket=week`, is 400 `{"error":"range too
  wide"}` (**judgement**: a response-size cap).
- `repo_id`, `harness`, `kind`, `plan`: repeatable; OR within a parameter, AND across. `kind` is
  `design`, `brief` or `report`, else 400. `/scores` instead requires exactly one `kind` (else 400
  `{"error":"kind required"}`).
- `kind` and `plan` are derived from `facts.path` with the rules of `keys.Kind`:
  `docs/plans/<plan>/DESIGN.md`, `docs/plans/<plan>/briefs/<file>.md`,
  `docs/plans/<plan>/reports/<file>.md`. Nested brief paths have no kind and count as `other`.
- Usage clocks use `facts.ts` (event time). Rejection counts and rejection rows use `rejections.at`.

### Routes

- `GET /v1/analytics/facets` — `{"repos","harnesses","kinds","plans","events","tools":[{"name","n"}],"checks":[{"kind","name"}]}`.
  Distinct values on in-window facts (called with the window only); `tools` is the 100 most frequent
  `payload.tool_name` on hook events; `checks` is the whole catalog from `GET /v1/checks`.
- `GET /v1/analytics/summary` — `from`, `to`, `conversations` (distinct), `hook_events`,
  `artifact_versions`, `distinct_content`, `by_kind {design,brief,report,other}`, `by_source
  {worktree,commit}`, `commits`, `rejections {precheck,screen}`, `screens {pass,unscreened}`
  (distinct in-window content hashes by latest screen verdict). Health's `pending` and
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
- Paging (executions, conversations): `limit` default 100, max 500 (**judgement**), `cursor` from a
  previous `next`; `next` absent on the last page. Executions order `ts` desc, `conversation_id`,
  `brief_path` asc. The cursor is opaque, bound to the route, the filters and the first page's
  resolved window; a cursor used with different filters is 400 `{"error":"cursor mismatch"}`.
- `GET /v1/analytics/explore` — one row per in-window fact plus in-window rejections (`type`
  `rejection`), newest first, with only the columns `type`, `ts`, `harness`, `repo_id`, `plan`,
  `kind`, `event`, `tool`, `path`, `conversation_id`, `source`, `sha`, `screen_verdict`,
  `rejection_stage`. At most 20,000 rows (**judgement**: browser memory), `truncated` true when more
  matched. Paths and tool names are not redacted: this is the same trust boundary as the other tenant
  reads.

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
- Fixed reports chart with LayerChart. `/explore` alone loads Perspective (client, viewer, server
  WASM) and says when the slice is capped. No second chart grammar, no SQL editor, no report
  builder, no BI shell (Evidence, Observable Framework, Rill, Grafana, Metabase, Superset,
  Lightdash, Cube and Tinybird each need a build-time snapshot or a second always-on service).
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
   `tools/workflow/internal/store/analytics.go`). Needs a decision on whether a rejection belongs to
   a repo (for example through its conversation's facts).
2. Executions and conversations paging loads the full sorted set and slices in Go; `Conversations`
   aggregates in Go and `Executions` uses a per-brief correlated `EXISTS`. Measure on a large tenant
   before relying on it remotely.
3. The hosted site sends no `X-Frame-Options` / `frame-ancestors`; a framed remote `/settings` could
   be clickjacked into redirecting the stored token.
4. `cors` sets `Vary: Origin` only for allowed origins (a shared cache could serve a header-less
   response to an allowed origin); `WORKFLOW_SERVE_CORS_ORIGINS` entries are never validated, so a
   trailing slash silently never matches.
5. `build.sh` runs `npm ci` only when `node_modules/` is absent, so a release can embed stale
   dependencies; a SIGKILLed run leaves the built site in `site/`, which the next run then saves as
   its "placeholder".
6. Cursor window bounds use `UnixNano`, which overflows outside 1678–2262.
7. Site: `/quality` shows distributions as a table with no chart; `/repos` omits an empty `repo_id`
   and fetches one summary per repo; `/settings` does not warn on an `http:` remote base or strip a
   trailing `/v1`; `/explore` keeps stale rows beside its error panel after a failed re-fetch;
   `format.ts` `num()` is unused.
8. Chart rendering is checked only through the tables; `svelte-check` is not installed. Perspective's
   viewer carries an opt-in LLM-chat feature that could send explore rows to a third-party provider
   if a user supplies a key.
