# Analytics Dashboard Overhaul

## Intent

User request, verbatim:

> significant improvements to the workflow UI. Greatly improve performance, filtering options, interactivity and UI / UX. It needs an overhaul into a modern dashboard with advanced graphs and drill down. Some filtering is very slow, large data sets taking tens of seconds and missing quick date range selection 
>
> Also provide more analytical  configurable multi dimension graphs. Create the design

## Problem

The analytics site ([design 7](../../design/07-analytics-site.md)) is too slow to use on a real ledger. Its interaction model is also too thin for the questions people ask of it.

**Volume.** The local ledger holds 7.6M facts in 9.35 GB, and about 5.9 GB of that is raw hook payload:

| Event | Rows | Raw size |
|---|---|---|
| OpenCode `message.part.delta` (one row per streamed token, since about 2026-10-05) | 7.46M | 4.0 GB |
| `message.part.updated` | — | 320 MB |
| `experimental.chat.system.transform` (the full system prompt on every request) | — | 302 MB |
| `tool.execute.after` | — | 280 MB |
| `chat.params` and `chat.headers` | — | 280 MB together |

Nothing downstream reads the bulky OpenCode bus events by name. Their only reader is the analytics site's counts. `chat.headers` and `shell.env` carry request headers and environment variables. So the ledger is mostly bodies that nobody queries, and some of them should never have been stored.

**Read path.** Every request re-aggregates the raw window:
- `tool`, `source` and `sha` are parsed from JSON on every row.
- `kind` and `plan` are Go SQLite functions evaluated per row, inside `WHERE`.
- Conversations streams every in-window row into Go.
- Executions and Conversations page in Go.
- Explore sorts the whole window before its `LIMIT`.
- Nothing is cached.

Filter changes take tens of seconds.

**Missing data.** Model, token and cost data reaches the ledger:
- Claude `transcript.assistant_message` carries `model` and `usage`.
- Codex `transcript.token_count` carries `model` and `usage`.
- OpenCode `transcript.assistant_message` carries `modelID` and `cost`.

Design 7 excludes these fields and no code extracts them.

**Site.**
- Filter changes refetch immediately, with no debounce, cancellation or cache.
- `/repos` fans out one request per repo, and `/explore` reloads its slice on every change.
- The window is two date inputs with no presets, and nav links drop the filter query.
- Nothing drills into anything.
- The only charts are LayerChart line and bar, with no tokens and no dark mode.
- No chart can be configured over more than one dimension.

**Missing capability.** Two things asked for have no current equivalent:
- The Intent asks for "advanced graphs", including configurable charts over several dimensions. Nothing the site has today can show flows (design → brief → commit → report), hierarchies (harness → event → tool), time-of-week patterns, or a measure split by two dimensions.
- The user asked for cross-harness comparison (PROVENANCE.md, Turn 5). This needs one event vocabulary shared by all four harnesses. Today each harness names its events differently.

**Constraint.** For some sessions, hook bodies are the only record of the transcript. Taking them out of the ledger must not lose them (PROVENANCE.md, Turn 5).

## Solution Shape

After this change, three things hold for the ledger:
- The ledger stores no hook bodies. It holds envelopes plus the analytics fields extracted at ingest: a normalised cross-harness event, tool, model, token usage and cost.
- Every hook body that is kept is written verbatim to a per-conversation archive on disk, so the original source survives outside the database.
- OpenCode's secret-bearing and redundant bus events are removed at capture and at ingest, and streamed deltas collapse to one row per message part.

An offline command applies the same policy to history and reclaims the space, which takes the ledger from about 9 GB to well under 1 GB.

One generic aggregate endpoint answers any measure × up-to-two-dimension × time-bucket question under 500 ms p95 against the real ledger, including token and cost measures by model. The existing routes are re-served from the same columns.

The site is rebuilt as a dashboard shell on ECharts:
- a global filter bar with quick date presets and brush-to-zoom;
- filters that persist across views;
- cross-filtering and drill-down from every mark down to one conversation's timeline;
- a chart builder for configurable multi-dimension charts;
- named saved views and dashboards in the URL and `localStorage`.

Aggregation stays in SQLite. Local serve and the Pages deployment run the same build.

### Domain: Capture and event policy (`packages/opencode-workflow-hooks`, `tools/workflow/internal/ingest`)

- Owns: which hook events are recorded, in what form, and the normalised event vocabulary.
- Contract:
  - **The policy table.** One table in `internal/ingest` maps `(harness, event)` to `keep`, `collapse` or `remove`. Any pair not listed is `keep`. The OpenCode plugin carries the same `remove` list, and a test asserts the two lists are equal.
  - **`remove`.** Applies to OpenCode `experimental.chat.system.transform`, `chat.params`, `chat.headers` and `shell.env`. The plugin does not forward them. Ingest answers them `accepted` and stores nothing: no fact row and no archive line. This covers older plugins and other clients.
  - **`collapse`.** Applies to OpenCode `message.part.delta` when `payload.event.properties` carries non-empty `messageID`, `partID` and `field`.
    - The stored fact's row hash is computed from `(type, harness, event, conversation_id, messageID, partID, field)` instead of the whole envelope. `INSERT OR IGNORE` therefore keeps exactly one row per part, and a redelivered delta is a `duplicate`. Its `ts` is the first-received delta's.
    - Every delta is still archived.
    - A delta lacking the key fields is `keep`.
    - `facts` stays append-only ([design 3](../../design/03-remote-service.md)).
  - **`keep`.** Every other hook event is stored as an envelope plus extracted fields. Row-hash identity is unchanged: it is computed from the full received envelope, as today.
  - **Normalised event.** Each stored hook event gets a `norm_event`, which is one of these values:
    - `session_start`, `session_end`, `prompt`, `tool_pre`, `tool_post`, `tool_fail`, `batch_end`;
    - `assistant_message`, `usage`, `turn_end`, `subagent_start`, `subagent_end`, `compact`, `message_part`;
    - `other`.

    The mapping per harness is a table in `internal/ingest`, seeded from `tools/hooklog/hooklog.py`'s kinds. The native `event` is kept beside it.
  - **Model and usage extraction.** Fields are extracted where the payload has them:

    | Harness | Source | Fields |
    |---|---|---|
    | Claude | `transcript.assistant_message` | `model`, `usage.{input,output,cache_read_input,cache_creation_input}_tokens`, `output_tokens_details.thinking_tokens` |
    | Codex | `transcript.token_count` | `model`, `usage.{input,cached_input,output,reasoning_output,cache_write_input}_tokens` |
    | OpenCode | `transcript.assistant_message` | `modelID`, `providerID` (model as `provider/model`), and `cost` as a harness-reported cost |
    | Cursor | — | nothing |

    One model call is counted once. A fixture test per harness compares extracted totals to `tools/transcript/parsers` (Claude) or hand totals.
- Non-goals:
  - capturing new events;
  - Cursor usage;
  - changing the spool or queue format;
  - normalising tool names across harnesses.

### Domain: Event archive (`internal/store`, new archive package)

- Owns: the on-disk record of received hook bodies.
- Contract:
  - **Layout.** `<tenant dir>/archive/<YYYY-MM>/<conversation_id>.jsonl.zst`, one file per conversation per UTC month of fact `ts`. Each line is `{"row_hash","received_at","fact":<canonical received fact JSON>}`. The archive holds every received `keep` and `collapse` hook event, verbatim and after secret redaction. It holds no `remove` event and no artifact content (that stays in the pending/content store).
  - **Delivery.** Archiving is at-least-once. Ingest appends to the archive before it commits the fact rows, so a redelivered event can appear twice, and readers deduplicate by `row_hash`. For collapsed deltas each line carries the delta's own envelope hash, not the part hash.
  - **Read access.** A store function reads one conversation's archive lines in time order. This design exposes no HTTP route for it (see Non-goals); it exists for transcript tools and a later design.
- Non-goals:
  - serving bodies over HTTP;
  - full-text search;
  - archive retention or expiry;
  - replicating the archive off the tenant host.

### Domain: Ledger shape and compaction (`internal/store`, `workflow` CLI)

- Owns: the `facts` columns, the indexes, the migration, and the offline compaction.
- Contract:
  - **Stored hook facts.** A hook-event fact's stored `raw` is its envelope (`type`, `harness`, `event`, `conversation_id`, `ts`, `repo_id`) with no `payload`. The row hash is unchanged (see above). `artifact_version` and `commit` facts keep their full `raw`.
  - **New columns on `facts`.**
    - `norm_event`, `tool` and `model`;
    - the artifact `kind` and `plan`;
    - `source` and `sha`;
    - `tok_in`, `tok_out`, `tok_cache_read`, `tok_cache_write`, `tok_reasoning`, `cost_reported`.

    All are filled at insert. `rejections` gains an index on `at`. `facts` gains `(type, ts)` and `(ts, harness, norm_event)` indexes; refine may adjust indexes against the benchmark.
  - **Schema migration.** It runs inside `Open()`, as today, and is `ADD COLUMN`/`CREATE INDEX`-cheap only. It never rewrites rows, so serve on an uncompacted ledger starts as fast as today.
  - **Compaction command.** `workflow ledger compact --tenant-dir <dir>` is offline and resumable. It runs when it can take an exclusive lock on the tenant dir; serve takes the same lock shared and refuses to start while compaction holds it. In one pass over existing hook facts it:
    1. archives each body;
    2. applies the policy table: `remove` rows are deleted with no archive line, and deltas are collapsed into one row per part using the collapse identity;
    3. strips the payload and fills the new columns;
    4. records completion in a store meta key.

    Then it runs `VACUUM`. Before it starts it prints the free space it needs and refuses if that space is not available. It reports rows and bytes before and after.

    These deletes and rewrites are the one sanctioned exception to append-only. Design 3 records it.
  - **Uncompacted ledgers.** Until compaction completes, `/v1/health` reports `"compaction":"required"` and analytics responses carry `"partial": true`.
- Non-goals:
  - online compaction inside serve;
  - re-deriving historical facts that were never captured.

### Domain: Analytics reads (`internal/serve/analytics.go`, `internal/store/analytics.go`)

- Owns: the `/v1/analytics/*` HTTP contract. Design 7's routes, auth, CORS and error shapes carry over unless stated below.
- Contract:
  - **Shared filter.**
    - New repeatable keys: `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`. The OR/AND rules are as in design 7.
    - New `tz` (IANA name, default `UTC`), used for bucket boundaries and the `hour_of_day`/`weekday` dimensions.
    - `all=1` replaces `from` and means the whole ledger.
    - The 400-bucket cap applies per bucket unit.
    - A filter on a dimension the requested measure does not carry is ignored, and that key is listed in `ignored_filters` in the response. This replaces design 7's silent drop to zero (its open issue 1, for `repo_id` and `harness`, which rejections do not carry).
  - **`GET /v1/analytics/query`.** Parameters:
    - `measure`, required;
    - `dim`, 0–2 times;
    - `bucket`: `none` (default), `hour`, `day`, `week` (ISO Monday) or `month`;
    - `top`: default 20, max 100. It ranks each dimension's keys independently by the measure's total over the window. Keys outside the top N fold to `"__other__"`, which is not a valid filter value.

    Responses are capped at 20,000 rows, with `truncated`. The response is `{"measure","bucket","dims":[…],"rows":[{"t"?,"k":[…],"v"}],"ignored_filters"?,"partial"?}`. Rows are sparse, and `t` is RFC3339 in `tz`. An unsupported measure × dimension pairing is 400 `{"error":"unsupported dimension <d> for <measure>"}`.
  - **The measure × dimension matrix.** It is served verbatim at `GET /v1/analytics/schema` as `{"measures":[{"name","unit","dims":[…]}],"buckets":[…]}`. Every measure also takes `hour_of_day` and `weekday`.

    | Measure | Dimensions |
    |---|---|
    | `hook_events` | `harness`, `repo_id`, `norm_event`, `event`, `tool`, `conversation_id` |
    | `conversations` (distinct) | `harness`, `repo_id`, `model` |
    | `artifact_versions`, `distinct_content` | `harness`, `repo_id`, `kind`, `plan`, `source`, `conversation_id` |
    | `commits` | `harness`, `repo_id`, `conversation_id` |
    | `rejections` | `stage` |
    | `model_calls`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`, `cost_usd`, `unpriced_calls` | `harness`, `repo_id`, `model`, `conversation_id` |
  - **Cost.** `cost_usd` is computed at read time. It is the call's `cost_reported` when present. Otherwise it is tokens × the model's price in a pricing table that serve embeds, generated from `tools/transcript/pricing.json` (a test asserts the two are equal). A call with neither counts in `unpriced_calls` and adds 0. Repricing needs only a new binary.
  - **Existing routes.** `facets`, `summary`, `series`, `scores`, `executions`, `conversations` and `explore` keep their request and response shapes. They read the new columns and gain the new filter keys. The documented count changes:
    - `hook_events` counts a collapsed part once;
    - removed events disappear;
    - `summary` gains `model_calls`, `cost_usd` and `tokens_*`;
    - `facets` gains `models` and `norm_events`.
  - **Paging.** Executions and conversations page in SQL by keyset. Explore applies its cap without sorting the whole window first. Explore columns gain `norm_event`, `model` and `cost_usd`.
  - **`GET /v1/analytics/conversation`** (`id` required). It returns `{"conversation_id","harness","repos","models","first_ts","last_ts","totals":{tokens…,cost_usd},"events":[{"ts","type","norm_event","event","tool","model","path","kind","source","sha","tokens"?,"cost_usd"?}]}` in time order, capped at 5,000 events with `truncated`. It returns no bodies.
  - **Rollups are conditional.** Performance comes first from the slimmed ledger, the columns and the indexes. An hourly rollup table is added only for measures that miss the bound. If one is added, a store test asserts that rollup aggregates equal base-row aggregates over a fixture, and windows that are not hour-aligned read their edge hours from base rows.
  - **Performance bound.** A committed benchmark runs against a compacted copy of the local ledger. It covers every route, each preset (24h, 7d, 30d, 90d, all time), every measure with 0, 1 and 2 dimensions, and every bucket within the cap. Every case is under 500 ms p95. The benchmark is runnable against any ledger path.
- Non-goals:
  - ETag/HTTP caching (the ledger changes every few seconds);
  - SQL or expression input;
  - writes;
  - user identity;
  - changes to `/v1/baselines` or MCP.

### Domain: Dashboard site (`packages/workflow-analytics`)

- Owns: every person-facing view, the URL view-state format, saved views, and the client data layer.
- Contract:
  - **The URL is the view.** Filters, the window, the active view and every chart configuration (measure, dims, bucket, chart type, top) serialise into the query string. Pasting the URL reproduces the view. Filters survive navigation between views.
  - **Date window.**
    - Presets: Today, 24h, 7d, 30d, 90d, This month, YTD, All time.
    - A custom range picker.
    - Brush-to-zoom on any time-axis chart.
    - Presets stay relative in a shared URL. Times display in the browser's zone, which is sent as `tz`.
    - Each chart picks the finest bucket within the cap unless one is set.
  - **Data layer.** One client module issues every request. It debounces filter changes (≤ 250 ms), aborts superseded requests, and caches responses for the session by normalised query. The UI never renders a superseded result. It shows `partial` and `ignored_filters` as notices.
  - **Drill-down.**
    - Every chart mark and table row for a dimension value applies that value as a filter (shift-click excludes it). `__other__` is not clickable.
    - Active filters show as removable chips.
    - Any conversation ID opens the conversation timeline, and counts link to the filtered explore slice.
  - **Views.**
    - Overview: KPI tiles with sparklines, including cost and tokens; an hour-of-day × weekday heatmap.
    - Trends.
    - Usage & cost: tokens and cost by model, harness and repo, plus the cost trend.
    - Repos.
    - Hooks: harness → `norm_event` → tool treemap.
    - Quality: distribution charts beside the baseline.
    - Executions: design → brief → commit → report sankey plus table.
    - Conversations: virtualised.
    - Conversation timeline.
    - Explore: Perspective.
    - Chart builder.
    - Dashboards.
    - Settings.
  - **Chart builder.** It is driven only by `/v1/analytics/schema`: any measure, up to two dimensions and a bucket. Chart types are line, stacked area, stacked/grouped bar, heatmap, treemap and small multiples, offered only where the shape fits. An unsupported pairing cannot be selected.
  - **Saved views and dashboards.** A named saved view is a stored URL. A dashboard is an ordered grid of saved views, which can be exported and imported as JSON. Both live in `localStorage` under the prefix `workflow-analytics-views`.
  - **Charts and theme.**
    - Charts render with Apache ECharts, tree-shaken, and LayerChart is removed.
    - Colours come from one token set, with light and dark themes following the system preference.
    - Each chart has a data-table toggle.
    - The site works down to 1024 px wide.
  - **Unchanged from design 7.** The `/settings` base URL and token behaviour, the non-JSON connection error, the bundle-key check and the static build output carry over.
- Non-goals:
  - a server-side saved-view store;
  - a SQL editor or BI shell;
  - showing archived bodies;
  - alerting;
  - narrow mobile layouts.

## Architectural Implications

- **[Design 7](../../design/07-analytics-site.md)** is rewritten at close-out. These parts change:
  - filters and `ignored_filters`;
  - the `query`, `schema` and `conversation` routes, and the matrix;
  - the token, cost and model fields, which reverses design 7's exclusion;
  - count semantics;
  - ECharts replacing LayerChart;
  - saved views;
  - the view list.

  Open issues 1, 2, 7 and 8 close.
- **[Design 1](../../design/01-event-model-and-ingest.md)** gains three things: the event policy (keep, collapse, remove), the normalised event vocabulary, and "model and cost where the payload has them", which is now implemented. A fact's stored `raw` no longer holds hook bodies; they live in the archive.
- **[Design 3](../../design/03-remote-service.md)** gains:
  - the new `facts` columns and the archive directory;
  - the tenant-dir lock;
  - the compaction exception to append-only;
  - the collapse row-hash rule.

  Remote tenants run the same code. An operator runs `workflow ledger compact` on a remote tenant during a maintenance stop.
- **[Design 2](../../design/02-edge-capture.md)** and `packages/opencode-workflow-hooks/README.md`: the plugin no longer forwards every bus type. It drops the `remove` list.
- **`tools/hooklog`** reads the local spool, not the ledger. Its kinds are unaffected, because the removed events have no hooklog reader.
- **Ordering.** Phase order follows dependency. The performance bound only holds on the compacted ledger. The site's new views need `query`, `schema` and `conversation`. The usage views need the token columns from Phase 1.

## Decisions

- Performance starts with collapsing OpenCode deltas at ingest, then removing or stripping bulk (user: "the chunk events are the main one, can these be collapsed … should be done on ingest, then rollup"). Rollups are built only where the benchmark shows they are needed.
- A collapsed part counts as one hook event. There is no chunks measure, so redelivery is exactly idempotent through the row hash.
- OpenCode `experimental.chat.system.transform`, `chat.params` and `chat.headers` are removed (user: "Definitely remove those opencode system, chat params/headers"). `shell.env` joins them because it carries environment secrets.
- The database stores no hook bodies. The original bodies are kept verbatim on disk (user: "drop bodies for analytics, but separately store full transcripts … on disk. So original source is kept somewhere, just not in db").
- Standard events are normalised across harnesses (user: "keep standard events we can normalise across harnesses and are useful").
- The policy is enforced at ingest and in the OpenCode plugin.
- Model, token and cost fields become measures where they are available (user: "yes I want model/token/cost fields for sure where they are avaialble"). This reverses design 7's exclusion.
- History is compacted in place and the space is reclaimed, by an offline command rather than a background job, so serve startup and ingest are never blocked.
- Charts use Apache ECharts. Views persist as URL state plus `localStorage`. The closing bound is p95 < 500 ms. All phases are approach-known.

## Assumption Ledger

None — see PROVENANCE.md.

## Open Questions

Each question below is answered during build by a measurement. None of them changes the phase count or order.

1. **Are rollups needed?** The Phase 3 benchmark answers this.
   - If no measure misses the bound, no rollup table is built.
   - If one does, the rollup contract under Analytics reads applies, and the Phase 3 surfaces gain a rollup table in `internal/store/store.go`.
   - This blocks only the close of Phase 3.
2. **What share of deltas lack the collapse key** (`messageID`, `partID`, `field`)? Phase 1 measures it on the local ledger before the policy table is fixed.
   - If the share is more than 1%, collapse needs a fallback key before Phase 2 runs.
   - This blocks Phase 2.
3. **How large is the compacted ledger?** The 1.5 GB figure in Phase 2 is an estimate, not a measurement (see that phase).
   - Phase 2 reports the real figure.
   - A miss is advisory. Phase 3's latency bound is the gate that matters.

## Phases

Each criterion is tagged with where it comes from:
- **[user]**: the user chose it in the design conversation (see PROVENANCE.md).
- **[measured]**: it derives from a measurement recorded in Problem or PROVENANCE.md, Turn 4.
- **[judgement]**: an estimate or a convenient default. A breach of a judgement number is advisory, not a failed phase.

### Phase 1 — Event policy, archive and slim ingest

- Outcome: With an updated binary, the shared fixture batch is posted to `POST /v1/facts`. The batch contains, for every harness, removed, collapsible (including redelivered deltas) and kept events, plus usage events.
  - Removed events return `accepted` and leave no fact and no archive line.
    - Guards against secrets from `chat.headers` and `shell.env` reaching any store.
    - [user] Turn 5, plus the secret risk recorded in Problem.
  - The deltas of one part leave exactly one fact, and resending the batch returns all `duplicate`.
    - Guards against the 97% delta volume coming back, and against double counts on at-least-once redelivery.
    - [user] Turn 1/Turn 3; [measured] 7.46M rows.
  - Every kept or collapsed event has a verbatim archive line under `archive/<YYYY-MM>/<conversation_id>.jsonl.zst`.
    - Guards against stripping bodies destroying the only copy of the source.
    - [user] Turn 5: "original source is kept somewhere".
  - No stored hook fact's `raw` contains `payload`.
    - Guards against the ledger regrowing with bodies.
    - [user] Turn 5.
  - `norm_event`, `model` and the token columns equal the fixture's expected values. The per-harness usage totals match `tools/transcript/parsers` (Claude) or the fixture's hand totals.
    - Guards against wrong cost and token numbers being shown as fact.
    - [user] Turn 3.
  - The share of local-ledger deltas without the collapse key is reported (Open Question 2).
  - `packages/opencode-workflow-hooks/tests/test_hooks.mjs` shows the plugin does not forward the `remove` list, and the remove-list equality test passes.
    - Guards against the two enforcement points drifting apart.
    - [user] Turn 5: "Ingest + OpenCode plugin".
- Surfaces:
  - `tools/workflow/internal/ingest/ingest.go` (policy, normalisation and extraction tables) and `ingest_test.go`;
  - `tools/workflow/internal/store/store.go` (column migration, `Append`, tenant lock) and `store_test.go`;
  - new `tools/workflow/internal/archive/` (writer and per-conversation reader);
  - `packages/opencode-workflow-hooks/src/index.ts` and `tests/test_hooks.mjs`;
  - `tools/hooklog/tests/fixtures/` (shared fixture batch);
  - `tools/workflow/cmd/workflow/drain_test.go`.
- Approach: known
- Depends on: nothing
- Units:
  - 1-01 Event archive package: `briefs/1-01-archive-package.md`. Depends on nothing. Alongside 1-02, 1-03, 1-04.
  - 1-02 Ledger columns, indexes and Append: `briefs/1-02-store-columns.md`. Depends on nothing. Alongside 1-01, 1-03, 1-04.
  - 1-03 OpenCode plugin remove list: `briefs/1-03-plugin-remove-list.md`. Depends on nothing. Alongside 1-01, 1-02, 1-04.
  - 1-04 Normalised event table, usage extraction and shared fixture: `briefs/1-04-normalise-and-extract.md`. Depends on nothing. Alongside 1-01, 1-02, 1-03.
  - 1-05 Ingest policy, collapse, slim facts and archive wiring: `briefs/1-05-ingest-policy.md`. Depends on 1-01, 1-02, 1-03, 1-04. Alongside nothing.
  - 1-06 End-to-end Phase 1 proof and delta-key share: `briefs/1-06-end-to-end-and-delta-share.md`. Depends on 1-05. Alongside nothing.
- Placement notes: the tenant lock named in the surfaces above is proved by Phase 2's outcome and is built there. The route is `POST /v1/ingest`, not `/v1/facts`.

### Phase 2 — Historical compaction and reclaim

- Outcome: `workflow ledger compact` is run against a copy of the local ledger.
  - It completes and reports before and after rows and bytes.
  - `facts` has no removed-event rows.
  - It has exactly one row per distinct delta part key.
  - No hook fact carries a payload.
  - The archive's distinct `row_hash` count equals the pre-compaction count of non-removed hook facts.

  These guard against history silently disagreeing with the Phase 1 ingest rules, and against compaction losing a body ([user] Turn 2: "Compact in place + reclaim").

  The file is under 1.5 GB.
  - Guards against the space not actually being reclaimed.
  - [judgement] This is an estimate. About 215k surviving rows ([measured]) carry envelopes and indexes instead of 5.9 GB of payload; 1.5 GB leaves room for the new columns and indexes. A miss is advisory (Open Question 3).

  `/v1/health` no longer reports `compaction: required`.

  Separately:
  - Starting serve while compaction holds the lock fails with a clear error. This guards against two writers on one SQLite file.
  - Interrupting compaction and rerunning it ends in the same state. This guards against a half-compacted ledger that cannot be finished.
- Surfaces:
  - `tools/workflow/internal/store/store.go` (compaction, meta key, lock);
  - `tools/workflow/cmd/workflow/main.go` (the `ledger compact` subcommand);
  - `tools/workflow/internal/serve/serve.go` (health field, lock acquisition at start);
  - `tools/workflow/internal/archive/`.
- Approach: known
- Depends on: Phase 1

### Phase 3 — Fast analytics API with usage and cost

- Outcome:
  - The committed benchmark is run against the compacted ledger copy. It reports p95 < 500 ms for every case in the performance bound.
    - Guards against the "tens of seconds" filtering in Intent.
    - [user] Turn 1 chose the bound.
  - `GET /v1/analytics/schema` returns the matrix above, and an unsupported pairing is 400. These guard against the site offering charts the server cannot answer.
  - A kind filter on a `hook_events` query is listed in `ignored_filters`. This guards against design 7 open issue 1, where a filter silently zeroes a measure.
  - `cost_usd` for a fixture conversation equals its hand-computed value from `tools/transcript/pricing.json`, and reported OpenCode cost passes through. This guards against cost drifting from the repo's pricing source ([user] Turn 3).
  - The existing Playwright suite in `packages/workflow-analytics/tests/e2e/` passes against the current site, which proves the retained route shapes did not regress. It does not prove counts, which change by design.
  - Go tests cover `query`, `conversation`, keyset paging past page one, `tz` bucketing of a sub-day fixture, and top-N folding.

  The response caps (20,000 rows, top 20/100, 5,000 timeline events) are [judgement] defaults.
- Surfaces:
  - `tools/workflow/internal/serve/analytics.go` and `analytics_test.go`;
  - `tools/workflow/internal/store/analytics.go`, `analytics_test.go`, and a new `analytics_bench_test.go`;
  - a new embedded pricing table in `tools/workflow/internal/store/`, with a test asserting it equals `tools/transcript/pricing.json`.
- Approach: known. Rollups are conditional (Open Question 1).
- Depends on: Phase 2

### Phase 4 — Dashboard shell, filters and drill-down

- Outcome: These run against the compacted ledger served locally.
  - The 7d preset chosen on Overview persists when navigating to Hooks. This guards against the missing quick ranges and lost filters named in Intent and Problem.
  - Brushing a Trends chart narrows the window.
  - Clicking a harness bar adds a `harness` filter chip, and shift-clicking excludes it.
  - Clicking a conversation ID opens its timeline with token and cost totals.
  - Usage & cost shows cost by model.

    These guard against the drill-down gap in Intent.
  - Every interaction renders within 1 s, as measured by a Playwright timing assertion from input to settled chart.
    - Guards against the site, not the API, being the bottleneck.
    - [judgement] 500 ms API + render.
  - A burst of filter changes issues only the last request, and `/repos` issues one request, not one per repo. These guard against the refetch storms in Problem. The 250 ms debounce is [judgement].
  - Every design 7 report renders with ECharts in light and dark themes, each with a data-table toggle, and `layerchart` is gone from `package.json`. This guards against two chart stacks ([user] Turn 1: ECharts).
- Surfaces:
  - `packages/workflow-analytics/src/lib/api.ts`, `filters.ts` and `state.svelte.ts` (data layer, URL view state);
  - `src/lib/charts/` (ECharts components replacing `Bars.svelte` and `LineSeries.svelte`);
  - `src/lib/components/FilterBar.svelte`;
  - `src/routes/+layout.svelte` and every route under `src/routes/`, plus new `usage/` and `conversation/` routes;
  - `package.json`;
  - `tests/e2e/*.spec.ts`.
- Approach: known
- Depends on: Phase 3

### Phase 5 — Chart builder and dashboards

- Outcome:
  - In the builder, `cost_usd` × `model` × `harness` with a `day` bucket renders small multiples. Switching to `heatmap` with `hour_of_day` × `weekday` renders a heatmap. These guard against the "configurable multi dimension graphs" in Intent.
  - A view saved under a name and added to a new dashboard survives a reload. Exporting the dashboard JSON and importing it into a fresh browser profile reproduces it. This guards against saved work being lost or unshareable ([user] Turn 1: URL plus local).
  - Executions shows the design → brief → commit → report sankey, and clicking a link filters its table.
  - No unsupported pairing can be selected.
  - Playwright covers builder, save, dashboard, export and import.
- Surfaces:
  - `packages/workflow-analytics/src/routes/` (new `builder/` and `dashboards/`, changed `executions/`);
  - a new `src/lib/views.ts` (saved-view store);
  - `tests/e2e/` (new `builder.spec.ts` and `dashboards.spec.ts`).
- Approach: known
- Depends on: Phase 4

## Provenance Notes

- **What the ledger is.** It is mostly bodies nobody queries: token deltas, repeated system prompts and request parameters. Removing and stripping them at ingest shrinks the ledger by roughly 10× before any read-side work. That is why rollups became conditional rather than foundational.
- **How collapse stays append-only.** It works by choosing the fact's identity (row hash from the part key) instead of updating rows. That gives exact idempotency for free. A separate `part_chunks` table with a per-delta seen-id set was considered and rejected: exact chunk counts would have needed millions of stored ids.
- **The archive replaces payloads in `raw`.** It is a per-conversation file that people and transcript tools can read whole. It is not served over HTTP: design 7's rule that no payload bodies reach the browser still holds, and a body view in the timeline would be a later design with its own trust review.
- **Compaction is offline.** Rewriting a 9 GB SQLite file inside serve would block the single writer and ingest. A migration in `Open()` would block startup.
- **ETags were dropped.** OpenCode drains every few seconds and presets resolve `to` to "now", so validators would rarely match. The client session cache plus a small ledger carry the latency instead.
- **Rejected alternatives:**
  - DuckDB-WASM (design 7);
  - server-side dashboards (no user identity);
  - keeping LayerChart (sankey, heatmap, treemap and brush would all be hand-built);
  - an approximate seen-id window for chunk counts (the user dropped the measure instead).
