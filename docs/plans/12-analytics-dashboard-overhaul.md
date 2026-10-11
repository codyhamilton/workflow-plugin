# Analytics Dashboard Overhaul

The analytics site was slow on a real ledger and too thin to answer the questions people asked of it. This work slimmed the ledger at ingest, added an offline compaction and a generic query API, and rebuilt the site as an ECharts dashboard with filters, drill-down, a chart builder and saved dashboards. On a compacted copy of the local ledger every benchmark case came in under 500 ms p95 and the site settles interactions under one second. The live server has not been cut over, and most cost figures are unpriced until rates are added.

## Intent

User request, verbatim:

> significant improvements to the workflow UI. Greatly improve performance, filtering options, interactivity and UI / UX. It needs an overhaul into a modern dashboard with advanced graphs and drill down. Some filtering is very slow, large data sets taking tens of seconds and missing quick date range selection 
>
> Also provide more analytical  configurable multi dimension graphs. Create the design

## Why This Existed

The local ledger held 7.6M facts in 9.35 GB, and about 5.9 GB was hook payload nobody queried; 97% of the rows were OpenCode streamed-token deltas. Every analytics request re-aggregated the raw window, parsing JSON per row. The site refetched on every filter change, had no date presets, no drill-down and only line and bar charts. Model, token and cost data reached the ledger but was never extracted. Some payloads (`chat.headers`, `shell.env`) carried secrets and should never have been stored.

## What Was Built

**Changed:** `tools/workflow/internal/{ingest,archive,store,compact,serve}`, `tools/workflow/cmd/workflow`, `packages/opencode-workflow-hooks`, `packages/workflow-analytics`, `tools/hooklog/tests/fixtures`, and design docs 1, 2, 3 and 7.

### Phase 1 — Event policy, archive and slim ingest
One policy table in ingest maps each event to keep or remove; the OpenCode plugin carries the same remove list and a test asserts the two are equal. Removed events are answered `accepted` and stored nowhere. Every kept hook body is written verbatim, after redaction, to a per-conversation zstd archive before the fact commits; the fact keeps only an envelope plus extracted columns (`norm_event`, `tool`, `model`, token columns, reported cost, artifact `kind`, `plan`, `source`, `sha`). Models, usage and a normalised cross-harness event vocabulary are extracted for Claude, Codex and OpenCode.

### Phase 2 — Historical compaction and reclaim
`workflow ledger compact` is offline and resumable under an exclusive tenant-dir lock that serve takes shared. It archives bodies, drops removed events, strips payloads, fills the columns and vacuums. A copy of the real ledger went from 11.6 GB to 296 MB with no removed events, payloads or deltas left and every archive hash accounted for.

### Phase 3 — Fast analytics API with usage and cost
`GET /v1/analytics/query`, `/schema` and `/conversation` plus the shared filter keys (`tz`, `all=1`, `ignored_filters`), keyset paging for executions and conversations, and read-time cost from an embedded pricing table equal to `tools/transcript/pricing.json`. Hourly rollups were needed and added for the cases that missed. The committed benchmark passes 2,063 cases with a max p95 of 464 ms.

### Phase 4 — Dashboard shell, filters and drill-down
LayerChart was replaced by ECharts with light and dark themes and a data-table toggle. The URL is the view; presets, brush-to-zoom, filter chips with include and shift-exclude, a debounced and cancelling client with a session cache, and the conversation timeline with token and cost totals.

### Phase 5 — Chart builder and dashboards
A schema-driven builder (line, stacked area, grouped bar, heatmap, treemap, small multiples), saved views and dashboards in `localStorage` with JSON export and import, an Executions sankey, quality box plots, and fixes for latency, the usage table and the conversation page. Playwright covers builder, save, dashboard, export and import.

## Deviations

- `message.part.delta` is removed rather than collapsed: the user decided during the work that deltas are dropped at the source, and a purge command removes them from history. `hook_events` therefore counts parts from `message.part.updated`.
- The compaction engine lives in `internal/compact`, not `store`, because the policy table sits in ingest, which imports store.
- The hook treemap is two linked two-level treemaps because `/query` takes two dimensions. `/repos` makes a fixed four requests. Non-query routes clamp All time to 399 days with a visible notice.
- Dashboard tiles are iframes of the saved URL with `embed=1`; the sankey link filter runs client-side over the loaded page.
- Phase 4's own verification missed the 1 s target on the large copy; a debounce change and API speedups in Phase 5 brought it under (max 597 ms).

## Review

Terminal review by three focused reviewers: no blocker, and no high finding that is in scope and non-architectural, so no fixer ran. One mechanical medium was fixed in place: the secrets corpus test failed on a report quoting dummy `NAME=value` assignments, and the wording was changed. Verdict was PASS_WITH_FOLLOWUPS.

## Residual Risks

- The live ledger is neither compacted nor migrated. First open of a large ledger pays one-time index and backfill cost; run `workflow ledger compact` and the delta purge during a maintenance stop. A `serve` binary built from this tree reports "analytics bundle not embedded" unless the site build runs before `go build`.
- Benchmark headroom is thin (464 ms of 500 ms); the usage read still sorts and parses JSON in Go over every kept row.
- Pricing rates for Claude and Codex are missing from `tools/transcript/pricing.json` and `internal/store/pricing_table.json`, so most calls show as unpriced, never as `$0`.
- Live Claude usage is not deduplicated by message id (about 0.06% of local message ids repeat).
- `artifact_feedback` never scored any brief or report because the workflow MCP server failed to start.

## Follow-ups

Recorded under open issues in [design 7](../design/07-analytics-site.md): the usage rollup and SQL grouping, message-id column for live Claude dedupe, archive read past a torn frame, compaction re-archiving slim rows and its cursor shortcut, the `config` hook capture, builder zero-dimension state, dashboard import caps and `embed=1` with fragments, `partial` on every route, conversation totals over truncated timelines, `time/tzdata` and input bounds, saved-view store validation, builder `data-ready` staleness, and server-side sankey filtering.

## Decisions Worth Keeping

- Collapse by row-hash identity was rejected in favour of dropping deltas; the ledger stays append-only except for the sanctioned compaction exception.
- Hook bodies live in an on-disk archive, not the database, and are never served over HTTP.
- Rollups were conditional on the benchmark, and aggregation stays in SQLite.
- The URL is the view; named views and dashboards are `localStorage` only, with no server store.
