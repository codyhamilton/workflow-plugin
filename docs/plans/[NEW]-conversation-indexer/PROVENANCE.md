# Provenance: Conversation Log Indexer

## Session

- Session: Initial plan — critical assessment of architecture proposal (Jun 14, 2026)
- Timestamp: 2026-06-14T00:00:00Z
- CWD: /home/codyh/workspace/workflow-plugin

## Initial Request (verbatim)

> The current parser skill relies on instructions, but really what you want is a script that can allow programmatic queries of conversation logs. It should support opencode, cursor, claude code, codex, copilot. Start with opencode and cursor. We'd want to index conversation logs, store them efficiently, then provide a queryable interface. A simple method might be to index them into sqlite (at least the analytics, not all the log detail) How would you structure this?
>
> Check over the plan that was just created - what would you change?
>
> there wasn't really a plan created, we want to make one. I just meant re-think the previous message with its suggested approach, assess it critically. Then summarise the changes if any to the approach.

## Planning Conversation

### Turn 1

**User responded:** Confirmed: re-think the previous architecture proposal critically; summarise concrete changes rather than create a full plan doc yet.

**Agent decisions:**

- Treat the architecture proposal as a draft to be critiqued, not as plan truth.
- Produce a short summary of changes, not a full PLAN.md, until the user signals they want a full plan.

### Turn 2 — Scope-Shaping Decisions

The agent asked five scope-shaping questions; user accepted all five recommendations:

**Agent asked:** v1 tool scope?

**User responded:** opencode + claude-code first (shared format), then cursor; copilot and codex deferred until their storage is researched.

**Agent decisions:**

- v1 ships opencode and claude-code parsers; claude-code reuses the opencode parser because the JSONL format and storage path are identical.
- CursorParser is the second distinct parser to ship.
- Copilot and Codex are explicitly out of v1 scope; storage research is a separate small task.

**Agent asked:** Output interface?

**User responded:** Python library + CLI. Library exposes Session/Agent/Turn models; CLI is a thin wrapper.

**Agent decisions:**

- Project layout: `conv_index/` Python package plus `conv-index` console script. The library is the primary surface; the CLI delegates to it.
- Library types are the contract — they are what eval scenarios and downstream tools import.

**Agent asked:** Database location?

**User responded:** Single global DB at `~/.conv-index/analytics.db`.

**Agent decisions:**

- One SQLite file per user, not per project. Cross-project analytics is enabled by default.
- The `projects` table (a small extra table) handles the human-meaningful "which repo" association without using project as a partition key.

**Agent asked:** Token data capture granularity?

**User responded:** Per-message token usage (input, output, cache_read, cache_creation) for every assistant message.

**Agent decisions:**

- Add a `token_usage` table keyed by `(agent_id, message_index)`. This is the source of truth.
- `peak_context_tokens` is derived: `MAX(input + cache_read + cache_creation) over all messages` for a session.
- Per-agent rollups are computed views, not stored.

**Agent asked:** Cost model in v1?

**User responded:** Defer pricing to v2; capture data only.

**Agent decisions:**

- v1 captures per-message tokens. No `models` pricing table; no cost column.
- The schema and library are designed so v2 can add a `models` table and compute `cost_usd` as a pure function over `token_usage` without a backfill.

## Agent Decisions

Cross-cutting decisions appended before plan is finalized.

- **Scope of this turn**: the user asked for critical review, not a complete plan. Produce a concise change list with rationale; defer PLAN.md and DESIGN.md until the user confirms direction.
- **Stable doc alignment**: the conversation indexer is a new tool outside the current `workflow-plugin` skills. It does not yet fit into `01-workflow-improvements`; it likely belongs in a new `[NEW]-` parent program. Will surface this when the user signals they want a plan.
- **Tool support priority**: opencode + claude-code share a format; ship those first, then cursor; defer copilot and codex.
- **Cost model is out of v1 scope**: pricing is a v2 concern; data capture is shaped to make v2 a pure function over existing data.
- **Schema must support cost later without backfill**: every place `model` is recorded, also record `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens`. This is the constraint that drove the `token_usage` table into v1.
- **Identity is `(tool, session_id)`**: `project_hash`, `cwd`, and `git_remote` are metadata, not identity. A `projects` table maps human labels to sessions via a join table.
- **Cross-tool tool-name aggregation matters**: store `tool_name_raw` (what the source said) and `tool_name_canonical` (mapped to a small enum). Without this, `WHERE tool_name = 'Read'` misses Cursor's `read_file`.

## Plan Output Decisions

Decisions made when writing PLAN.md / DESIGN.md / child plans.

- **Parent program, three child plans.** Phases: (1) schema + opencode/claude-code parser + indexer core, (2) cursor parser validating the abstraction, (3) CLI queries + cost-comparison formatter + tests. This phasing keeps each child shippable and reviewable independently.
- **DESIGN.md is created.** Schema, parser interface, and CLI command surface all carry contracts that downstream child plans must obey. DESIGN.md reifies them once at the parent level so each child PLAN.md can reference rather than restate.
- **Claude Code and opencode share one parser.** Per the existing `transcript-parser` skill: same storage path, same JSONL format, same parent + subagents layout. The parser is `opencode` and the tool column stores `claude-code` for sessions discovered under that tool's distinct discovery path (or shared, since they're identical).
- **Schema migrations live in `conv_index/migrations/`.** v1 ships migration `001_initial.sql`. The `schema_version` table tracks applied versions. New migrations append; no destructive changes to applied migrations.
- **Library is the primary surface.** `conv_index` Python package exposes `Indexer`, `Session`, `Agent`, `Turn` types. The CLI is a thin wrapper. The library is what eval scenarios and downstream tools (e.g., a future `cost-comparison` formatter skill) import.
- **Tests are part of phase 1.** A minimal fixture corpus (one opencode session with one subagent) is shipped in `tests/fixtures/` so the parser and indexer are tested from day one. Cursor phase adds a Cursor fixture; CLI phase adds CLI tests.
- **Cost-comparison formatter is a phase 3 deliverable, not a primary command.** Phase 1 CLI exposes `conv-index index`, `conv-index sessions`, `conv-index session <id>`. Phase 3 adds `conv-index cost-comparison <id>` rendering the eval schema. This separates query from formatting.
