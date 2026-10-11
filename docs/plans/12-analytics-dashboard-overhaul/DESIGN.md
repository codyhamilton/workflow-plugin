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

- Outcome: With an updated binary, the shared fixture batch is posted to `POST /v1/ingest`. The batch contains, for every harness, removed, collapsible (including redelivered deltas) and kept events, plus usage events.
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
- Units:
  - 2-01 Tenant-dir lock, meta table and compaction state in health: `briefs/2-01-lock-meta-health.md`. Depends on nothing. Alongside 2-02.
  - 2-02 Archive tolerates and repairs a torn last frame: `briefs/2-02-archive-torn-frame.md`. Depends on nothing. Alongside 2-01.
  - 2-03 Compaction engine: `briefs/2-03-compact-engine.md`. Depends on 2-01, 2-02. Alongside nothing.
  - 2-04 `workflow ledger compact` command: `briefs/2-04-ledger-compact-command.md`. Depends on 2-03. Alongside nothing.
  - 2-05 Start compaction on a copy of the local ledger: `briefs/2-05-kickoff-compaction-on-copy.md`. Depends on 2-04. Alongside nothing.
  - 2-06 Verify the compacted copy: `briefs/2-06-verify-compacted-copy.md`. Depends on 2-05. Alongside nothing.
- Placement notes: the engine lives in a new `internal/compact` package, not in `store.go`, because the policy table is in `internal/ingest`, which imports `store`; `store` gains only the lock, `meta` and the `OpenExclusive`/`Raw` hooks. Compaction also backfills `kind`, `plan`, `source` and `sha` on artifact and commit facts, which Phase 3 reads. 2-05 and 2-06 are split at the kickoff because the compaction of the roughly 11.6 GB ledger runs for longer than a worker's turn budget; the copy lives in `/var/tmp/workflow-compact-copy/` (the `/home` disk has under 9 GB free) and is kept for Phase 3's benchmark.

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
- Units:
  - 3-01 Embedded pricing table and cost function: `briefs/3-01-pricing-cost.md`. Depends on nothing. Alongside 3-02, 3-03.
  - 3-02 Shared filter keys and column-based reads: `briefs/3-02-filter-columns.md`. Depends on nothing. Alongside 3-01, 3-03.
  - 3-03 One survivor-ts rule for ingest and compaction: `briefs/3-03-collapse-survivor-ts.md`. Depends on nothing. Alongside any unit up to 3-10 (it owns only `internal/compact`).
  - 3-04 Measure matrix and query engine, non-usage measures: `briefs/3-04-query-engine.md`. Depends on 3-02. Alongside 3-01, 3-03.
  - 3-05 Usage measures, cost and Claude message dedupe: `briefs/3-05-usage-measures.md`. Depends on 3-01, 3-04. Alongside 3-06.
  - 3-06 Filter parsing, `schema` and `query` routes: `briefs/3-06-serve-query-routes.md`. Depends on 3-02, 3-04. Alongside 3-05.
  - 3-07 Keyset paging for executions and conversations: `briefs/3-07-keyset-paging.md`. Depends on 3-02, 3-06. Alongside 3-09.
  - 3-08 Summary, facets and Explore additions: `briefs/3-08-summary-facets-explore.md`. Depends on 3-05, 3-07. Alongside 3-09.
  - 3-09 `conversation` route: `briefs/3-09-conversation-route.md`. Depends on 3-05, 3-06. Alongside 3-07, 3-08.
  - 3-10 Env-gated benchmark harness: `briefs/3-10-benchmark-harness.md`. Depends on 3-08, 3-09. Alongside nothing.
  - 3-11 Run the benchmark on the compacted copy and decide rollups: `briefs/3-11-run-benchmark-on-copy.md`. Depends on 3-10. Alongside nothing.
  - 3-12 Conditional: indexes, then hourly rollups, for the cases that missed: `briefs/3-12-fix-misses-indexes-rollups.md`. Depends on 3-11. Runs only if 3-11 reports misses (Open Question 1). Alongside nothing.
  - 3-13 Phase 3 outcome check: `briefs/3-13-phase-proof.md`. Depends on 3-03, 3-11, and 3-12 when it ran. Alongside nothing.
- Placement notes: files are owned so that parallel units never share one: `store/analytics.go` belongs to 3-02, then 3-07, then 3-08 in turn, and `serve/analytics.go` to 3-06, 3-07, 3-08 in turn; new files (`pricing.go`, `query.go`, `usage.go`, `conversation.go`, `analytics_query.go`, `analytics_conversation.go`) carry the rest. The benchmark is in `internal/serve` (not `store`, as the surfaces list says) because it drives HTTP routes. It copies `ledger.db` from `/var/tmp/workflow-compact-copy/data/local` to a temp dir and opens the copy, so neither the compacted copy nor the live ledger is written. Whether 3-12 runs is decided by 3-11's report: no case over 500 ms p95 answers Open Question 1 "no rollup", and any miss is fixed first by an index and only then by a rollup; more than three missed measures sends 3-12 back to the orchestrator to split per measure. Local models are mostly absent from `tools/transcript/pricing.json` (7 Cursor models), so most calls will show as `unpriced_calls` unless the harness reported a cost; 3-11 records the share.

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
- Units:
  - 4-01 Data client: cancellation, debounce, cache, dedupe, concurrency: `briefs/4-01-data-client.md`. Depends on nothing. Alongside 4-02, 4-03, 4-04.
  - 4-02 Filter model, presets, bucket choice and cost label: `briefs/4-02-filter-model-presets.md`. Depends on nothing. Alongside 4-01, 4-03, 4-04.
  - 4-03 Fixture usage data and e2e helpers: `briefs/4-03-fixture-usage-e2e-helpers.md`. Depends on nothing. Alongside 4-01, 4-02, 4-04.
  - 4-04 ECharts components, theme and data-table toggle: `briefs/4-04-echarts-components.md`. Depends on nothing. Alongside 4-01, 4-02, 4-03.
  - 4-05 Shell, filter bar, chips and shared view state: `briefs/4-05-shell-filterbar-view.md`. Depends on 4-01, 4-02, 4-03, 4-04. Alongside nothing.
  - 4-06 Overview: `briefs/4-06-overview.md`. Depends on 4-05. Alongside 4-07 to 4-15.
  - 4-07 Trends with brush: `briefs/4-07-trends.md`. Depends on 4-05. Alongside 4-06, 4-08 to 4-15.
  - 4-08 Usage & cost: `briefs/4-08-usage-cost.md`. Depends on 4-05. Alongside 4-06, 4-07, 4-09 to 4-15.
  - 4-09 Repos: `briefs/4-09-repos.md`. Depends on 4-05. Alongside 4-06 to 4-08, 4-10 to 4-15.
  - 4-10 Hooks: `briefs/4-10-hooks.md`. Depends on 4-05. Alongside 4-06 to 4-09, 4-11 to 4-15.
  - 4-11 Quality: `briefs/4-11-quality.md`. Depends on 4-05. Alongside 4-06 to 4-10, 4-12 to 4-15.
  - 4-12 Executions: `briefs/4-12-executions.md`. Depends on 4-05. Alongside 4-06 to 4-11, 4-13 to 4-15.
  - 4-13 Conversations, virtualised: `briefs/4-13-conversations.md`. Depends on 4-05. Alongside 4-06 to 4-12, 4-14, 4-15.
  - 4-14 Conversation timeline: `briefs/4-14-conversation-timeline.md`. Depends on 4-05. Alongside 4-06 to 4-13, 4-15.
  - 4-15 Explore and Settings: `briefs/4-15-explore-settings.md`. Depends on 4-05. Alongside 4-06 to 4-14.
  - 4-16 Retire LayerChart and the old filter model; cross-route interaction tests: `briefs/4-16-retire-layerchart-interactions.md`. Depends on 4-06 to 4-15. Alongside nothing.
- Placement notes: every route unit owns one route directory and its spec; shared code is owned by 4-01 to 4-05 only, so 4-06 to 4-15 never share a file. The e2e suite binds a fixed port and builds once per run, so parallel route units run in separate git worktrees (each needs `node_modules`) with distinct `E2E_PORT` values (4-03 adds the variable, default 4391). The server has no exclude parameter: the site realises an exclude chip as the complement of the facet values (`apiParams` in 4-02), so an exclude on `conversation_id` is unsupported and is marked so on the chip. `/query` allows two dimensions, so the three-level harness, norm_event, tool treemap is two linked two-level treemaps (4-10), a deviation from the Solution Shape wording. "`/repos` issues one request, not one per repo" is realised as a fixed four `/query` requests with `dim=repo_id` and `top=100`, independent of repo count (4-09). Routes other than `/query` reject windows over 400 days, so All time is clamped to 399 days there with a visible notice, and `/query` takes `all=1`. Presets and buckets are chosen in range (4-02), `scores` always carries one `kind` (4-02, 4-11), and cost is shown through `costLabel` with `unpriced_calls`, never as `$0` (4-02, 4-06, 4-08, 4-14). The sankey, builder and saved views are Phase 5 and are not built here.

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
- Units:
  - 5-01 — Saved-view and dashboard store (`views.ts`). Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-01-saved-view-store.md`. Depends on: none. Alongside: all wave-1.
  - 5-02 — Chart-builder config model (`builder.ts`). Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-02-builder-spec.md`. Depends on: none. Alongside: all wave-1.
  - 5-03 — Sankey and box-plot components, `EChart.svelte` registration. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-03-sankey-boxplot-charts.md`. Depends on: none. Alongside: all wave-1.
  - 5-04 — Usage legend overlap, Hooks bar hit area (`options.ts`, `BarChart.svelte`). Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-04-chart-legend-and-bar-hit-area.md`. Depends on: none. Alongside: all wave-1.
  - 5-05 — `BuilderChart`, grouped bar, small multiples. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-05-builder-chart-components.md`. Depends on: 5-02. Alongside: 5-01, 5-03, 5-04, 5-06, 5-09, 5-10, 5-11 to 5-16.
  - 5-06 — Layout: save-view control, nav, embed mode, notices fix. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-06-shell-saved-views-embed-notices.md`. Depends on: 5-01. Alongside: 5-02 to 5-05, 5-10 to 5-16.
  - 5-07 — `/builder` route and spec. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-07-builder-route.md`. Depends on: 5-02, 5-05. Alongside: 5-08, 5-09, 5-10, 5-14, 5-15, 5-16.
  - 5-08 — `/dashboards` route, export, import. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-08-dashboards-route.md`. Depends on: 5-01, 5-06. Alongside: 5-07, 5-09, 5-10, 5-14, 5-15, 5-16.
  - 5-09 — Executions sankey and link filter. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-09-executions-sankey.md`. Depends on: 5-03. Alongside: 5-07, 5-08, 5-10, 5-14, 5-15, 5-16.
  - 5-10 — Usage table consistent key set. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-10-usage-table-merge.md`. Depends on: none. Alongside: all other units.
  - 5-11 — `query.ts` debounce and in-flight entry. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-11-client-latency-and-inflight.md`. Depends on: none. Alongside: all wave-1.
  - 5-12 — Go: profile Overview and Usage request sets on the large ledger. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-12-page-request-set-profile.md`. Depends on: none. Alongside: all site units.
  - 5-13 — Go: speed up the three slowest requests. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-13-api-slowest-cases.md`. Depends on: 5-12. Alongside: all site units.
  - 5-14 — Back link, zero-token rows, `costLabel`. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-14-conversation-page-fixes.md`. Depends on: none. Alongside: all other units.
  - 5-15 — Quality box plots beside the baseline. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-15-quality-distribution-charts.md`. Depends on: 5-03. Alongside: 5-07, 5-08, 5-09, 5-10, 5-14, 5-16.
  - 5-16 — Conversations error panel. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-16-conversations-fetch-errors.md`. Depends on: none. Alongside: all other units.
  - 5-17 — Phase 5 end-to-end proof and 1 s timing. Brief: `docs/plans/12-analytics-dashboard-overhaul/briefs/5-17-phase-5-e2e.md`. Depends on: 5-04 to 5-11, 5-14 to 5-16, 5-18. Alongside: nothing.
- Placement notes: wave 1 (no dependencies, disjoint paths) is 5-01, 5-02, 5-03, 5-04, 5-10, 5-11, 5-12, 5-14, 5-16; then 5-05 (after 5-02), 5-06 (after 5-01), 5-09 and 5-15 (after 5-03), 5-13 (after 5-12); then 5-07 (after 5-02, 5-05) and 5-08 (after 5-01, 5-06); 5-17 last. Each route unit owns one route directory and its spec; `+layout.svelte` is owned by 5-06 alone, `EChart.svelte` by 5-03 alone, `query.ts` by 5-11 alone, `format.ts` by 5-14 alone. Parallel e2e units use separate git worktrees and distinct `E2E_PORT` values. Deviations from the wording above: `/query` takes one measure, so the Usage table fix (5-10) is five requests with `top=100` returning one key set, not literally one `/query`; `/executions` rows carry no design reference, so the sankey (5-09) takes its design node from the executions total and its links from `counts` only; dashboard tiles (5-08) are iframes of the saved URL with `embed=1`, which 5-06 supports; the sankey link click is a page-local `shape` URL parameter filtering the table client side. The 1 s timing assertion holds on the fixture (5-17); the large-ledger figure is re-measured by the orchestrator, with 5-11 (debounce) and 5-12/5-13 (API) as the levers.

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

## Amendments after sign-off

- **`message.part.delta` is removed, not collapsed.** The user decided (during Phase 3) that streamed deltas are dropped at the source. The OpenCode plugin and ingest both list `message.part.delta` as `remove`: no fact and no archive line. The `collapse` outcome and the "every delta is still archived" rule above no longer apply to new data. The historical ledger and archive are rewritten offline to delete every delta fact and archive line, since the message parts remain in `message.part.updated`. Closed Phases 1 to 3 are not edited; a fixer unit after Phase 3 makes the change.
- **`hook_events` counts parts from `message.part.updated`.** It no longer counts a collapsed delta part. The Phase 4 and Phase 5 measures and any chart that offers `hook_events` use this meaning.
