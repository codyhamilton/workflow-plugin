---
name: transcript-parser
description: Parse an AI tool session transcript to extract cost metrics (agents spawned, tool turns per agent, tool type breakdown, context estimate, wall time) in eval cost-comparison format. Use after a plan-execute run to populate a cost-comparison.md, or during workflow-tuning to compare execution approaches.
---

# Transcript Parser

Use this skill to extract objective cost metrics from a session transcript and produce a section ready to paste into `cost-comparison.md` in the eval schema.

This skill covers opencode and Claude Code (primary), Cursor, and GitHub Copilot transcript formats. opencode and Claude Code share the same storage location and JSONL format.

## Session Location

### Identifying the session

Prefer in this order:
1. Session ID or slug provided directly by the user
2. `## Session` section in `IMPLEMENTATION.md` for the relevant plan
3. Most recently-modified session for the current project (auto-detect)

### opencode / Claude Code — finding the JSONL

Both opencode and Claude Code store sessions in the same location and format. Auto-detect by checking the `OPENCODE_RUN_ID` environment variable first.

Project hash = working directory path with every `/` replaced by `-`. The leading `/` naturally produces a leading `-` — no additional prefix needed.

Example: `/home/codyh/workspace/workflow-plugin` → `-home-codyh-workspace-workflow-plugin`

```
~/.claude/projects/{project-hash}/{session-id}.jsonl      — parent session
~/.claude/projects/{project-hash}/{session-id}/
  subagents/
    agent-{id}.meta.json    — {agentType, description, toolUseId}
    agent-{id}.jsonl        — full subagent transcript (opencode adds `slug` and `agentId` fields)
  tool-results/             — persisted large tool outputs (ignore for cost metrics)
```

Auto-detection (preferring `OPENCODE_RUN_ID`, then the most recently modified `.jsonl` in the project's session directory) is built into `scripts/parse_session.py` — run it with no `session-id` argument. See Parsing below.

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

## Parsing — opencode / Claude Code

Both tools use the same JSONL format. Run `scripts/parse_session.py` (beside this file) to extract all metrics in a single pass — this avoids repeated file reads:

```bash
python3 scripts/parse_session.py [session-id]
```

Omit `session-id` to auto-detect (see Session Location above). Requires only the Python 3 standard library. It prints:

- parent tool-turn counts, broken down by tool
- subagent count, and per-subagent type, model, and tool-turn counts
- wall time (from first to last parent message timestamp)
- an approximate context estimate (input + cache-read + cache-creation tokens from the first assistant response with usage data)

Feed this output directly into the Output Format below.

### Parsing — Cursor

Cursor JSONL uses `role` / `message.content[].type` structure. Count `tool_use` items across all assistant messages. Cursor does not store subagent breakdowns separately; report total tool turns only.

### Parsing — GitHub Copilot

Count pairs of `tool.execution_start` + `tool.execution_end` events per `toolName`. Each matched pair = one tool turn. Group by `turnId` to attribute turns to conversational rounds.

## Known Gotchas

- **Counting real API calls / summing usage.** A `type: "assistant"` JSONL line is one
  content block, not one API call — a response that reasons before acting logs a `thinking`
  fragment and a `tool_use` fragment as two lines sharing the same `message.id` and identical
  `usage`. Raw line counts roughly double the true call count for any such response, and
  summing `usage` per raw line double-counts cost. `parse_session.py` already avoids this by
  counting `tool_use` blocks rather than lines; if you're counting or summing usage by hand,
  dedupe by `message.id` first.
- **Cache resets on agent resume.** `cache_read_input_tokens` can collapse back to near-zero
  baseline at a resume (e.g. via `SendMessage`) regardless of elapsed wall time — observed
  after a gap as short as 0.2 minutes, which rules out simple TTL expiry. It's a
  resume-structural effect (the resume prompt likely invalidates the cached prefix), not a
  clock. Expect a resumed agent's next call to cost roughly 6-8x a normal call at that
  context depth.

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
- Context estimate: <N> tokens (approximate — first response only, opencode / Claude Code)
- Wall time: <M:SS>
```

If context is unavailable (Cursor, Copilot): write `not available (source: <reason>)`.

## Workflow

1. **Identify the session** — read IMPLEMENTATION.md Session section, accept user input, or auto-detect most recent session for current project.
2. **Locate the transcript** — determine the tool (opencode, Claude Code, Cursor, Copilot) and resolve the full path(s) using the formulas above.
3. **Parse (opencode / Claude Code)** — run `scripts/parse_session.py`; it covers both the parent transcript and every subagent (`subagents/*.meta.json` + corresponding `.jsonl`) in one pass, printing tool loop counts, wall time, and context estimate. For Cursor and Copilot, apply the formulas above by hand.
4. **Format and output** — write the completed `## Candidate` or `## Baseline` section in eval schema format. Note any fields that are unavailable and why.

## Rules

- Report what is in the transcript. Do not estimate counts you cannot read.
- Mark unavailable fields explicitly: `not available (source: <reason>)`.
- Context estimate is always approximate — note this in the output.
- Agent tool_use calls in the parent count as parent tool turns; they are also the delegation boundary for subagent attribution.
- If a session has no subagent directory, report "0 subagents" and parent-only metrics.
- For Cursor and Copilot, report total tool turns only unless subagent breakdowns are available in the format.
