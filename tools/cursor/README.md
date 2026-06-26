# Cursor Transcript Toolkit

Standalone Python 3.10+ scripts for parsing and analysing Cursor agent-transcript sessions. No external dependencies. No indexing step. Each script is independently runnable with `--help`.

## Quick start

```bash
# Discover sessions for a project
python3 tools/cursor/find.py ~/workspace/garcia-music

# Extract a session and pipe to stats or analysis
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music | python3 tools/cursor/stats.py
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music | python3 tools/cursor/iterate_analysis.py

# Search message text across a session
python3 tools/cursor/search.py 87e55915 ~/workspace/garcia-music "pattern to find"
```

## Cursor format

Cursor stores agent transcripts under `~/.cursor/projects/{project-hash}/agent-transcripts/{session-id}/`:

- **Parent JSONL**: `{session-id}.jsonl` — the orchestrator conversation. Each line is a JSON object `{"role": "user"|"assistant", "message": {"content": [...]}}`.
- **Subagents dir**: `subagents/{agent-id}.jsonl` — one file per spawned subagent, same JSONL format.

**Project hash**: derived from the project path by stripping the leading `/` and replacing `/` with `-`. Example: `/home/cody/workspace/garcia-music` → `home-cody-workspace-garcia-music`.

Content item types:
- `{"type": "text", "text": "..."}` — plain text
- `{"type": "tool_use", "name": "Task", "input": {"description": "...", "model": "...", "prompt": "...", "subagent_type": "..."}}` — agent spawn
- `{"type": "tool_result", ...}` — tool output
- User messages may wrap the real query in `<user_query>...</user_query>` tags

There are no timestamps in the JSONL. Use file mtime for ordering.

---

## Scripts

### `find.py` — session discovery

Lists all sessions for a project.

```
python3 tools/cursor/find.py [PROJECT_PATH] [--format text|json]
```

- `PROJECT_PATH` defaults to cwd
- Resolves the Cursor project hash automatically
- Output columns: `SESSION_ID`, `START_TIME`, `SUBAGENTS`, `PARENT_SIZE_BYTES`
- Start time is inferred from earliest file mtime in the session

Example:
```
python3 tools/cursor/find.py ~/workspace/garcia-music
SESSION_ID                             START_TIME                  SUBAGENTS  PARENT_BYTES
----------------------------------------------------------------------
87e55915-f481-4dcc-8b6a-54c69392fcf9   2026-06-25T12:37:53+00:00        67        451614
...
```

To find the most recent session with subagents:
```bash
python3 tools/cursor/find.py ~/workspace/garcia-music --format json | \
  python3 -c "import json,sys; ss=[s for s in json.load(sys.stdin) if s['subagent_count']>0]; print(ss[-1]['session_id'])"
```

---

### `extract.py` — structured extraction

Reads a session and outputs a normalised JSON document to stdout.

```
python3 tools/cursor/extract.py SESSION_ID [PROJECT_PATH]
```

- `SESSION_ID` can be a prefix (e.g. `87e55915`) — exits if ambiguous
- `PROJECT_PATH` defaults to cwd

Output document structure:
```json
{
  "session": {
    "id": "87e55915-...",
    "project_hash": "home-...",
    "start_time_iso": "2026-06-25T12:37:53+00:00",
    "end_time_iso": "2026-06-25T23:36:24+00:00",
    "parent_tool_counts": {"Task": 67, "Shell": 44, ...},
    "total_messages": 268,
    "subagent_count": 67
  },
  "task_calls": [
    {
      "seq": 0,
      "msg_idx": 6,
      "description": "Research player codebase",
      "model": "composer-2.5",
      "subagent_type": "",
      "prompt_len": 704,
      "prompt_first_200": "..."
    },
    ...
  ],
  "user_queries": [
    {"msg_idx": 11, "text": "This is not how the iterate skill..."}
  ],
  "subagents": [
    {
      "id": "db5f994e-...",
      "mod_time": 1782391073,
      "mod_time_iso": "2026-06-25T12:37:53+00:00",
      "file_size": 18401,
      "msg_count": 15,
      "tool_counts": {"Read": 12, "Shell": 8, ...},
      "total_tool_turns": 42,
      "direction_preview": "..."
    }
  ]
}
```

The extract output is the primitive consumed by `stats.py` and `iterate_analysis.py`. Cache it with tee if running multiple analyses:
```bash
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music > /tmp/session.json
cat /tmp/session.json | python3 tools/cursor/stats.py
cat /tmp/session.json | python3 tools/cursor/iterate_analysis.py
```

---

### `stats.py` — summary statistics

Reads extracted JSON from stdin (or re-extracts with `--session`) and prints summary statistics.

```
python3 tools/cursor/extract.py SESSION_ID PROJECT | python3 tools/cursor/stats.py [--format text|json]
python3 tools/cursor/stats.py --session SESSION_ID [PROJECT_PATH] [--format text|json]
```

Output sections:
- **Session Overview**: message count, task count, subagent count, wall time
- **Parent Tool Distribution**: ranked tool usage in the orchestrator
- **Model Breakdown**: per-model task count with prompt length statistics
- **Subagent Tool Distribution**: aggregated tool usage across all subagents
- **Subagent Size & Activity**: file size, message count, tool turn statistics

---

### `search.py` — transcript search

Searches message text across parent and subagent transcripts.

```
python3 tools/cursor/search.py SESSION_ID PROJECT_PATH PATTERN [options]
```

Options:
- `--regex` — treat PATTERN as a Python regex (default: substring)
- `--agent AGENT_ID` — search only in one subagent's transcript
- `--role user|assistant` — filter by role
- `--context N` — characters of context around match (default: 200)
- `--format text|json`

Examples:
```bash
# Find user corrections
python3 tools/cursor/search.py 87e55915 ~/workspace/garcia-music "not how the iterate"

# Find where a specific model was mentioned
python3 tools/cursor/search.py 87e55915 ~/workspace/garcia-music "glm-5.2" --role assistant

# Regex search for synthesis mentions
python3 tools/cursor/search.py 87e55915 ~/workspace/garcia-music "synthes(is|ize)" --regex

# Search only user messages for direction corrections
python3 tools/cursor/search.py 87e55915 ~/workspace/garcia-music "" --role user --regex "."
```

---

### `cost_window.py` — token attribution by time window

Ties a session to its token cost in the usage export (`usage-events-*.csv`).
The export has **no session/agent join key** — its `Cloud Agent ID` and
`Automation ID` columns are empty — so the only link is the session's wall-clock
window against the event timestamps. This script does that correlation and, by
comparing the in-window models against the models the session actually used (from
its Task calls), reports how trustworthy the window is.

```
python3 tools/cursor/extract.py SESSION_ID PROJECT | \
  python3 tools/cursor/cost_window.py --csv usage-events-2026-06-26.csv
```

Or with an explicit window (no extract, no session-model list):
```
python3 tools/cursor/cost_window.py --csv FILE \
  --start 2026-06-25T12:37 --end 2026-06-25T23:37
```

Options: `--csv FILE` (required), `--start`/`--end` (ISO prefixes), `--pad-minutes N`
(widen the session window each side, default 1), `--pricing FILE` (default
`tools/cursor/pricing.json`), `--no-pricing` (token-only), `--substitute FROM:TO`
(what-if), `--format text|json`.

Output: per-model token totals and event counts, foreign-model flags (models
in-window the session did **not** use), an attribution-confidence percentage, the
`Cost`-column label distribution, and — when `pricing.json` is present — a **dollar
cost split four ways** (cache_read / fresh_in / cache_write / output) with the
cache-read and output **cost shares** per model. `pricing.json` carries Cursor's
published per-Mtok rates; edit it to track rate changes. Cache read is typically
65–70% of the dollar cost on the bulk models, so model choice should be driven by
**cache_read price**, not output price.

What-if model substitution (the cost-optimisation lever):
```
... | python3 tools/cursor/cost_window.py --csv FILE --substitute glm-5.2-high:kimi-k2.5
# WHAT-IF: run glm-5.2-high tokens at kimi-k2.5 rates -> saves $5.03 (58%)
```

**Two facts this surfaces, not bugs:**
- The `Cost` column is `Included`/`Free`, never a dollar amount — subscription
  token-accounting, not billing. "Cost" means *tokens consumed*.
- Billing **events ≠ agents**: one agent emits many usage events (one per turn),
  so per-model token *totals* are reliable but per-agent attribution is not.

When piped from `extract.py` the window and session-model list are automatic; with
`--start/--end` there is no session-model list, so foreign-model flagging is off and
the tool cannot separate this session's spend from other in-window work.

---

### `iterate_analysis.py` — iterate workflow analysis

Classifies task calls into iterate workflow phases and detects alignment issues.

```
python3 tools/cursor/extract.py SESSION_ID PROJECT | python3 tools/cursor/iterate_analysis.py [--format text|json]
python3 tools/cursor/iterate_analysis.py --session SESSION_ID [PROJECT_PATH] [--format text|json]
```

**Phases classified**:

| Phase | Description |
|-------|-------------|
| `research` | Explores codebase, no writing |
| `plan` | Produces plan artifacts |
| `execute` | Builds code, runs tests |
| `divergence-gate` | Approves/rejects challenger plans |
| `synthesis` | Cross-candidate synthesis, selects winner |
| `consolidation-plan` | Plans consolidation onto winner |
| `consolidation-execute` | Builds consolidation |
| `review` | Comprehensive review |
| `extrapolate` | Top-3 next steps |
| `other` | Catch-all |

**Alignment issues detected**:

| Issue | Trigger |
|-------|---------|
| `orchestrator-absorbed-planning` | Execute agent appears before first plan agent in a cycle |
| `parallel-execution` | Two execute-phase Task calls at same `msg_idx` |
| `synthesis-repeated` | More than one synthesis agent in a cycle |
| `prompt-degradation` | Gate agent prompt_len drops >50% within a cycle |
| `sub-subagent` | A subagent's JSONL contains its own Task calls |

**Known classification limitations**:
- Descriptions with "execute" + "consolidat" but containing "plan" in a parenthetical (e.g. "Consolidation plan (no execution)") are handled by keyword order priority — check results manually.
- Descriptions without iteration-phase keywords fall to `other`.
- Post-review fix tasks ("Fix consolidation review findings") are classified as `review` not `execute`.

---

## Ad-hoc jq queries

With extracted JSON saved to file:

```bash
# Count task calls by phase (requires jq + iterate_analysis output)
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music | \
  python3 tools/cursor/iterate_analysis.py --format json | \
  jq '[.task_calls_classified[] | .phase] | group_by(.) | map({(.[0]): length}) | add'

# List models used in synthesis agents
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music | \
  python3 tools/cursor/iterate_analysis.py --format json | \
  jq '[.task_calls_classified[] | select(.phase == "synthesis") | {seq, model, description}]'

# Show all alignment issues
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music | \
  python3 tools/cursor/iterate_analysis.py --format json | \
  jq '.alignment_issues[] | "[" + .severity + "] " + .type + ": " + .evidence'

# Get subagents with most tool turns
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music | \
  jq '.subagents | sort_by(-.total_tool_turns) | .[:5] | .[] | {id: .id[:8], turns: .total_tool_turns}'
```

---

## Relationship to conv-index

These scripts are a fast-track standalone toolkit. The full `conv-index` CLI (child plans 01–03 in the conversation-indexer program) will add:
- SQLite indexing for cross-session queries
- The correct Cursor subagent format (parent JSONL + `subagents/` dir, confirmed by this toolkit)
- Backfill and multi-project support

Until that lands, these scripts are the primary way to analyse Cursor sessions.
