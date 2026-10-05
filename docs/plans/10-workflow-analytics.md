# Workflow Analytics Site

A static Svelte dashboard over one tenant's workflow ledger, plus the read API it needs.
`workflow serve` gained seven aggregate `/v1/analytics` routes and browser CORS, a new package
`packages/workflow-analytics` renders nine report views from them, and the release binary embeds
that site so local serve hosts it at `/`; the same build is declared as a Cloudflare Pages output.
All three phase outcomes were met and the terminal review passed with follow-ups. The contracts
live on in [design 7](../design/07-analytics-site.md).

## Intent

User request, verbatim:

> /design Lets add a new package with a static site built in svelte that provides access to effectively a dashboard/analytics for the user workflow stats. The site itself would be static and call workflow apis (in local exposed through `workflow serve`. In local the serve also serves the site, though for remote this would be a cloudflare pages site. 
>
> The site should provide a large number of different views on agent, hook, build/design usage with lenses by repo, trends over time, lenses by analysis type with distributions etc. It should allow filtering and providing different types of reports
>
> If there are out of the box tools for this type of analytics then great use it. If not wrap it up in a svelte site.
>
> Conduct thorough research using subagents for existing tools we can use for this kind of dashboard/analytics view into the workflow data. Examine thoroughly the data workflow contains in the various artifacts and how we can represent that in various ways and what the different lenses are. Then produce a comprehensive design to build the solution

## Why This Existed

`workflow serve` held the tenant ledger (hook events, artifact versions, commits, screens, scores,
rejections), but its only reads were the agent's point lookups. Nothing answered a person's
questions: how agents and hooks are used, how design / brief / report work moves, how scores are
distributed, and how that changes by repo and over time. The constraint was a static site that
calls the live tenant API at view time, served by local serve and deployable to Pages against a
remote serve. Research rejected every off-the-shelf BI tool against that constraint, since each
needs a build-time snapshot or a second always-on server. Only Perspective (a static WASM pivot) and
LayerChart (Svelte charts) were adopted, inside a SvelteKit site.

## What Was Built

Three phases, nine units, all with Sonnet workers under an Opus orchestrator.

**Changed:** `tools/workflow/internal/serve/` (`serve.go`, new `analytics.go`, `site.go`, `site/`
placeholder, tests), `tools/workflow/internal/store/` (new `analytics.go`, a `facts_ts` index
migration, tests), `tools/release/` (`build.sh`, `test_release.py`), new `packages/workflow-analytics/`,
`docs/design/03-remote-service.md`, `docs/design/system-architecture.md`, new
`docs/design/07-analytics-site.md`.

### Phase 1 — Analytics reads

Store queries (`Facets`, `Summary`, `Series`, `WindowScores`, `Executions`, `Conversations`,
`Explore`) with `wf_kind`/`wf_plan` SQLite functions deriving kind and plan from paths, and seven
handlers with a shared filter parser and an opaque base64url cursor bound to route, filters and
resolved window. CORS middleware runs after `localGuard`: loopback origins in local mode, an exact
`WORKFLOW_SERVE_CORS_ORIGINS` allowlist in keyed mode, allowed `OPTIONS` answered 204 before auth.
Verified live with a seven-fact fixture posted through ingest (22/22 assertions).

### Phase 2 — Report views

SvelteKit with adapter-static, an API client honouring the stored base URL and token, URL-held
filters with a facet-driven filter bar, the overview, `/trends`, `/repos`, `/hooks` (LayerChart),
`/quality` (window percentiles beside `/v1/baselines`), `/executions` and `/conversations` (cursor
pager), `/explore` (Perspective loaded only on that route, capped-slice banner) and `/settings`. A
bundle check fails the build if a tenant key or token appears in the output. A Playwright suite runs
against local and keyed serves seeded with a fixture (26 tests).

### Phase 3 — Local serve hosts the site

`site.go` embeds `all:site` and serves it with SPA fallback and the cache rules; a committed
placeholder keeps `go test` Node-free and makes a placeholder build answer JSON 404. `build.sh`
builds the site, copies it in, cross-compiles the four targets and restores the placeholder on exit.
`wrangler.toml` declares the Pages output. A hosted Playwright spec (`npm run test:hosted` with
`WORKFLOW_BIN`) proves a release binary serves the overview same-origin with no token, survives a
refresh on `/quality`, caches immutable assets, keeps `/v1` JSON, and loads Perspective's WASM from
the binary.

## Deviations

- Executions are one row per brief, not per conversation, so a conversation with one reported brief
  of several is not counted complete. This was a design ledger choice made explicit at build.
- Nested brief paths (`briefs/<dir>/<file>.md`) have no kind and are not executions, matching
  `keys.Kind`; they count under summary `other`.
- `/quality` renders distributions as a table, not a chart (the brief allowed it).
- `@perspective-dev/server` was first used only transitively; it was declared as a direct dependency
  in phase 3.
- Feedback-service scoring was missed for phase 2 at its close (server unreachable) and caught up
  at phase 3. Report 2-03 sits below the tenant's p25 on plain problems and named departures. One
  phase-1 report never reached the service.

## Review

`PASS_WITH_FOLLOWUPS` from two independent reviewers, one on the Go and release side, one on the site.
No blocker or high findings. Fixed during review:
- trend lines now zero-fill the sparse series instead of drawing across empty days
- a non-JSON `/v1` response (a static host with no base URL configured) is now a connection error pointing at `/settings`
- facets now refetch only when the window changes
- keyed-mode 401 is tested on all seven analytics routes
- the release test asserts each binary embeds the built site

All of these were re-verified against a freshly built release binary: Go tests, unit tests 11/11, e2e 26/26, hosted 6/6.

## Residual Risks

- Paging and aggregation speed on a large tenant are unmeasured.
- The browser token in `localStorage` is as powerful as the tenant key and is readable by any script
  on the Pages origin, which the design accepts. There is also no anti-framing header yet.
- Charts are verified only through their tables.
- Perspective's viewer has an opt-in LLM-chat feature that could send explore rows to a third party
  if a user supplies a key.
- `build.sh`'s missing-Node branch and its trap under signals are unexercised.

## Follow-ups

All non-blocking follow-ups are recorded in [design 7, Open issues](../design/07-analytics-site.md#open-issues). None were filed in a tracker. The one that needs a decision first: precheck rejections vanish under any `repo_id` or `harness` filter, because their rows carry no repo. Someone must decide whether a rejection belongs to a repo before it can be fixed.

## Decisions Worth Keeping

- Aggregate in SQLite and ship JSON aggregates plus one capped slice. Do not use a browser query engine (DuckDB-WASM) or a hosted BI server.
- The URL query is the report. A saved-report store waits for user identity in the ledger.
- The execution view is computed at read time, not materialised on ingest. Design 3 now says so.
- A committed placeholder with a marker keeps the Go build Node-free. The marker also lets the
  binary refuse to pretend it hosts a site it doesn't have. The release build is the only path that
  embeds the real site.
- Analytics is person-facing HTTP and was never added to the MCP surface.
