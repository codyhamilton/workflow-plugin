---
name: transcript-parser
description: Parse an AI tool session transcript to extract cost metrics (agents spawned, tool turns per agent, tool type breakdown, context estimate, wall time) in eval cost-comparison format. Use after a plan-execute run to populate a cost-comparison.md, or during workflow-tuning to compare execution approaches.
---

# Transcript Parser

Use this skill to extract objective cost metrics from a session transcript and produce a section ready to paste into `cost-comparison.md` in the eval schema.

This skill covers Claude Code (primary), Cursor, and GitHub Copilot transcript formats.

## Session Location

### Identifying the session

Prefer in this order:
1. Session ID or slug provided directly by the user
2. `## Session` section in `IMPLEMENTATION.md` for the relevant plan
3. Most recently-modified session for the current project (auto-detect)

### Claude Code — finding the JSONL

Project hash = working directory path with every `/` replaced by `-`. The leading `/` naturally produces a leading `-` — no additional prefix needed.

Example: `/home/codyh/workspace/workflow-plugin` → `-home-codyh-workspace-workflow-plugin`

```
~/.claude/projects/{project-hash}/{session-id}.jsonl      — parent session
~/.claude/projects/{project-hash}/{session-id}/
  subagents/
    agent-{id}.meta.json    — {agentType, description, toolUseId}
    agent-{id}.jsonl        — full subagent transcript
  tool-results/             — persisted large tool outputs (ignore for cost metrics)
```

To auto-detect the most recent session for the current project:
```bash
python3 -c "
import os, json
cwd = os.getcwd()
proj_hash = cwd.replace('/', '-')
proj_dir = os.path.expanduser(f'~/.claude/projects/{proj_hash}')
files = sorted(
    [f for f in os.listdir(proj_dir) if f.endswith('.jsonl')],
    key=lambda x: os.path.getmtime(os.path.join(proj_dir, x)),
    reverse=True
)
if files:
    with open(os.path.join(proj_dir, files[0])) as f:
        for line in f:
            obj = json.loads(line)
            if 'sessionId' in obj:
                print('session-id:', obj['sessionId'])
                print('slug:', obj.get('slug'))
                break
"
```

### Cursor — finding the transcript

```
~/.cursor/projects/{project-name}/agent-transcripts/{session-id}/
```

`project-name` is the absolute path with leading `/` stripped, then remaining `/` replaced by `-` (e.g. `home-codyh-workspace-workflow-plugin`). Session ID is the directory name (UUID or timestamp string). If not captured in IMPLEMENTATION.md, find the most recently-modified directory:

```bash
ls -lt ~/.cursor/projects/$(pwd | sed 's|^/||;s|/|-|g')/agent-transcripts/ 2>/dev/null | head -5
```

### GitHub Copilot — finding the transcript

```
~/.copilot/session-state/{session-id}/events.jsonl
~/.copilot/session-store.db             — SQLite index if you need to query by date
```

Use event types `tool.execution_start` / `tool.execution_end` to reconstruct tool loops.

## Parsing — Claude Code

Use a single Python script to extract all metrics at once. This avoids repeated file reads.

```python
import json, os, glob
from datetime import datetime, timezone

PROJ_HASH = os.getcwd().replace('/', '-')
SESSION_ID = '<session-id>'   # fill in
PROJ_DIR = os.path.expanduser(f'~/.claude/projects/{PROJ_HASH}')
SESSION_FILE = os.path.join(PROJ_DIR, f'{SESSION_ID}.jsonl')
SUBAGENT_DIR = os.path.join(PROJ_DIR, SESSION_ID, 'subagents')

def parse_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]

def count_tool_loops(messages, is_parent=True):
    """Count tool_use blocks in assistant messages."""
    counts = {}
    for msg in messages:
        if msg.get('type') != 'assistant':
            continue
        if is_parent and msg.get('isSidechain'):
            continue
        for item in msg.get('message', {}).get('content', []):
            if isinstance(item, dict) and item.get('type') == 'tool_use':
                name = item.get('name', 'unknown')
                counts[name] = counts.get(name, 0) + 1
    return counts

# Parse parent session
parent_msgs = parse_jsonl(SESSION_FILE)
parent_tool_counts = count_tool_loops(parent_msgs)
parent_total = sum(parent_tool_counts.values())

# Timestamps (wall time)
timestamps = [
    msg['timestamp'] for msg in parent_msgs
    if 'timestamp' in msg and msg.get('type') in ('user', 'assistant')
]
first_ts = min(timestamps) if timestamps else None
last_ts = max(timestamps) if timestamps else None

# Context estimate (from first assistant response with usage)
context_estimate = None
for msg in parent_msgs:
    usage = msg.get('message', {}).get('usage')
    if usage:
        context_estimate = (
            usage.get('input_tokens', 0) +
            usage.get('cache_read_input_tokens', 0) +
            usage.get('cache_creation_input_tokens', 0)
        )
        break

# Parse subagents
subagents = []
if os.path.isdir(SUBAGENT_DIR):
    for meta_file in sorted(glob.glob(os.path.join(SUBAGENT_DIR, '*.meta.json'))):
        with open(meta_file) as f:
            meta = json.load(f)
        agent_id = os.path.basename(meta_file).replace('.meta.json', '')
        jsonl_path = os.path.join(SUBAGENT_DIR, f'{agent_id}.jsonl')
        sub_msgs = parse_jsonl(jsonl_path) if os.path.exists(jsonl_path) else []
        
        # Get model from first assistant message
        sub_model = None
        for m in sub_msgs:
            sub_model = m.get('message', {}).get('model')
            if sub_model:
                break
        
        sub_counts = count_tool_loops(sub_msgs, is_parent=False)
        subagents.append({
            'type': meta.get('agentType', 'unknown'),
            'description': meta.get('description', ''),
            'model': sub_model or 'unknown',
            'tool_counts': sub_counts,
            'total': sum(sub_counts.values()),
        })

# Output
print(f'Parent tool turns: {parent_total} {parent_tool_counts}')
print(f'Subagents: {len(subagents)}')
for i, sa in enumerate(subagents):
    print(f'  [{i+1}] {sa["type"]} ({sa["model"]}): {sa["total"]} turns {sa["tool_counts"]}')
    print(f'       "{sa["description"]}"')
if first_ts and last_ts:
    dt0 = datetime.fromisoformat(first_ts.replace('Z', '+00:00'))
    dt1 = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
    delta = dt1 - dt0
    mins, secs = divmod(int(delta.total_seconds()), 60)
    print(f'Wall time: {mins}:{secs:02d}')
if context_estimate is not None:
    print(f'Context estimate (first response, approximate): {context_estimate:,} tokens')
```

### Parsing — Cursor

Cursor JSONL uses `role` / `message.content[].type` structure. Count `tool_use` items across all assistant messages. Cursor does not store subagent breakdowns separately; report total tool turns only.

### Parsing — GitHub Copilot

Count pairs of `tool.execution_start` + `tool.execution_end` events per `toolName`. Each matched pair = one tool turn. Group by `turnId` to attribute turns to conversational rounds.

## Output Format

Produce a completed section matching the `cost-comparison.md` schema from `evals/README.md`. Specify whether this is Baseline or Candidate:

```markdown
## Candidate

- Agents spawned: <N> × <model> (<type>), <N> × <model> (<type>), ...
- Tool use turns (per agent):
  - parent: <N> turns (Bash: N, Read: N, Edit: N, Agent: N, ...)
  - agent-1 [<type>, <model>]: <N> turns (Bash: N, Read: N, ...)
  - agent-2 [<type>, <model>]: <N> turns (...)
- Tool use turns (total): <sum>
- Context estimate: <N> tokens (approximate — first response only, Claude Code)
- Wall time: <M:SS>
```

If context is unavailable (Cursor, Copilot): write `not available (source: <reason>)`.

## Workflow

1. **Identify the session** — read IMPLEMENTATION.md Session section, accept user input, or auto-detect most recent session for current project.
2. **Locate the transcript** — determine the tool (Claude Code, Cursor, Copilot) and resolve the full path(s) using the formulas above.
3. **Parse the parent transcript** — run the extraction script; collect tool loop counts, wall time, context estimate.
4. **Parse each subagent** (Claude Code) — read `subagents/*.meta.json` and corresponding `.jsonl`; extract type, model, tool counts.
5. **Format and output** — write the completed `## Candidate` or `## Baseline` section in eval schema format. Note any fields that are unavailable and why.

## Rules

- Report what is in the transcript. Do not estimate counts you cannot read.
- Mark unavailable fields explicitly: `not available (source: <reason>)`.
- Context estimate is always approximate — note this in the output.
- Agent tool_use calls in the parent count as parent tool turns; they are also the delegation boundary for subagent attribution.
- If a session has no subagent directory, report "0 subagents" and parent-only metrics.
- For Cursor and Copilot, report total tool turns only unless subagent breakdowns are available in the format.
