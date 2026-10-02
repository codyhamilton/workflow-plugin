# Transcript Toolkit

Unified CLI for extracting cost metrics from Claude Code and Cursor session transcripts.

Discovery defaults to all registered sources. Filter with `--tool claude-code`, `--tool cursor`, or `--tool cursor-cloud`. The cloud source is locally cached run metadata, not a transcript; `latest` ignores it unless `--tool cursor-cloud` is explicit.

## Quick start

```bash
# Discover sessions
python3 tools/transcript/find.py ~/workspace/open-pajero-maps
python3 tools/transcript/find.py --all --limit 10
python3 tools/transcript/find.py --match pajero
python3 tools/transcript/find.py --tool claude-code
python3 tools/transcript/find.py --all --tool cursor-cloud --limit 10
python3 tools/transcript/find.py --all --tool cursor --min-parent-assistant-turns 60

# Extract once, analyse many times
python3 tools/transcript/extract.py f06c7365 ~/workspace/open-pajero-maps > /tmp/s.json
python3 tools/transcript/extract.py session_01GUoz3qj2N9czSfWTifD6rM   # Claude URL slug
cat /tmp/s.json | python3 tools/transcript/stats.py
cat /tmp/s.json | python3 tools/transcript/cost.py --label Candidate
cat /tmp/s.json | python3 tools/transcript/classify.py --dry-run   # Jev snapshot classify (no API key)

# One-shot
python3 tools/transcript/stats.py --session latest --project ~/workspace/open-pajero-maps
python3 tools/transcript/cost.py --session latest --project ~/workspace/open-pajero-maps --label Baseline
```

`--session latest` picks the most recent session across all queried tools for the resolved project path (or globally when no project is given).

## Commands

| Script | Purpose |
|--------|---------|
| `find.py` | List sessions. Flags: `--all`, `--match`, `--limit`, `--since`, `--min-subagents`, `--min-parent-assistant-turns`, `--tool`, `--format` |
| `extract.py` | Normalized JSON to stdout. Resolves UUID, prefix, URL slug, bridge ID, or `latest` |
| `stats.py` | Summary from stdin JSON or `--session` + `--project` |
| `cost.py` | Emit `cost-comparison.md` schema via `--label Baseline\|Candidate` |
| `search.py` | Pattern search across parent + subagent transcripts |
| `iterate_analysis.py` | Classify spawn phases against iterate workflow |
| `classify.py` | Jev session-kind Choice (+ optional workflow Score) from extract JSON snapshot |
| `cost_window.py` | Token attribution from usage CSV against session wall-clock window |
| `cost_estimate.py` | Ballpark Cursor token/cost estimate from transcript; `--reconcile-csv` compares to export |

Run any script with `--help` for full options.

### Jev transcript classification (spike)

Builds a compact snapshot from normalized JSON (not raw JSONL), then calls TypeSafe System One with pinned model `jev-1.13.0`. Requires `TYPESAFE_API_KEY` for live calls; defaults to dry-run when the key is missing.

```bash
python3 tools/transcript/extract.py SESSION PROJECT > /tmp/s.json
python3 tools/transcript/classify.py --dry-run < /tmp/s.json          # print request JSON
python3 tools/transcript/classify.py --live < /tmp/s.json             # POST + append log
python3 tools/transcript/classify.py --session latest --project PATH --live
```

Live runs append to `tools/transcript/.classify-log.jsonl` (gitignored) with `answers`, `usage`, `snapshot_hash`, and `human_label: null` for later comparison.

## Normalized output schema

Every source emits the same top-level JSON shape. The `source` field identifies `claude-code`, `cursor`, or `cursor-cloud`.

```json
{
  "source": "claude-code",
  "session": {
    "id": "...",
    "external_url": "https://claude.ai/code/session_01...",
    "project_path": "/home/user/project",
    "start_time_iso": "2026-09-14T11:24:26.000Z",
    "end_time_iso": "2026-09-14T11:30:28.000Z",
    "wall_seconds": 362,
    "parent_tool_counts": {"shell": 9, "spawn": 5},
    "parent_tool_counts_raw": {"Bash": 9, "Agent": 5},
    "parent_tool_turns": 14,
    "parent_api_calls": 8,
    "parent_token_usage": {"input_tokens": 0, "output_tokens": 0, ...},
    "subagent_api_calls": 14,
    "subagent_token_usage": {"input_tokens": 0, "output_tokens": 0, ...},
    "api_calls": 22,
    "context_estimate": 52314,
    "token_usage": {"input_tokens": 0, "output_tokens": 0, ...},
    "subagent_count": 5
  },
  "agent_spawns": [{"seq": 0, "agent_type": "...", "model": "...", "description": "..."}],
  "subagents": [{"id": "...", "tool_counts": {...}, "total_tool_turns": 10, "api_calls": 3, "token_usage": {...}, ...}],
  "user_queries": [{"ts": "...", "text": "..."}]
}
```

- `parent_tool_counts` / subagent `tool_counts` use **canonical** names (`shell`, `spawn`, `read`, …) for cross-harness comparison
- `*_raw` preserves harness-native names for debugging
- `agent_spawns` unifies Claude `Agent` and Cursor `Task` tool invocations
- `token_usage` / `api_calls` at session level are **parent + all subagents** (deduped per `message.id`). `parent_*` and `subagent_*` fields hold the split. Each usage block is per API call and includes full context for that call (`cache_read_input_tokens` is not incremental-only).
- `context_estimate` is the first parent response only — not total session context or cost input.

### Cursor turns

Cursor extraction also exposes `session.parent_assistant_turns`, `parent_user_turns`,
`subagent_assistant_turns`, `subagent_user_turns`, and aggregate `assistant_turns` /
`user_turns`. Each subagent has its own `assistant_turns` and `user_turns`.
`stats.py` prints these counts. An assistant turn here means one recorded assistant
message row. A row may contain several `tool_use` blocks; tool-use counts are
separate. User turns count user message rows, including subagent instructions.
Status/error rows and malformed lines are excluded. These are **observed
transcript turns**, not certified billable API calls: Cursor JSONL has no call
IDs or usage blocks, so `api_calls` remains `null`.

Use `parent_assistant_turns` for a parent-session length threshold. Aggregate
`assistant_turns` adds child work and can overstate the length of the parent
session. A session ID may have different JSONL copies under different project
directories; extraction counts the selected path and does not silently merge or
deduplicate those copies.

### Cursor cloud runs

`cursor-cloud` reads `bc-*` run records from the local Cursor global-state
database (`ItemTable`, `cloudAgentRepository.agents.*`). `find.py --all
--tool cursor-cloud` lists them; `extract.py BC_ID --tool cursor-cloud` returns
metadata, `transcript_available: false`, and null assistant/user turn counts.
The run's `workspaceRootPath` is a remote path, so project filtering requires
that exact path; use `--all` for a complete local cache inventory.

Conversation bodies are cached locally for only a few runs (the ones opened in
the Cursor UI; a 2026-10-03 sweep found 19 of 430, 3 of them complete). Two
stores are read:

- `cursorDiskKV` `composerData:*` / `bubbleId:*:*` rows, the same model as local
  chats. A run links via a `composerData:<bc-id>` key, `bubbleId:<bc-id>:*`
  keys, or a local composer whose `createdFromBackgroundAgent.bcId` is the run.
  Bubble `type` 1 is user, 2 is assistant; tool calls are `toolFormerData`.
  Bubbles can be missing while headers remain. `parent_*_turns` are set only
  when headers exist and every header has a bubble (`transcript_complete`).
- `conversation-search.db` `cloud-cache` rows: role-labelled flattened text
  (`user:` / `assistant:` blocks), no tool calls, may be truncated. Used for
  `observed_*_turns` lower bounds and `search` only; never for exact counts.

Extraction reports `transcript_available`, `transcript_complete`,
`transcript_store`, `bubble_headers`, `bubbles_present`, and `observed_*`
counts. Runs with no body keep every turn count null (unknown, not zero).
`bcCachedDetails:*` values are file diff caches, not conversations, and
`agentKv:blob:*` / IndexedDB hits for a `bc-*` ID are local-agent mentions.

`find.py --min-parent-assistant-turns N` filters on observed parent assistant
turns. It excludes records with unknown counts and prints how many were
excluded by source to stderr; it never treats an unknown count as zero. Use
`--tool cursor` for the local JSONL cohort. A cloud run remains ineligible for
a turn-threshold cohort unless its stream is complete (`transcript_complete`).

## Cursor cost estimation + CSV reconciliation

Cursor JSONL has no usage blocks. For ballpark session cost:

```bash
# Estimate from transcript (fixed context + per-tool deltas + cache simulation)
python3 tools/transcript/cost_estimate.py --session SESSION --project PATH --tool cursor

# Reconcile against dashboard export (usage-events-*.csv)
python3 tools/transcript/cost_estimate.py --session SESSION --project PATH --tool cursor \
  --reconcile-csv usage-events-2026-09-14.csv
```

Override heuristics per repo with `estimate.json` (see `estimate_defaults.json`). Claude Code
sessions with `token_usage` in the transcript should use `stats.py` instead.

## jq examples

```bash
# Parent tool breakdown
jq '.session.parent_tool_counts' /tmp/s.json

# Cursor parent turn proxy
jq '.session.parent_assistant_turns' /tmp/s.json

# Subagent turn totals
jq '[.subagents[].total_tool_turns] | add' /tmp/s.json

# Spawn models
jq '[.agent_spawns[].model] | group_by(.) | map({model: .[0], count: length})' /tmp/s.json
```

## Adding a new parser

1. Create `parsers/mytool.py` implementing the `TranscriptParser` protocol (`discover`, `discover_all`, `resolve`, `extract`, `search`)
2. Register in `parsers/__init__.py`: `from . import mytool`
3. Add canonical tool-name mappings in `lib/tools.py` if needed

No changes to CLI dispatch logic required.

## Relationship to conversation indexer

This toolkit is the fast-track for ad-hoc session analysis. The planned [conversation indexer](../../docs/design/conversation-indexer.md) will provide a SQLite-backed, queryable interface for cross-session search and aggregation.
