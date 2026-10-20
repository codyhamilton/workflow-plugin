# Analytics dashboard redesign

## Intent

User request, verbatim:

> The analytics dashboard needs a total redesign. We did have a prior plan to do this but it was too conservative. To be clear, just about everything needs replacing. The UI is cumbersome, the layout and styling not usable. We'd need a few passes over this, redesigning the style and component system, rethinking the dashboards and data layouts. I'd like to see landing dashboard with a good quick view into trending data, I'd like the graphs and visualisations to be rich and dynamic and interactive. Also a minor thing if the user isn't logged in just direct straight to login.
>
> create a thorough design to rethink the UI. Keep the changes just to the analytics dashboard package

## Problem

The dashboard is `packages/yakka-analytics`, a static SvelteKit client. Plan 14 already shipped a pass over it. The close-out record is `docs/plans/14-analytics-ui.md`. The signed design is git `2bc26e0` (`docs/plans/14-analytics-ui/DESIGN.md` at that commit). Its provenance keeps the current route set and ECharts: "the request is about those pages, not a new information architecture." The only structural UI change was dashboards, from iframes to in-document tiles. Phases `analytics-ui:1` through `analytics-ui:5` are done. That is the conservatism this request replaces.

What a person gets today is that information architecture. The shell in `src/routes/+layout.svelte` is a header, a theme switch, and a nav of report routes (`/`, `/trends`, `/builder`, `/usage`, `/repos`, `/hooks`, `/quality`, `/executions`, `/conversations`, `/explore`, `/dashboards`), then `FilterBar`, `FilterChips`, `Notices`, and `SaveView` on every report. Color is the solarized sheet `src/lib/theme.css`. Charts are ECharts option builders under `src/lib/charts/`. Each report page assembles its own analytics requests. Saved views in `src/lib/views.ts` store a report id plus that page's chart params. `/` is KPI tiles, sparklines, grouped counts, and a weekday-by-hour heatmap. A time series the person configures is `/trends`, which asks for a metric first.

A person who is not logged in is not sent to login. The package has no load guard and no navigation to `/login`. After a failed fetch the layout shows an error panel with a Sign in link. `docs/design/07-analytics-site.md` (Site) already says that on the collector an unauthenticated analytics `GET` is 401 and the layout sends the browser to `/login`. The package does not do that send.

The package does not import another workspace package. JSON aggregates are served from `packages/yakka`. This redesign stays inside `packages/yakka-analytics`.

## Solution Shape

`packages/yakka-analytics` becomes a different dashboard. After the document loads, a collector entry with no session is on `/login`. Screens are composed from a new analysis-first component and style system. Landing and investigation read through one aggregation boundary the package owns, which can express a trend window and the breakdowns those views need. A logged-in user opening `/` sees trending data for a window they did not configure. From that view they investigate with interactive graphs. Usage, cost, quality, conversation grain, and saved analysis return as exploration tools in that investigation, in a new information architecture.

Five domains, all inside the package. The package owns the code. Each domain owns the contract under its name.

Handoffs a later brief can cite:

- The session gate allows a dashboard screen to mount. It does not load aggregates and it does not draw charts.
- The component and style system supplies frame, type, color, space, and the chart frame. Landing and analysis pass data and handlers in. They do not own color or chart styling.
- The aggregation boundary answers a query. Landing and analysis do not call analytics HTTP themselves.
- The landing view hands the investigation the window on screen and the trend it showed. The investigation is not the first screen.

### Domain: Session gate

- Owns: whether a document load in the package may show the dashboard. Surfaces: `src/routes/+layout.svelte`, `src/routes/+layout.ts`, `src/lib/api.ts` (`fetchMe`, `isCollectorMode`, `oauthLoginPath`), `src/routes/login/+page.svelte`, `src/routes/oauth/callback/+page.svelte`, `src/routes/device/+page.svelte`. Identity and connection screens stay in the package and are not analysis: `src/routes/profile/+page.svelte`, `src/routes/settings/+page.svelte`.
- Contract: after the document loads, a remote collector with no session navigates to `/login`, and a local serve whose analytics reads succeed stays on the dashboard.
  - **Document load** means the static document has been served and the package script has started. `src/routes/+layout.ts` sets `ssr = false`. The gate runs after that. It is a client navigation to `/login`.
  - **Sign-in flow** is `/login` and `/oauth/callback`. Those two routes stay put when there is no session.
  - **Collector, no session.** On a remote collector, an analytics `GET` with no session is 401 (design 7, Site). Opening any package route other than the sign-in flow in that condition ends on `/login`. The person does not activate a link. Collector mode is the mode `isCollectorMode()` already names: stored base empty, or its origin `https://api.yakka.build`, or the page host a Pages host.
  - **Local serve stays on the dashboard.** Local mode authorizes ledger reads for tenant `local` with no session (design 7, Analytics reads; design 3). `GET /v1/me` is 401 with no session even then. The gate must not treat that `/v1/me` 401, by itself, as the collector-unauthorized case. When analytics reads succeed, `/` stays the dashboard.
  - **Other refusals stay on their current destination.** HTTP 403 `no such tenant` is the profile path. A 401 or network failure that is not the collector session refusal, and a non-JSON `/v1` response, is the settings path (design 7, Site).
  - The `/login` URL carries `return` set to the path and query that were opened. The GitHub link on `/login` passes that `return` through `oauthLoginPath`. The login page today does not pass one.
- Non-goals: an HTTP redirect before the document is painted. That would be `packages/yakka/internal/serve/serve.go`, which is outside the package. A flash of the document before the client navigates is accepted. Reworking GitHub OAuth, the session cookie, or token issuance. Those stay in `packages/yakka`.

### Domain: Component and style system

- Owns: the visual language every screen in the package is built from. The old language is `src/lib/theme.css` (solarized tokens, design 7 Theme), the report chrome in `src/routes/+layout.svelte` (`FilterBar`, `FilterChips`, `SaveView`, the report nav), and the ECharts frame in `src/lib/charts/` (`EChart.svelte` and the option builders).
- Contract: a screen takes its layout, color, and chart frame from this system, and a library may implement the frame without being named here.
  - A screen is a composition of this system: a **frame** (regions for the view and for sign-in, identity, and connection), **type, color, and space** tokens, and a **chart frame**.
  - The chart frame renders a series, a breakdown, a distribution, or a score band. The view supplies the data and the handlers for hover, brush, and drill. The frame does not fetch.
  - A screen this redesign adds takes its layout, color, and chart frame from this system. It does not take them from `src/lib/theme.css`, from `FilterBar` / `FilterChips` / `SaveView` / `DashboardTile`, or from `src/lib/charts/`.
  - Color tokens are not the solarized hexes design 7 lists (`#002b36`, `#fdf6e3`, `#839496`, `#657b83`, and that series palette). A light/dark/system preference may remain. If it does, it switches this system's color.
  - `/login`, `/profile`, `/settings`, `/device`, and `/oauth/callback` use the same system, so the package has one visual language. Their jobs stay: GitHub sign-in, identity and tenant and tokens, API base and bearer, device grant.
  - A library may implement the chart frame or the tokens. This design names no library and no version.
- Non-goals: a shared UI package outside `packages/yakka-analytics`. Matching an external visual reference (none was given). Restyling the current report pages onto the solarized sheet. Keeping ECharts as the chart grammar because plan 14 did.

### Domain: Aggregation boundary

- Owns: the only read API the landing view and the analysis views call. The HTTP client it may use is `src/lib/api.ts`. The query, window, and row types it replaces as the views' source of truth are `src/lib/query.ts`, `src/lib/params.ts`, `src/lib/types.ts`, and the per-page fetches coordinated by `src/lib/view.svelte.ts`. Session routes (`GET /v1/me`, tenants, tokens) stay on `src/lib/api.ts` and are not this boundary.
- Contract: one request, one result. Callers do not name `/v1/analytics/*` or `GET /v1/baselines`.

  Request:

  - `window`: `{ from, to }` as RFC3339, and `tz` as an IANA name. A preset may be passed instead of `from`/`to`. Preset names are the ones the package already has: Today, 24h, 7d, 30d, 90d, This month, YTD, All time (`src/lib/presets.ts`). Omitted range resolves as design 7 Shared filter: `to` now, `from` thirty days earlier. That thirty-day span is design 7's labelled judgement.
  - `filters.include` and `filters.exclude`: repeatable values of `repo_id`, `harness`, `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`. The server has no exclude parameter. The boundary applies an exclude. An exclude on `conversation_id` stays unsupported and is reported on the result, which is the current client rule.
  - `ask`, one of:
    - `trend`: a measure, a bucket (`hour`, `day`, `week`, `month`), optional one breakdown dim
    - `breakdown`: a measure and one dim, no time bucket
    - `distribution`: a measure, grain `call` or `conversation`, optional dim `model`
    - `quality`: artifact kind `design`, `brief`, or `report`, and bucket `day`, `week`, or `month`
    - `conversations`: the conversation list for the window
    - `conversation`: one id
    - `executions`: the derived execution shape for the window (counts, and the shape series when a bucket is set)

  Measures and dims are the set design 7 already serves (`/v1/analytics/schema` for query measures; distribution measures `cost_usd` and the token measures; quality kinds as above). The boundary does not invent a measure the server cannot answer. It may call the existing reads, compose several of them, or aggregate in the client from data the package loaded. A library is allowed for that aggregation. No library is named here.

  Result: the slice the `ask` needs (points, rows, bins, score band and baseline, conversation rows, or one run), the resolved `window`, and `partial`, `ignored_filters`, and `truncated` when the read produced them. A window the server clamps (the 399-day client clamp, the 400-bucket refusal) is visible on the result. The boundary does not present a clamped window as complete. Field meanings for those signals stay the ones design 7 gives the underlying read. A view does not branch on which URL answered.

- Non-goals: new or changed routes in `packages/yakka/internal/serve`, new tables in `packages/yakka/internal/store`, ingest changes, and a server-side store of saved analyses.

### Domain: Landing trend view

- Owns: the first screen a logged-in user sees, at `/` (`src/routes/+page.svelte`). It is the entry the package already uses. It is not the current overview on that route.
- Contract: `/` with an empty query string shows a trend for the preselected window, read through the aggregation boundary and drawn in the chart frame.
  - The gate has allowed the load. The query string is empty. A trend over the preselected window is on screen. The person does not choose a measure, a chart type, or a saved analysis first.
  - The trend is values over time, read with `ask: trend` on the aggregation boundary, drawn in the chart frame.
  - **Judgement:** the unconfigured trend shows hook-event volume (`hook_events`) and cost (`cost_usd`) on that window. Those two stand in for activity and spend. The set is a judgement, not a measured catalogue. Nine KPI tiles are not required.
  - The picture is this trend. It is not the current `/` content: the nine KPI tiles, the grouped counts, and the weekday-by-hour heatmap.
  - From this view the person can open an investigation. The handoff is the window on screen and the measures the trend showed.
- Non-goals: a report the person must configure before any trend is visible. A grid of saved tiles as the landing page.

### Domain: Interactive analysis

- Owns: the investigation opened from the landing view. The jobs that return are usage, cost, quality, conversation grain, and saved analysis. Old report modules this replaces: `src/routes/usage/+page.svelte`, `src/routes/quality/+page.svelte`, `src/routes/conversations/+page.svelte`, `src/routes/conversation/+page.svelte`, `src/routes/dashboards/+page.svelte`, `src/routes/builder/+page.svelte`, `src/routes/trends/+page.svelte`, `src/routes/repos/+page.svelte`, `src/routes/hooks/+page.svelte`, `src/routes/executions/+page.svelte`, `src/routes/explore/+page.svelte`, plus `src/lib/views.ts`, `SaveView`, and `DashboardTile`.
- Contract: the investigation opened from the landing view updates its graph from the aggregation boundary, and usage, cost, quality, conversation grain, and saved analysis are tools inside it.
  - The person reaches the investigation from the landing view. It opens on the landing's window and measures.
  - The graph is interactive. Changing the window (a preset, or a brush on a time axis) and changing a breakdown dim ask the aggregation boundary again, and the graph updates from that result. Drill applies a real filter dim. `__other__`, the empty key, `hour_of_day`, and `weekday` are not filters (design 7, Drill-down). Shift-click excludes where the boundary can express an exclude.
  - The live investigation serialises into the query string: window, filters, and `ask`. Pasting that URL reproduces the investigation. The keys are the boundary request, not the old per-page keys (`metric`, `group`, `m`, `d`, `b`, `c`, and the report path).
  - **Usage and cost** are one tool. Model against model, tokens and `cost_usd`, over time (`ask: trend` with dim `model`) and as a distribution (`ask: distribution`, grain `call`). Unpriced cost is shown as unpriced, not as zero (design 7, Cost).
  - **Quality** is one tool. One kind `design`, `brief`, or `report`: the window score distribution beside the all-time baseline, and the score series for the bucket (`ask: quality`). A bucket with no point is a gap.
  - **Conversation grain** is one tool. The window's conversations (`ask: conversations`), with model and cost on the row, and one run (`ask: conversation`): the event list is the whole run, events inside the window are marked, `totals` is the run, and `window_totals` is present when a window is set (design 7, conversation read).
  - **Saved analysis** is one tool. The person saves the investigation and opens it again by name. Stored record: `{ id, name, spec }` where `spec` is the boundary request that reproduces it (the `ask`, the window, and the filters). It is not `{ report, params }` with `report` one of `overview`, `trends`, `usage`, `repos`, `hooks`, `quality`, `executions`, `conversations`, `explore`, `builder`. Persistence is client-side (`localStorage`). There is no server view store. Opening one stays inside the investigation.
  - Repo, harness, hook (`norm_event`, `event`, `tool`), and execution shape (`ask: executions`) are breakdowns inside the same investigation. They are not destinations.
- Non-goals: porting the old pages. A `/usage`, `/quality`, `/conversations`, `/dashboards`, or `/builder` screen that is the current page with new paint. The twelve-tile dashboard grid. An iframe. A dedicated `/explore` pivot page. Perspective is not required. A server-side saved-view store.

## Architectural Implications

- This design supersedes the conservatism of `docs/plans/14-analytics-ui.md`. That close-out stays the record of the pass that finished (`analytics-ui:1` through `analytics-ui:5`, commits `5e4eaa0`, `261a776`, `af13663`, `ee0fd2a`, `2bc26e0`, close-out `4c09438`). This folder does not reopen it.
- `docs/OVERVIEW.md` does not mention the analytics UI. It is the skill loop. This design does not depend on changing it.
- `docs/ARCHITECTURE.md` names `packages/yakka-analytics` in the component map and does not describe routes, data loading, or the visual system. The package boundary does not change, so that map stays.
- `docs/design/07-analytics-site.md` is the contract that still specifies the post-plan-14 site: the route table, the solarized theme, ECharts, per-page reads, the URL as a report view, and `localStorage` dashboards of report ids. A change to routes, to data loading, or to the visual system is not in that doc, nor in `docs/OVERVIEW.md` or `docs/ARCHITECTURE.md`. That is the pivot. Each phase amends the section of design 7 that it changes. The file is a surface of those phases.
- `docs/design/06-*.md` is missing. `docs/design/system-architecture.md` indexes row 6, "Lab and analysis", and there is no file. This design does not depend on it and does not block on it.
- `packages/yakka/internal/serve/serve.go` is out of scope, so the document is still served before the gate runs. Server aggregate routes stay as design 7 states them. The new query contract is the boundary inside the package.
- Hosting stays: static adapter, embedded `yakka serve`, Pages (`wrangler.toml`). The package remains a client SPA.
- Five phases. Refine is not skipped. A design with one phase that one worker could carry would skip refine. This design does not.

## Decisions

Answered in the session, in the requester's words (the turn record is `PROVENANCE.md`):

- Reinvent the current analytical jobs (saved views, quality, cost, usage, conversation grain). They return as exploration tools in a new information architecture, not as a port of the old pages.
- The package may change how it aggregates and loads data. Libraries are allowed.
- No visual reference. The bar is rich analysis: interactive, exploratory, not a static report.
- The package boundary stays `packages/yakka-analytics`. Unauthenticated users go straight to login from inside the package, a client redirect to `/login` after the document loads. An HTTP redirect before paint would require `packages/yakka/internal/serve/serve.go`. That question was asked and not answered. The original package-only constraint decides it, and that file stays out of scope.

Derived so phase 1 stays checkable against the ledger the package already runs:

- Local serve, where analytics reads succeed with no session, is not an unauthenticated collector entry. `GET /v1/me` 401 alone does not send it to `/login`. Rationale: design 7 Analytics reads and the package ground. If wrong, local `/` would also end on `/login`.

## Assumption Ledger

None — see PROVENANCE.md.

## Open Questions

None.

## Phases

Ordered. The count is fixed at sign-off. A phase closes when its outcome is provably true. The union of these outcomes is the acceptance criteria. This design does not skip refine: it is not one phase a single worker could carry.

### Phase 1 — Session gate

- Outcome: On a remote collector with no session, opening `/` loads the document and ends on `/login`, with no click on a sign-in link. Opening any other package route that is not `/login` or `/oauth/callback` ends there too, and the URL carries `return` for the path that was opened. Opening `/login` stays on `/login`. On a local serve, where analytics reads succeed without a session, opening `/` stays on the dashboard. This guards against a logged-out person remaining in the shell, which is what the package does now (an error-panel link, no navigation). Required by the intent sentence "if the user isn't logged in just direct straight to login", and by design 7 Site, which already states the send the package does not perform.
- Surfaces: `packages/yakka-analytics/src/routes/+layout.svelte`, `src/routes/+layout.ts`, `src/lib/api.ts`, `src/routes/login/+page.svelte`, `src/routes/oauth/callback/+page.svelte`, `src/routes/device/+page.svelte`, `src/routes/+page.svelte`. `docs/design/07-analytics-site.md` Site (the send, which the package will then actually do). Not `packages/yakka/internal/serve/serve.go`.
- Approach: known
- Depends on: nothing

### Phase 2 — Analysis component and style system

- Outcome: While logged in, the dashboard shell's layout and color come from the new component and style system. The report nav is not in that shell, and the page background is not the solarized `#002b36` or `#fdf6e3`. `/login` uses the same system. A screen composed for this redesign takes its chart frame from the system, not from `src/lib/charts/`. This guards against another solarized report chrome, which is the plan 14 result the request calls too conservative. Required by the intent: "redesigning the style and component system" and "the layout and styling not usable."
- Surfaces: `src/lib/theme.css`, `src/routes/+layout.svelte`, `src/lib/components/` (`FilterBar`, `FilterChips`, `Notices`, `SaveView`, `DashboardTile`), `src/lib/charts/`, `src/routes/login/+page.svelte`, `src/routes/profile/+page.svelte`, `src/routes/settings/+page.svelte`, `src/routes/device/+page.svelte`, `src/routes/oauth/callback/+page.svelte`, and the component and style system the package adds. `docs/design/07-analytics-site.md` Theme and the route-nav description.
- Approach: known
- Depends on: phase 1

### Phase 3 — Aggregation boundary

- Outcome: A caller asks the package's aggregation boundary for a trend window and a breakdown and receives points or rows, plus `partial`, `ignored_filters`, and `truncated` when the read produced them. The caller does not name an analytics HTTP path. `packages/yakka/internal/serve` gains no analytics route from this phase. This guards against each view keeping its own request fan-out, which is how the current pages load (overview, trends, usage, quality, and conversations each call their own reads). Required by the decision that the package may change how it aggregates and loads data, inside the package boundary.
- Surfaces: `src/lib/api.ts`, `src/lib/query.ts`, `src/lib/params.ts`, `src/lib/types.ts`, `src/lib/view.svelte.ts`, `src/lib/presets.ts`, and the aggregation boundary the package adds. `docs/design/07-analytics-site.md` Data layer. Not `packages/yakka/internal/serve` and not `packages/yakka/internal/store`.
- Approach: known
- Depends on: nothing

### Phase 4 — Landing trend view

- Outcome: A logged-in user opening `/` with an empty query string sees hook-event volume and cost over the preselected window (design 7's thirty-day judgement when `from` is omitted), without choosing a measure, a chart, or a saved analysis. The primary picture is that trend, drawn with the new chart frame from the aggregation boundary. The nine KPI tiles and the weekday-by-hour heatmap are not that picture. Which two measures stand for volume and cost is the labelled judgement in the landing contract (`hook_events`, `cost_usd`). This guards against a first screen that is either the old overview or a chart the person must configure. Required by the intent: "landing dashboard with a good quick view into trending data."
- Surfaces: `src/routes/+page.svelte`, the landing view, the aggregation boundary, the component and style system. `docs/design/07-analytics-site.md` route `/` and the overview-link sentences.
- Approach: known
- Depends on: phases 1, 2, and 3

### Phase 5 — Interactive analysis

- Outcome: From the landing view, the user opens an investigation on that window, changes the window and a breakdown, and the graph updates. Usage and cost (model against model, over time and as a distribution), quality (one artifact kind, against the baseline), conversation grain (the list and one run), and a saved analysis (save, then open again by name) are each available there and show their data. Repo, hook, and execution shape are breakdowns in that same investigation. The address is an investigation URL, not `/usage`, `/quality`, `/conversations`, `/dashboards`, or `/builder`. This guards against those jobs returning as a restyle of the old pages. Required by the intent ("graphs and visualisations to be rich and dynamic and interactive") and by the decision that those jobs return as exploration tools in a new information architecture.
- Surfaces: the route modules and view storage named on the Interactive analysis domain, the landing view, the aggregation boundary, the component and style system. `docs/design/07-analytics-site.md` route table, Drill-down, Chart builder, and Saved views and dashboards.
- Approach: known
- Depends on: phases 2, 3, and 4

## Provenance Notes

Plan 14's provenance at `2bc26e0` is the decision this design reverses: "Routes: keep the current route set. Reimagine what each page shows. Rationale: the request is about those pages, not a new information architecture." And: "Chart grammar: stay on ECharts, with Perspective only on Explore." The close-out's lasting UI change was in-document tiles instead of iframes. The request says that plan was too conservative and that just about everything needs replacing. The alternative of another pass over those pages, on ECharts, in solarized, is rejected.

An HTTP redirect before paint was asked and not answered. It is rejected because the request keeps the change inside the analytics dashboard package, and the redirect lives in `packages/yakka/internal/serve/serve.go`. The client navigates after the document loads. The first paint can still be the document.

No visual reference was given, and no chart library is chosen. The approach of every phase is known because the outcome does not depend on which library implements it. Choosing one is below the phase outcome. Staying on ECharts in order to avoid that choice is the plan 14 constraint, and it is not carried forward. Design 7's "no second chart grammar" sentence is part of the pivot phase 2 amends.

The old pages for repos, hooks, executions, and explore are not ported. Their questions survive as breakdowns the boundary can already ask (`repo_id`, hook dims, `ask: executions`). A free-form pivot page is not a job the request kept. The twelve-tile grid and the `{report, params}` saved-view record are the old dashboard, and they are not the saved-analysis tool.

Identity, connection, and device grant stay. The request reinvented the analytical jobs. The package still has to sign a person in, hold a tenant, and set a cross-origin base.

Server bugs stay server bugs. Conversation `window_totals` stored as whole seconds (`packages/yakka/internal/serve`) and conversation-grain unpriced accounting (`packages/yakka/internal/store`) are outside the package. A conversation view built on those reads still shows them. Presentation bugs on the old tiles and report pages go away with those surfaces. They are not a work list here.

Phase 2 replaces the shell. Old report URLs may still resolve until phase 5. Phase 5 is when the investigation is the way those jobs are reached. Finishing at phase 2 would be the conservative restyle this design refuses.
