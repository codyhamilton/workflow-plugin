# Provenance: Analytics Dashboard Overhaul

## Session

- Session: Initial design (October 8, 2026)
- Timestamp: 2026-10-07T15:56:04Z
- CWD: /home/codyh/workspace/workflow-plugin

## Initial Request (verbatim)

> significant improvements to the workflow UI. Greatly improve performance, filtering options, interactivity and UI / UX. It needs an overhaul into a modern dashboard with advanced graphs and drill down. Some filtering is very slow, large data sets taking tens of seconds and missing quick date range selection 
>
> Also provide more analytical  configurable multi dimension graphs. Create the design

## Design Conversation

### Turn 1

**Agent asked:** Four questions:
- Performance model: server rollups with a generic cube query, a browser query engine, or index tuning only.
- Chart library: ECharts, LayerChart or Observable Plot.
- Where saved views persist: URL plus localStorage, a server store, or URL only.
- Performance target: p95 under 500 ms, 200 ms or 2 s.

**User responded:**
- Performance: "I think the chunk events are the main one, can these be collapsed (multiple concurrent chunks aggregate). That is a starting point and should be done on ingest, then rollup."
- Chart library: Apache ECharts.
- Saved views: URL plus local saved views.
- Target: p95 < 500 ms per request.

**Agent decisions:**

- Verified the user's chunk claim against the local ledger. `opencode` `message.part.delta` is 7,398,259 of 7,612,161 facts (97%), one row per streamed token. It began about 2026-10-05 and spans 1,382 conversations.
- Ingest collapses deltas into one aggregate row per `(conversation_id, messageID, partID, field)` with a chunk count (see Turn 2 and Agent Decisions for where that row lives). Rollups are built over the collapsed ledger.
- ECharts replaces LayerChart.
- The URL is the view; named views live in `localStorage`. This keeps design 7's rule against a saved-report store.
- p95 < 500 ms per analytics request on the real ledger closes the performance phase.

### Turn 2

**Agent asked:** How the hook-events measure should count a collapsed part; what to do with the 7.4M historical delta rows; whether the dashboard look-and-feel phase is approach-known or open.

**User responded:**
- Counting: "1 event per part, plus a 'chunks' measure".
- History: "Compact in place + reclaim".
- UI phase: "Known: build straight through".

**Agent decisions:**

- `hook_events` counts a part once; `chunks` is its own measure.
- A resumable background job in serve compacts history. An explicit maintenance command runs `VACUUM`.
- All four phases are approach-known.

### Turn 3

**Agent asked:** The adversarial review found three open decisions:
- how exact chunk counts must be, given that exact dedup needs millions of stored ids;
- whether to build rollups up front or benchmark first;
- whether to add model, token and cost fields, which design 7 excludes.

**User responded:**
- Chunk counts: "Drop chunks measure".
- Rollups: benchmark first, roll up only if needed.
- Tokens: "yes I want model/token/cost fields for sure where they are avaialble".

**Agent decisions:**

- Collapsed deltas become one fact per part. Its row hash comes from the part key, so redelivery is a `duplicate` and there is no `part_chunks` table.
- Rollups are conditional on the benchmark.
- Token, cost and model measures are in scope. Cost is reported cost where present, else tokens × `tools/transcript/pricing.json`.

### Turn 4

**User responded (mid-turn):** "but look to what other events we can drop?"

**Agent decisions:**

- Measured raw bytes per event. Besides deltas (4.0 GB), the largest are `message.part.updated` (320 MB), `experimental.chat.system.transform` (302 MB, about 30 KB each), `tool.execute.after` (280 MB) and `chat.params`/`chat.headers` (140 MB each).
- Traced readers: no downstream code reads the bulky OpenCode bus events by name.
- Proposed a keep, stub or collapse policy.

### Turn 5

**Agent asked:** Approve the policy, and choose whether to enforce it at ingest only or at ingest plus the OpenCode plugin.

**User responded:**
- Policy: "Definitely remove those opencode system, chat params/headers. We should try to keep standard events we can normalise across harnesses and are useful. We can probably drop bodies for analytics, but separately store full transcripts (at least what we have of them via the events) on disk. So original source is kept somewhere, just not in db".
- Enforcement: "Ingest + OpenCode plugin".

**Agent decisions:**

- Policy outcomes are `remove` (no fact and no archive line), `collapse` and `keep`. `shell.env` is added to `remove` because it carries environment secrets.
- Stored hook facts drop their payloads. Bodies go verbatim to a per-conversation `.jsonl.zst` archive under the tenant dir.
- A `norm_event` cross-harness vocabulary is seeded from hooklog kinds.
- The plugin and ingest share the remove list, and a test asserts they match.
- Folded in the adversarial review's findings:
  - the migration only adds columns;
  - compaction is offline under a tenant lock;
  - ETags are dropped;
  - the matrix is stated in the design;
  - filters that don't apply to a measure are listed in `ignored_filters`;
  - folding and response caps are defined.
- Phase 1 is split into ingest (new data) and historical compaction, which makes five phases.

## Agent Decisions

- **Append-only preserved**: a collapsed delta's identity is its part key, so `INSERT OR IGNORE` keeps one row per part. Only the offline compaction deletes or rewrites facts, and design 3 records it as the sanctioned exception. Rationale: design 3 principle 6 forbids `UPDATE` on facts.
- **Rollups conditional**: rollups are added only for measures that miss the benchmark. Rationale: once slimmed, the ledger is about 215k rows, and rollups carry most of the consistency risk.
- **Old routes retained**: design 7's routes keep their shapes, re-served from the new structures. Rationale: the existing e2e suite then proves Phase 3 did not regress the current site before Phase 4 replaces it.
