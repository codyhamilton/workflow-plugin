# 04 — Cursor Analysis Toolkit (Fast-Track)

## Intent

User request, verbatim:

> We have just used the iterate skill for a multi-cycle iteration for some significant changes to an existing repo. The repo is ~/workspace/garcia-music. The costing data is in @usage-events-2026-06-26.csv. The harness was cursor and its transcripts are available in ~/.cursor/projects (find the one relating to this work).
>
> What we should start with is analysing the transcript, thinking about what kind of data we'd want to pull out. I certainly want to consolidate the usage data into costings alongside the workflow, visualise how the workflow is working, assess the quality of the directions given to subagents and its alignment with the workflow. Initial steps should be to pull out data - the transcripts are too large for manual work - we need to pull out stats and important aspects that relate to workflow alignment

> Ok output analysis into a doc, but most importantly ensure the analysis tools are scriptable and easy for agents to run, and documented, so we can reduce manual discovery work. I'd like the tools to make it easy to just search/query/analyse conversation transcripts. ensure it works with cursor for now. First plan the changes and then delegate implementation

## Why This Plan Exists

The existing `[NEW]-conversation-indexer` program (child plans 01–03) provides the right long-horizon solution: a SQLite-backed indexer with a `conv-index` CLI. But it is currently unimplemented and begins with the OpenCode schema and parser — not Cursor.

There is an immediate need: a just-run 4-cycle iterate session in `~/workspace/garcia-music` produced 67 subagents whose data has been manually extracted at significant effort. That effort must not repeat. Agents need scriptable tools they can invoke without a prior indexing step or a DB installation.

This plan delivers standalone Python scripts that parse Cursor transcripts directly and a documented analysis of the garcia-music session. The scripts are designed so they can later be consumed by, or replaced by, the full `conv-index` CLI from child plans 01–03.

Additionally, child 02's PLAN.md contains an incorrect architectural assumption — it says Cursor sessions have "a single parent agent" with no subagent support. The Cursor format DOES store subagent transcripts (confirmed by inspecting a real session): the parent JSONL lives in `{session-dir}/{session-id}.jsonl` and subagents live in `{session-dir}/subagents/{agent-id}.jsonl`. This plan corrects that assumption.

## Scope

### 1. Toolkit scripts: `tools/cursor/`

Five standalone Python 3.10+ scripts. No external dependencies. No indexing step required. Each is individually callable with `--help` documentation.

**`find.py`** — session discovery
- Given a project path (default: `cwd`), resolves the Cursor project hash and lists all sessions under `~/.cursor/projects/{hash}/agent-transcripts/`
- Output: session IDs with start time (inferred from earliest subagent mtime), total subagents, parent JSONL size
- Format: `--format text|json`

**`extract.py`** — structured extraction
- Given a session ID and optional project path, reads the parent JSONL and all `subagents/*.jsonl`
- Outputs a normalized JSON document:
  - `session`: id, project_hash, parent_tool_counts, total_messages
  - `task_calls`: ordered list of `{seq, msg_idx, description, model, subagent_type, prompt_len, prompt_first_200}`
  - `user_queries`: ordered list of `{msg_idx, text}` (genuine user queries, not Cursor system messages)
  - `subagents`: ordered-by-mtime list of `{id, mod_time, file_size, msg_count, tool_counts, total_tool_turns, direction_preview}`
- This JSON is the input to all other tools

**`stats.py`** — summary statistics
- Reads extracted JSON (or re-extracts from session)
- Prints: total agents, tool distribution (parent + subagents), model breakdown per task call, prompt-length stats by agent role, wall time estimate from mtime range
- Format: `--format text|json`

**`search.py`** — transcript search
- Reads a session's parent JSONL and subagent JSONLs
- Searches message text for a pattern (substring or regex)
- Returns: `{agent_id, msg_idx, role, text_snippet}` matches
- Flags: `--regex`, `--agent <id>` (search one agent only), `--role user|assistant`

**`iterate_analysis.py`** — iterate-workflow analysis
- Reads extracted JSON (or re-extracts)
- Classifies each task call into an iterate phase using description + prompt heuristics:
  `research | plan | execute | divergence-gate | synthesis | consolidation-plan | consolidation-execute | review | extrapolate | other`
- Detects common alignment issues (heuristics):
  - Orchestrator doing own research (high Read/Shell counts before first Task call)
  - Parallel candidate execution (two Execute tasks at same msg_idx)
  - Synthesis running multiple times in one cycle
  - Prompt-length degradation in gate/execute agents across a cycle
  - Subagent spawning wrong model (execute agent with Task calls)
- Outputs: cycle structure, per-cycle agent counts, direction quality table (phase × prompt_len), alignment issues list with evidence
- Format: `--format text|json`

### 2. README: `tools/cursor/README.md`

Agent-oriented documentation:
- How to discover sessions for a project (`find.py`)
- How to extract session data (`extract.py`)
- How to run workflow analysis (`iterate_analysis.py`)
- Example invocations for common queries
- How to pipe JSON through jq for ad-hoc queries
- Note on the Cursor format (parent JSONL + subagents dir)

### 3. Analysis document: `docs/analysis/2026-06-25-garcia-music-iterate.md`

The full analysis of the garcia-music session (the one just completed), written as:
- A substantive record of what the session did and what the iterate workflow produced
- An example of what `iterate_analysis.py` produces, with the actual tool invocations shown inline
- Findings: session stats, cycle structure, cost breakdown by model/phase, alignment issues ranked by severity, direction quality trend, what worked

This document serves two purposes: provenance for the garcia-music work, and a living example of the toolkit in use.

### 4. Correction: `02-cursor/PLAN.md`

Update the "Architectural Implications" section to reflect the real Cursor subagent format. The current plan says:

> Subagents in Cursor. Cursor does not store subagent transcripts separately in v1. `agents` will be a single parent agent.

The correct description:

> Cursor DOES store subagent transcripts. The session directory contains a parent JSONL at `{session-id}.jsonl` and a `subagents/` subdirectory with `{agent-id}.jsonl` for each spawned agent. The v1 cursor parser must read both. This was confirmed by inspecting a real Cursor session with 67 subagents.

## Architectural Implications

- **No new dependencies on child plans 01–03.** The toolkit scripts are standalone and do not import from `conv_index/`. They can later be adapted as a thin shell around the conv-index library, but that is not required here.
- **`tools/` directory at repo root.** New top-level directory alongside `skills/`, `docs/`, `evals/`. Contains a `cursor/` subdirectory. Additional harnesses (opencode, copilot) can be added as peer subdirectories when those parsers land in the main program.
- **`docs/analysis/` directory.** New directory for session analysis artifacts. Not plan artifacts (which live in `docs/plans/`); rather, outputs of running the toolkit on real sessions.
- **`02-cursor` plan is corrected, not replaced.** Its scope still makes sense for the full SQLite integration. The fact that Cursor stores subagents is now known; the correction is additive.
- **No changes to stable docs.** The toolkit is a peer tool alongside the workflow-plugin skills, not a change to those skills.

## Open Questions

- **Iterate phase classification accuracy.** The heuristics (description + prompt keyword matching) are good-enough for the current session. They may need tuning when applied to sessions with different orchestrator styles. Record misclassifications as known limitations in the README.
- **Should `extract.py` cache its output?** Outputting to stdout and letting callers cache is simpler and more composable. No caching for v1.
- **How does this relate to the transcript-parser skill?** The toolkit scripts are more capable than the current skill. Post-program follow-on: update the `transcript-parser` skill to call `iterate_analysis.py` when the session is from Cursor.

## Execution Phases

1. **Toolkit scripts** (`tools/cursor/` — five scripts + README)
   - `find.py`, `extract.py`, `stats.py`, `search.py`, `iterate_analysis.py`
   - Each is self-contained, tested against the garcia-music session

2. **Analysis document** (`docs/analysis/2026-06-25-garcia-music-iterate.md`)
   - Written by running the toolkit against the session
   - Includes inline tool invocations showing how each section was produced

3. **02-cursor correction** (update `02-cursor/PLAN.md` subagent assumption)

4. **ROADMAP update** (add `04-cursor-toolkit` as the first shipped child plan)

Phases 1 and 2 can proceed in parallel. Phase 3 is a single-file edit. Phase 4 is the final bookkeeping step.

## Acceptance Criteria

- **`find.py` discovers the garcia-music session.** Running `python tools/cursor/find.py ~/workspace/garcia-music` returns the `87e55915` session with subagent count ≥ 60.
- **`extract.py` produces valid JSON.** Running `python tools/cursor/extract.py 87e55915 ~/workspace/garcia-music` produces a JSON document with `task_calls` count = 67 and `subagents` count = 67.
- **`iterate_analysis.py` classifies all 67 agents.** Every task call gets a phase label. At least 4 cycles are detected. At least 3 alignment issues are detected, including the cycle-01 orchestrator-absorbed-planning violation (task #3 description "Build candidate 1 naive player" before user correction at msg 11).
- **`search.py` finds user corrections.** Running with pattern "not how the iterate skill" finds the msg-11 correction.
- **`stats.py` reports model breakdown.** Output matches: composer-2.5 as majority model, glm-5.2-high for synthesis agents, at least one other model present.
- **README is agent-runnable.** A fresh agent reading only the README can discover and analyze the garcia-music session without additional instruction.
- **Analysis doc is self-contained.** A reader can understand the garcia-music session, the iterate workflow, and the alignment findings without running the tools.
- **`02-cursor` plan corrected.** The subagent assumption is updated with the real format description.

## Out of Scope

- SQLite indexing or persistence (that is child 01–03 territory)
- OpenCode or Claude Code parsers
- Cost/pricing model or `cost_usd` computation
- Full `conv-index` CLI integration
- Web UI, server, or MCP interface
- Backfilling or cross-session queries (require the SQLite backend)

## Relationship to Child Plans 01–03

This plan adds a Cursor-specific fast track without blocking on the SQLite schema. The correct long-term relationship:

- `04` ships first as standalone scripts
- `01` + `02` land the SQLite-backed conv-index with proper Cursor subagent support (using the correct format now documented here)
- `03` adds the full CLI, including `conv-index iterate-analysis` that calls the same logic as `tools/cursor/iterate_analysis.py`
- After `01–03` land, `tools/cursor/` scripts can be deprecated or kept as lightweight wrappers

Update the parent ROADMAP to reflect this resequencing.
