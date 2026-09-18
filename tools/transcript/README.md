# Transcript Toolkit

Unified CLI for extracting cost metrics from Claude Code and Cursor session transcripts.

All commands default to querying **both** harnesses. Filter with `--tool claude-code` or `--tool cursor`.

## Quick start

```bash
# Discover sessions
python3 tools/transcript/find.py ~/workspace/open-pajero-maps
python3 tools/transcript/find.py --all --limit 10
python3 tools/transcript/find.py --match pajero
python3 tools/transcript/find.py --tool claude-code

# Extract once, analyse many times
python3 tools/transcript/extract.py f06c7365 ~/workspace/open-pajero-maps > /tmp/s.json
python3 tools/transcript/extract.py session_01GUoz3qj2N9czSfWTifD6rM   # Claude URL slug
cat /tmp/s.json | python3 tools/transcript/stats.py
cat /tmp/s.json | python3 tools/transcript/cost.py --label Candidate

# One-shot
python3 tools/transcript/stats.py --session latest --project ~/workspace/open-pajero-maps
python3 tools/transcript/cost.py --session latest --project ~/workspace/open-pajero-maps --label Baseline
```

`--session latest` picks the most recent session across all queried tools for the resolved project path (or globally when no project is given).

## Commands

| Script | Purpose |
|--------|---------|
| `find.py` | List sessions. Flags: `--all`, `--match`, `--limit`, `--since`, `--min-subagents`, `--tool`, `--format` |
| `extract.py` | Normalized JSON to stdout. Resolves UUID, prefix, URL slug, bridge ID, or `latest` |
| `stats.py` | Summary from stdin JSON or `--session` + `--project` |
| `cost.py` | Emit `cost-comparison.md` schema via `--label Baseline\|Candidate` |
| `search.py` | Pattern search across parent + subagent transcripts |
| `iterate_analysis.py` | Classify spawn phases against iterate workflow |
| `cost_window.py` | Token attribution from usage CSV against session wall-clock window |
| `cost_estimate.py` | Ballpark Cursor token/cost estimate from transcript; `--reconcile-csv` compares to export |

Run any script with `--help` for full options.

## Normalized output schema

Every harness emits the same JSON shape. The `source` field always identifies the harness (`claude-code` or `cursor`).

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
