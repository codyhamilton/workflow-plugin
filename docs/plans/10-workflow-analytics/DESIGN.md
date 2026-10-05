# Workflow analytics site

## Intent

User request, verbatim:

> /design Lets add a new package with a static site built in svelte that provides access to effectively a dashboard/analytics for the user workflow stats. The site itself would be static and call workflow apis (in local exposed through `workflow serve`. In local the serve also serves the site, though for remote this would be a cloudflare pages site. 
>
> The site should provide a large number of different views on agent, hook, build/design usage with lenses by repo, trends over time, lenses by analysis type with distributions etc. It should allow filtering and providing different types of reports
>
> If there are out of the box tools for this type of analytics then great use it. If not wrap it up in a svelte site.
>
> Conduct thorough research using subagents for existing tools we can use for this kind of dashboard/analytics view into the workflow data. Examine thoroughly the data workflow contains in the various artifacts and how we can represent that in various ways and what the different lenses are. Then produce a comprehensive design to build the solution

## Problem

`workflow serve` already holds the tenant ledger (hook events, artifact versions, commits, screens, scores, rejections) but the only reads are point lookups for the agent: one artifact, the check catalog, all-time baselines, and full-text search (`docs/design/04-advisory-surface.md` API). Nothing answers a person's questions about their own workflow: how agents and hooks are used, how design / brief / report work moves, how scores are distributed, or how that changes by repo and over time.

A second always-on BI product does not fit. The site has to be static files, call the live tenant API at view time, be served by local `workflow serve`, and be the same build deployed to Cloudflare Pages against a remote serve. Evidence, Observable Framework, Rill, Grafana, Metabase, Superset, Lightdash, Cube, and Tinybird were checked against that constraint (Provenance Notes). None is the analytics engine. The gap is a browser-facing read model over the existing ledger, and a static Svelte client for it.

Words in the request, mapped onto the ledger:

- **Agent** is `conversation_id` (`/conversations`).
- **Hook** is `hook_event`, split by `event` and `payload.tool_name` (`/hooks`). There is no cross-harness tool taxonomy.
- **Build / design usage** is the design → brief → commit → report shape (`/executions` and the kind counts). It is not a repository build, a CI run, or a `tools/driver` cost rollup.
- **Analysis type** is artifact kind (`design`, `brief`, `report`) plus the check distributions on `/quality`. It is not a separate taxonomy.
- **Reports** are the named routes. The URL query is the report.

## Solution Shape

After this change, a static Svelte site (`packages/workflow-analytics`) offers a fixed set of report views over one tenant's workflow ledger. Locally, `workflow serve` serves those files on the same origin as `/v1`. Remotely, the same build is a Cloudflare Pages site and calls a keyed `workflow serve` with a browser-supplied bearer token. Aggregation stays in SQLite. The browser receives JSON aggregates and one capped tabular slice. The agent MCP surface is unchanged.

Views, and the lens each one is:

| Route | Report | Lens |
|---|---|---|
| `/` | Overview counts for the window | volume of conversations, hooks, artifacts by kind, commits, rejections, screens |
| `/trends` | Time series | those volumes by day or week, split by one dimension |
| `/repos` | Repo comparison | the same volumes side by side per `repo_id` |
| `/hooks` | Hook usage | `event` and `tool_name` distributions, plus harness |
| `/quality` | Score distributions | per check, for one artifact kind, against the existing all-time baseline |
| `/executions` | Design → brief → commit → report | derived execution shape from design 1, per brief |
| `/conversations` | Agent runs | one row per `conversation_id` |
| `/explore` | Pivot | arbitrary slice of the capped fact table (embedded Perspective) |
| `/settings` | Connection | API base URL and bearer token for a cross-origin deployment |

Every report except `/settings` shares one filter set, stored in the page URL: window, `repo_id`, `harness`, `kind`, `plan`. Changing a filter refetches and the URL is the shareable report. There is no saved-report store.

### Domain: Analytics reads (`workflow serve`)

- Owns: browser-facing aggregates over one tenant's existing ledger. Tenant isolation stays the directory-per-tenant rule in `docs/design/03-remote-service.md` (Storage).
- Contract: additive `/v1` routes below. Every analytics `GET` uses the same tenant resolution as `GET /v1/artifacts`: local mode maps the request to tenant `local` and ignores any bearer token; keyed mode requires `Authorization: Bearer <key>` (`tools/workflow/internal/serve/serve.go`). `GET /v1/health` stays unauthenticated and is not an analytics route. Unknown routes under `/v1/` stay JSON 404. Error body stays `{"error":"<text>"}`.

Design 3's first-round env table gains one variable. Close-out records it on that doc; until then this contract is the authority.

| Variable | Meaning |
|---|---|
| `WORKFLOW_SERVE_CORS_ORIGINS` | Comma-separated exact origins allowed to read a keyed server from a browser. Unset or empty: no CORS headers. Ignored in local mode, which uses the loopback-origin rule below. |

- Non-goals: ingest changes; new fact fields; MCP tools; full artifact text; FTS snippets; cross-tenant admin; persisting report definitions; redefining `/v1/baselines`; design 1's report-usage edge query (whether a later brief addressed a report's leftovers); driver, CI, or token-cost metrics; a health panel (see Hosting).

#### Shared filter

On every analytics route except where a parameter is called out as required:

- `from`, `to`: RFC3339, inclusive. Omitted `to` is the server's current time. Omitted `from` is `to` minus 30 days. **Judgement:** 30 days is a default window, not a measured length of a workflow. An explicit range is honored as given.
- A range that would produce more than 400 `day` buckets, or more than 400 `week` buckets when `bucket=week`, returns 400 `{"error":"range too wide"}`. **Judgement:** 400 is a response-size cap, not a measured cardinality of real tenants.
- `repo_id`, `harness`, `kind`, `plan`: repeatable. Values within one parameter are OR; different parameters are AND. `kind` must be `design`, `brief`, or `report`; anything else is 400. `GET /v1/analytics/scores` does not use the repeatable form: it requires exactly one `kind` parameter, and zero or more than one returns 400 `{"error":"kind required"}`. The other shared parameters still apply on that route.
- `plan` is the single path segment in `docs/plans/<plan>/`, derived from `facts.path`. It is not a stored column.
- Usage clocks use `facts.ts` (event time, Unix seconds). `GET /v1/analytics/summary` rejection counts and rejection rows in `/explore` use `rejections.at` instead, because a rejection is not a fact row.

`kind` and `plan` use the same path rules as `keys.Kind` (`tools/workflow/internal/keys/keys.go`): `docs/plans/<plan>/DESIGN.md`, `docs/plans/<plan>/briefs/<file>.md`, `docs/plans/<plan>/reports/<file>.md`. Nested brief paths have no kind, matching the current function, and fall under summary `other`.

#### `GET /v1/analytics/facets`

Distinct values in the window, for filter controls.

```json
{"repos":[""],"harnesses":[""],"kinds":["design"],"plans":[""],"events":[""],
 "tools":[{"name":"","n":0}],"checks":[{"kind":"design","name":"d.outcomes_checkable"}]}
```

`repos`, `harnesses`, `plans`, and `events` are every distinct value on facts in the window. `tools` is `payload.tool_name` on `hook_event` facts, the 100 most frequent, count descending. **Judgement:** 100 is a dropdown cap. Tool names are not normalized across harnesses; a missing `tool_name` is omitted, not mapped. `checks` is the in-memory catalog served by `GET /v1/checks` (all kinds), not only checks that have scores in the window.

#### `GET /v1/analytics/summary`

```json
{"from":"","to":"","conversations":0,"hook_events":0,"artifact_versions":0,
 "distinct_content":0,"by_kind":{"design":0,"brief":0,"report":0,"other":0},
 "by_source":{"worktree":0,"commit":0},"commits":0,
 "rejections":{"precheck":0,"screen":0},"screens":{"pass":0,"unscreened":0}}
```

`conversations` is distinct `conversation_id`. Artifact counts are `artifact_version` rows; `distinct_content` is distinct `content_hash`. `by_source` reads `source` on those rows (`worktree` or `commit`). `screens` classifies distinct artifact content hashes in the window by the latest `screens` verdict. A Jev flag does not insert a `screens` row; it is `rejections` stage `screen` (`docs/design/03-remote-service.md` Screening). `GET /v1/health`'s `pending` and `screen_gaps` stay the point-in-time gauges they are; this route does not window them.

#### `GET /v1/analytics/series`

Query: `metric` (required) `hook_events`, `artifact_versions`, `commits`, `conversations`, or `rejections`. `bucket` (required) `day` or `week` (UTC; `t` is the day's date or the Monday of the ISO week). `group` is `none` (default) or:

| `metric` | allowed `group` |
|---|---|
| `hook_events` | `harness`, `repo_id`, `event`, `tool` |
| `artifact_versions` | `harness`, `repo_id`, `kind`, `plan`, `source` |
| `commits` | `harness`, `repo_id` |
| `conversations` | `harness` |
| `rejections` | `stage` |

Any other pairing is 400. `conversations` counts distinct `conversation_id` per bucket; other metrics count rows. `tool` is `payload.tool_name`, and an empty name is the series key `""`.

`group=none` returns one series whose `key` is `"all"`. A grouped response uses the dimension value as `key` (empty string when the value is missing).

```json
{"bucket":"day","series":[{"key":"all","points":[{"t":"2026-10-01","n":0}]}]}
```

```json
{"bucket":"day","series":[{"key":"cursor","points":[{"t":"2026-10-01","n":3}]}]}
```

#### `GET /v1/analytics/scores`

`kind` is required, exactly one of `design`, `brief`, `report`.

```json
{"kind":"design","checks":[{"name":"d.outcomes_checkable","n":0,"min":0,"p25":0,"median":0,"p75":0,"max":0}]}
```

One object per catalog check for that kind, zeros when nothing was scored. The population is distinct `content_hash` of in-window artifact versions of that kind, taking the latest `scores` row per `(content_hash, check_name)`. `n` is how many of those hashes have a score for the check. `min`, `p25`, `median`, `p75`, and `max` use the same percentile already applied to baselines: sort the `result` values, take position `(n-1)*q` with linear interpolation between the surrounding indexes, and round to 3 decimal places (`percentile` and `round3` in `tools/workflow/internal/serve/reads.go`). `q` is 0, 0.25, 0.5, 0.75, and 1. An empty population yields 0 for all five. This is not `GET /v1/baselines`, which stays all-time over the latest version of each path (`docs/design/04-advisory-surface.md` Scores and baselines). The quality view reads both and shows the window against that baseline. It does not write a new baseline.

#### `GET /v1/analytics/executions`

Grain is one brief: `(repo_id, conversation_id, brief path)` where the path is `docs/plans/<plan>/briefs/<stem>.md` and at least one `artifact_version` of that path in that conversation has `ts` in the window.

Shape, from design 1's derived execution view (`docs/design/01-event-model-and-ingest.md` Derived execution view), applied per brief rather than per conversation (Assumption 3):

| `shape` | Rule |
|---|---|
| `complete` | that conversation has at least one `commit` fact in that `repo_id`, and an `artifact_version` of `docs/plans/<plan>/reports/<stem>.md` in that repo |
| `unreported` | at least one such commit, and no such report |
| `started` | no such commit |

Commit and report facts count even when their `ts` is outside the window. The window chooses which briefs are listed; the shape is a property of the conversation's facts. `harness` on the row is the brief fact's `harness`.

```json
{"counts":{"complete":0,"unreported":0,"started":0},
 "rows":[{"repo_id":"","plan":"","conversation_id":"","brief_path":"","harness":"","shape":"complete","ts":""}],
 "next":""}
```

`counts` covers every matching brief. `rows` is one page: `limit` default 100, maximum 500 (**judgement:** page size, not a measured brief count), `cursor` from a previous `next`. `next` is absent on the last page. Rows are ordered by `ts` descending, then `conversation_id` ascending, then `brief_path` ascending. `ts` is the earliest brief `ts` in the window, RFC3339. The cursor is opaque and bound to the filters and order that produced it. A `cursor` whose filters differ from the request returns 400 `{"error":"cursor mismatch"}`. The encoding is not part of the contract.

#### `GET /v1/analytics/conversations`

A conversation is included when any of its facts has `ts` in the window. Counts and `first_ts` / `last_ts` use only in-window facts. `harness` is the most frequent `harness` on those facts; ties break to the lexicographically smaller name. `repos` and `kinds` are the distinct values on those facts (`kinds` omits empty).

```json
{"rows":[{"conversation_id":"","harness":"","repos":[],"first_ts":"","last_ts":"",
           "hook_events":0,"artifact_versions":0,"commits":0,"kinds":[]}],"next":""}
```

Paging matches executions (`limit` default 100, max 500, same **judgement**, same opaque cursor and `cursor mismatch` rule). Rows are ordered by `last_ts` descending, then `conversation_id` ascending.

#### `GET /v1/analytics/explore`

One row per in-window fact, plus in-window rejection rows (`type` `rejection`), newest `ts` first (rejections use `at`).

Columns, and only these: `type`, `ts`, `harness`, `repo_id`, `plan`, `kind`, `event`, `tool`, `path`, `conversation_id`, `source`, `sha`, `screen_verdict`, `rejection_stage`. `sha` is set on `commit` facts and on artifact versions that carry it. `screen_verdict` is the latest screen for that `content_hash`, empty when there is none. No payload, no `raw`, no file content, no score values.

```json
{"rows":[{}],"truncated":false}
```

The response stops at 20,000 rows and sets `truncated` true when more rows match. **Judgement:** 20,000 is a browser-memory cap for the pivot, not a measured tenant size. `path` and `tool` are not redacted. Anyone who can call the tenant API can read them in bulk. That is the same trust boundary as the existing reads (loopback local mode, or the tenant bearer key): this route does not widen it, and it does not scrub tool names or paths.

#### Browser access

- Local mode (no `WORKFLOW_SERVE_KEYS`): if the request `Origin` host is loopback (`localhost`, `127.0.0.1`, `::1`), the response includes `Access-Control-Allow-Origin` set to that exact origin, `Access-Control-Allow-Headers: Authorization, Content-Type`, `Access-Control-Allow-Methods: GET, OPTIONS`, and `Vary: Origin`. `OPTIONS` returns 204. Any other origin gets no CORS headers. This lets the Vite dev server call loopback serve. It does not let a public page read loopback, because that page's `Origin` is not loopback. `localGuard` (loopback `Host`, JSON-only POST) stays as in design 3.
- Keyed mode: the same CORS headers are sent only when `Origin` is listed exactly in `WORKFLOW_SERVE_CORS_ORIGINS` (comma-separated). Unset or empty means no CORS headers. No wildcard and no reflected arbitrary origin.
- No cookies. The site sends `Authorization` only when a token is configured. `Access-Control-Allow-Credentials` is not set.

### Domain: Analytics site (`packages/workflow-analytics`)

- Owns: the static UI, its routes, filter URL state, and the connection settings. Package name `@codyhamilton/workflow-analytics`.
- Contract: SvelteKit built with the static adapter to a directory of HTML, CSS, and JS (no SSR server). Routes are the table in Solution Shape. Each report route loads, reads the shared filter from the URL, calls the matching `/v1/analytics/*` routes (and `/v1/baselines` on `/quality`), and renders that response. A filter change updates the URL and the numbers. `/settings` saves an API base URL and a bearer token in the browser's `localStorage` for that origin under the keys `workflow-analytics-base` and `workflow-analytics-key`. An empty base URL means same-origin relative `/v1`. The token is sent only as `Authorization: Bearer`. It is never written into the built assets or the repo.
- Charts on the fixed routes use LayerChart (MIT). `/explore` loads the JSON `rows` into Perspective (`@perspective-dev/client` and `@perspective-dev/viewer`, Apache-2.0) and shows that viewer. When `truncated` is true, the page shows that the slice is capped, not a silent prefix. No second chart grammar and no SQL editor.
- The bearer token in `localStorage` is as sensitive as the serve key. This design does not rotate it, expire it, or protect it beyond the origin's own storage. A script running on that origin can read it.
- Non-goals: a report builder; accounts; reading blob text; calling MCP; embedding Evidence, Grafana, or another BI shell.

### Domain: Hosting

- Owns: how the built files reach a browser, locally and as a Pages artifact.
- Contract:
  - The site build output is copied to `tools/workflow/internal/serve/site` before `go build` embeds it. `tools/release/build.sh` runs that site build first and fails if `index.html` is missing. A placeholder `index.html` in that directory contains the exact marker `workflow-analytics-placeholder`. While that marker is present, `GET /` and other non-file routes stay 404 `{"error":"analytics bundle not embedded"}`, so `go test` does not need Node.
  - When the marker is absent, `workflow serve` serves the embedded files at `/`. Unknown paths that do not start with `/v1/` return `index.html` (client-side routes). `/v1/*` is never HTML. `index.html` is `Cache-Control: no-cache`. Files under the Vite asset directory are `Cache-Control: public, max-age=31536000, immutable`.
  - The package's static build is also the Cloudflare Pages artifact (Pages-compatible output directory declared in the package). Deploying a project and attaching a hostname is an operator action, not a step this change can perform.
- Non-goals: provisioning a Cloudflare account or project; TLS termination (design 3 already puts remote serve behind a TLS proxy); serving different assets from the remote binary than from the local one (the binary always embeds the same files; Pages is a second host of that build); changing `GET /v1/health` (it stays unauthenticated and aggregate, and the site does not render it).

## Architectural Implications

- Design 3's API table is additive-only inside `/v1`. These routes fit that rule. Design 3 does not yet mention static files or CORS; this design is the amendment. Close-out promotes it. Until then, design 3's "no static files" reading is stale on purpose.
- Design 4 stays the agent surface. Principle 2 in `docs/design/system-architecture.md` (the agent-facing surface is read-only and exists to help the agent decide) is why analytics is HTTP for a person and not an MCP tool. A dashboard does not change what the agent does in a run.
- Design 3 (Storage, Tables) says derived views are built by a reader into separate tables, and points their definition at design 4 and the lab. This change does not add those tables. `/v1/analytics/executions` is computed at read time from `facts`, narrowed per Assumption 3. Close-out reconciles that sentence in design 3 with design 1: the execution view is a read, not an ingest table. Design 1's report-usage edge query ("Usage measure") stays unbuilt and is a non-goal above.
- `docs/ARCHITECTURE.md`'s component map does not mention `tools/workflow` at all. That drift predates this design (plan `09-workflow-binary` is not closed out). This design does not depend on that map; it depends on `docs/design/01`, `03`, and `04`. The map is not rewritten here.
- Hook payloads are not a stable schema. `tool` and `event` are sparse and harness-specific. Views must tolerate empty keys. Model, token, and cost fields are not columns and are not added (Assumption 2).
- `Workflow-Phase:` trailers and `Workflow-Plan:` PR lines are git facts outside the ledger. Phase progress is not a lens this site can show without a capture change, which is out of scope.

## Decisions

- No hosted BI server. Evidence.dev, Observable Framework, Rill, Grafana (AGPL, server-side datasource), Metabase (AGPL), Superset, Lightdash, Cube, and Tinybird each need a build-time snapshot or a second always-on service. The site calls live per-tenant HTTP at view time (Intent). Rejected 2026-10-05; notes and URLs in Provenance Notes.
- SvelteKit static adapter, because the Intent asks for a static Svelte site when no out-of-the-box tool fits.
- LayerChart for the fixed reports; Perspective only for `/explore`. Observable Plot, ECharts, Vega-Lite, and AG Grid were not added beside those two.
- Aggregation in SQLite. DuckDB-WASM over bulk JSON was rejected as a second query engine on top of a ledger the server already queries.
- The person-facing API is new `/v1/analytics/*` routes. Extending `GET /v1/artifacts` into a listing would blur the agent point-lookup contract in design 4.
- The invoker did not declare a posture. The skill default is interactive, so this document does not claim a headless sign-off. The ledger is still the record of the choices the build would proceed on, because this run cannot hold a live checkpoint (Assumption 1). Downstream review challenges the ledger; it is not waved through.

## Assumption Ledger

### Assumption 1

- Question: the invoker did not declare interactive or headless. The skill says posture is declared, never inferred, and defaults to interactive. What is recorded here?
- Answer chosen: the choices are written as a ledger so the design can be built, and they are explicitly not a headless sign-off. No `PROVENANCE.md`, because there was no interactive turn.
- Rationale: the request says to produce the design, and this run has no turn-by-turn channel to ask in. Inferring "headless" would wave the checkpoint through, which the skill reserves for a declared headless run. Leaving the choices unwritten would not produce a design.
- If wrong: the invoker declares interactive, the ledger becomes unanswered questions, and the answers move into `PROVENANCE.md` before build.

### Assumption 2

- Question: should the dashboard add capture for model, tokens, cost, duration, or user id so those charts exist?
- Answer chosen: no. Charts use only what the Go ledger stores today.
- Rationale: design 1 mentions model and cost only "where the payload has them", and the store has no such columns (`tools/workflow/internal/store/store.go` `facts`). The driver cost rollup and the legacy Python ledger are different stores. Adding capture is a different design (event model and drain), and the Intent asks for a site over workflow data, not a new fact type.
- If wrong: a follow-on design adds normalized fields at drain time, then this API gains dimensions. The site routes do not need to change shape to display a new `group`.

### Assumption 3

- Question: design 1 defines an execution as a conversation that has a brief, commits, and a report. Is the analytics grain the conversation or each brief?
- Answer chosen: one row per `(repo_id, conversation_id, brief path)`, with the report path `docs/plans/<plan>/reports/<stem>.md` paired to that brief.
- Rationale: design 1 decision 1 is one report per brief. A conversation-level OR would mark the conversation complete when one brief of several has a report.
- If wrong: collapse to one row per `(repo_id, conversation_id)` using "any brief" and "any report". Counts change; the route stays.

### Assumption 4

- Question: how does a Pages site authenticate to a remote serve, given design 3 leaves registration and `workflow login` unimplemented?
- Answer chosen: the user types the serve base URL and a bearer key. That key is the tenant key from `WORKFLOW_SERVE_KEYS` (the same value the drain and shim use when `client.toml` has been written). The browser stores them in `localStorage` for the Pages origin. `workflow login` is not built (`docs/design/05-distribution.md`), so this design does not grow a login flow, a refresh token, or rotation.
- Rationale: one key per tenant already exists. A login service would reopen registration, which design 3 and plan 09 kept out of scope. The token is as sensitive as that key; XSS on the Pages origin can read it. Accepted for this operator-facing site.
- If wrong: a later design issues a short-lived browser token. The analytics routes keep accepting `Authorization: Bearer`.

### Assumption 5

- Question: does this change create the Cloudflare Pages project?
- Answer chosen: no. It produces the static build and the CORS allowlist the project needs. An operator deploys it and sets `WORKFLOW_SERVE_CORS_ORIGINS` to the Pages origin.
- Rationale: the repo has no Cloudflare credentials, and a live hostname cannot be an outcome of this change.
- If wrong: deployment is a later phase with a named account; the build contract does not change.

### Assumption 6

- Question: which clock is a trend?
- Answer chosen: `facts.ts` for usage. Rejection counts use `rejections.at`. Commit and report facts outside the window still count toward execution shape (see the executions contract).
- Rationale: `ts` is when the harness recorded the event; `received_at` is ingest lag. Scoring time would smear the activity the user asked to see.
- If wrong: add `clock=event|received` on the shared filter. Default remains event time.

### Assumption 7

- Question: are report definitions saved server-side?
- Answer chosen: no. The URL query is the report.
- Rationale: there is no user identity in the ledger (Assumption 2), so a saved-report table has no owner. Sharing a URL does not need one.
- If wrong: a tenant-scoped table of named filter sets, and a route to open them. The analytics aggregates stay.

## Open Questions

None that block a phase. Assumption 1 records that posture was not declared. Overturning any ledger entry changes scope the way that entry's "If wrong" describes. The undeclared posture does not block phase 1's API from being specified.

## Phases

Three phases. More than one unit, so `refine` runs before each is built. The phase count is fixed here.

### Phase 1 — Analytics reads

- Outcome: with `workflow serve` running on a fixture tenant, `GET /v1/analytics/summary`, `series`, `facets`, `scores`, `executions`, `conversations`, and `explore` return the JSON shapes in the Analytics reads contract, and the counts match the fixture's facts (including per-brief execution shape, percentiles computed as `percentile`/`round3` do for baselines, page order, and `truncated` when the explore cap is exceeded). A `GET` and an `OPTIONS` from `Origin: http://127.0.0.1:<any port>` in local mode include that origin in `Access-Control-Allow-Origin`, and the `OPTIONS` returns 204. A `GET` from `Origin: https://evil.example` includes no CORS header. A keyed server sends those CORS headers only for an origin listed in `WORKFLOW_SERVE_CORS_ORIGINS`. `GET /v1/artifacts` and `GET /v1/health` keep their current shapes.
- Guards against: a site built on invented fields, and a public page reading a keyless loopback ledger.
- Required by: the Intent's lenses (repo, time, analysis type, agent, hook, design/build usage) and design 3's browser guards (`docs/design/03-remote-service.md` Local and remote). The field list is the store as of `tools/workflow/internal/store/store.go` and design 1's execution table.
- Surfaces: `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/reads.go`, `tools/workflow/internal/store/reads.go`, `tools/workflow/internal/store/store.go`, and the tests next to those files.
- Approach: known
- Depends on: nothing
- Units:
  - 1-01 Browser access (CORS) — `briefs/1-01-browser-access.md` — depends on: nothing — alongside: 1-02
  - 1-02 Store analytics queries — `briefs/1-02-store-analytics.md` — depends on: nothing — alongside: 1-01
  - 1-03 `/v1/analytics/*` routes — `briefs/1-03-analytics-routes.md` — depends on: 1-01, 1-02 — alongside: nothing

### Phase 2 — Report views

- Outcome: from `packages/workflow-analytics`, the static build emits a directory of HTML/JS/CSS. Those files may be served by any static host; `workflow serve` answering `GET /` with them is phase 3. Against a phase-1 serve, opening `/`, `/trends`, `/repos`, `/hooks`, `/quality`, `/executions`, `/conversations`, and `/explore` shows the fixture's numbers for that route's lens; setting `repo_id` in the URL changes those numbers to the filtered fixture; reloading the same URL keeps the filter. `/quality` shows each check's window percentiles beside the `/v1/baselines` figures. `/explore` shows the Perspective viewer on the explore rows, and when the fixture sets `truncated` the page says the slice is capped. `/settings` stores a base URL and token, and a later request to a cross-origin serve carries `Authorization: Bearer` with that token. The built assets contain neither the token nor a tenant key.
- Guards against: filters that do not survive a reload, a quality view that quietly replaces the agent baseline, and a key baked into the Pages bundle.
- Required by: the Intent (static Svelte site, many views, filters, report types). Routes are the report types listed in Solution Shape.
- Surfaces: `packages/workflow-analytics/` (`package.json`, SvelteKit config, and the route modules under that package).
- Approach: known
- Depends on: Phase 1

### Phase 3 — Local serve hosts the site

- Outcome: after `tools/release/build.sh`, `workflow serve` bound to loopback answers `GET /` with the built `index.html` (`Content-Type: text/html`, no placeholder marker) and `GET /v1/health` with the existing JSON. Loading `http://127.0.0.1:<port>/` in a browser shows the overview counts from the same origin with no token configured. A client-side route such as `/quality` refreshes to the quality view rather than a JSON 404. `GET /v1/not-a-route` stays JSON 404. A tree still containing `workflow-analytics-placeholder` in the embedded `index.html` keeps `GET /` as JSON 404 `{"error":"analytics bundle not embedded"}`. The package declares a Pages output directory that is this same static build.
- Guards against: local serve failing to host the site the Intent asks for, SPA routes breaking the `/v1` API, and a release binary shipping the placeholder.
- Required by: the Intent's local-serve hosting, and design 3's rule that `/v1` stays the API. Pointer: `tools/release/build.sh` is the release build; `tools/workflow/internal/serve/serve.go` is the mux.
- Surfaces: `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/site/`, `tools/release/build.sh`, `packages/workflow-analytics/` Pages output config.
- Approach: known
- Depends on: Phase 2

## Provenance Notes

A clean-context pass on 2026-10-05 challenged posture, the design-3 execution-table citation, score percentile definition, pagination order, CORS preflight, explore truncation in the UI, and the bearer-token threat. Those edits are in the contracts and the ledger. The pass did not reopen the library choice or the phase split.

Ground (2026-10-05) read the Go store, the serve mux, design 1, 3, and 4, and the check catalog. The ledger tables are `facts`, `rejections`, `screens`, `scores`, and FTS `search`. Kind is path-derived. Scores are 0–1 per check on content hashes. Baselines are computed, not stored. Blobs exist on disk and are not returned by any current GET. The legacy Python service (`tools/quality`) and `tools/driver` run records have cost figures the Go ledger does not; they are not sources for this site. `tools/harness` watches subscription quotas, not plan throughput.

Rejected as the dashboard shell:

- Evidence.dev (MIT, SvelteKit, Cloudflare Pages) snapshots sources to Parquet at build time. Wrong for a live per-tenant API.
- Observable Framework (ISC) data loaders run at build time, and the UI is not Svelte.
- Rill (Apache-2.0), Superset (Apache-2.0), Lightdash, and Cube are always-on analytics servers in front of the warehouse. They duplicate `workflow serve`.
- Grafana and Metabase are AGPL servers. Grafana's Infinity datasource queries from the Grafana process, not the browser.
- Tinybird is a hosted second data plane; its chart kit is React.

Perspective stays because `/explore` needs a pivot, which is the one out-of-the-box piece that runs as static WASM on JSON the API already returns. LayerChart stays because the fixed reports are Svelte charts over small aggregate payloads, and Perspective's charts are not those reports.

Also rejected: showing artifact bodies or search snippets in the dashboard (design 3 stores content only after screening, and a human browser is a wider leak than the agent shim); adding analytics tools to `workflow mcp` (design 4's tool list is closed); treating `GET /v1/health` pending counts as a time series; building design 1's report-usage edge query (it "waits for the linked dataset" and nothing in the Intent asks whether a leftover was later addressed).
