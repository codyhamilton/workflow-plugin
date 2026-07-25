# [NEW] Conversation Indexer: SQLite-Backed Programmatic Querying

## Intent

User request, verbatim:

> The current parser skill relies on instructions, but really what you want is a script that can allow programmatic queries of conversation logs. It should support opencode, cursor, claude code, codex, copilot. Start with opencode and cursor. We'd want to index conversation logs, store them efficiently, then provide a queryable interface. A simple method might be to index them into sqlite (at least the analytics, not all the log detail) How would you structure this?
>
> Check over the plan that was just created - what would you change?
>
> there wasn't really a plan created, we want to make one. I just meant re-think the previous message with its suggested approach, assess it critically. Then summarise the changes if any to the approach.

The accepted v1 scope (from the planning conversation):

- v1 ships opencode and claude-code parsers (shared format) and a cursor parser; copilot and codex are deferred.
- Output interface: Python library + CLI.
- Database: single global DB at `~/.conv-index/analytics.db`.
- Token data: per-message usage captured (input, output, cache_read, cache_creation).
- Cost model: out of scope for v1; data shape supports it as a v2 pure function.

## Why This Plan Exists

The current `transcript-parser` skill is instruction-based: the LLM is told how to read JSONL files and produce a markdown section. This is fragile in two ways:

1. **Reproducibility.** Different agents, or the same agent under different context pressure, produce different outputs from the same session. There is no canonical record.
2. **Queryability.** Ad-hoc markdown sections are not queryable. Cost comparisons across sessions, time-series of tool usage, and cross-project analytics are all out of reach.

This plan replaces the instruction-based parser with a real system: a Python library and CLI that parse session logs into a SQLite database designed for analytics queries, leaving the original skill to consume the indexed data.

The result: `transcript-parser` becomes a thin renderer that reads from the indexer rather than re-parsing JSONL on every invocation. The hard work — discovering sessions, parsing formats, normalizing tool names, tracking compaction events — moves into tested code.

## Scope

A new tool, `conv-index`, that:

1. Discovers conversation sessions on disk for opencode, claude-code, and cursor.
2. Parses each session's JSONL (or equivalent) into a normalized schema.
3. Stores analytics in a single global SQLite database.
4. Exposes a Python library for programmatic queries and a CLI for shell use.

A `cost-comparison` formatter that renders a session's analytics in the eval schema, replacing the ad-hoc markdown output the current skill produces.

Out of scope for v1: a cost/pricing model, copilot and codex parsers, manifest-based incremental discovery, working-directory change tracking, a web UI, and a server/MCP interface.

## Architectural Implications

- **New tool, new directory.** `conv_index/` at repo root, plus a `conv-index` console script. Independent of the workflow-plugin skills; lives alongside them as a peer tool.
- **`transcript-parser` skill becomes a consumer.** Once the indexer is in place, the skill can be simplified: query the DB instead of re-parsing JSONL. This is a follow-on plan, not part of v1.
- **New parent program.** This is a `[NEW]-` parent program in `docs/plans/` with three child plans. It is unrelated to `01-workflow-improvements`; that program is complete and stays as historical provenance.
- **No stable-doc changes.** `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` describe the workflow-plugin itself. The indexer is a separate tool, not a workflow-plugin skill. No edits to stable docs are required.
- **Python 3.10+ baseline.** Match the harness runtime. No exotic dependencies — stdlib `sqlite3` and `json` are sufficient for the core; `click` for the CLI; `pytest` for tests.

## Intent Validation

Five scope-shaping questions were asked in the planning conversation; all five recommendations were accepted. They are recorded in `PROVENANCE.md`. No further questions are open at the parent-program level.

Per-child-plan questions will be asked as the child plans are written and executed.

## Open Questions

- **Where does `conv_index/` live long-term?** In-repo alongside the workflow-plugin is fine for v1. A separate repo is plausible later. Defer the split decision until the indexer has users.
- **How does `transcript-parser` migrate to the indexer?** The current skill continues to work via the existing skill prompt. A follow-on plan will rewrite it to query the indexer. Not part of v1.
- **Does the indexer need to ship as a `pip install` package?** v1 ships as a checkout and `pip install -e .`. A proper release / PyPI is a v2 concern.

## Execution Phases

1. **Schema + opencode/claude-code parser + indexer core** (child plan `01-schema-and-opencode/`)
   - Project skeleton: `pyproject.toml`, package layout, `conv_index/` directory, `tests/` directory.
   - v1 schema in `conv_index/schema.sql` with migration `001_initial.sql`.
   - Parser interface (`parsers/base.py`) and `parsers/opencode.py` covering both opencode and claude-code.
   - `Indexer` class with staleness check (mtime vs `indexed_at`) and parse-status reporting.
   - `index_runs` table populated on every run.
   - Library types (`Session`, `Agent`, `Turn`) and a minimal query API.
   - Test fixture: one opencode session with one subagent under `tests/fixtures/`.
    - Minimal CLI: `conv-index index <project-path> [--tool X]`, `conv-index sessions [--project LABEL] [--tool X] [--since YYYY-MM-DD] [--limit N] [--format json|table]`, `conv-index session <tool> <id>`, `conv-index doctor`, `conv-index history`.

2. **Cursor parser** (child plan `02-cursor/`)
   - `parsers/cursor.py` reading `~/.cursor/projects/{hash}/agent-transcripts/{session}/`.
   - Tool-name normalization: map Cursor tool names to the canonical enum.
   - Cursor test fixture under `tests/fixtures/`.
   - Validates that the parser abstraction generalizes beyond the opencode format.

3. **CLI queries + cost-comparison formatter + polish** (child plan `03-cli-and-formatters/`)
   - Full query CLI: `conv-index stats`, `conv-index tool-usage`, `conv-index projects`.
    - `conv-index cost-comparison <tool> <id> [--format md|json] [--baseline <tool> <id>]` rendering in the eval schema (the schema from `evals/README.md`).
    - `conv-index` reindex-all and `--since YYYY-MM-DD` filtering.
   - Documentation: `conv_index/README.md` with usage examples.
   - Comprehensive tests for queries and formatters.

## Acceptance Criteria

- **Schema v1 exists and migrates cleanly.** `conv_index/schema.sql` defines all tables (sessions, session_projects, projects, agents, tool_turns, token_usage, compaction_events, index_runs, schema_version). Running the indexer on a fresh DB creates the schema and inserts a `schema_version` row. Running it again is a no-op.
- **Opencode and claude-code are parseable.** Given the test fixture (one opencode session with one subagent), the indexer populates `sessions`, `agents`, `tool_turns`, and `token_usage` correctly. The same parser handles a claude-code session without code changes.
- **Cursor is parseable.** Given a Cursor fixture, the cursor parser populates the same tables with `tool_name_canonical` normalized to the shared enum.
- **`delegates_to_agent_id` is set on parent turns that delegate to a subagent.** The schema makes the parent→subagent boundary queryable.
- **Token data is captured per message.** A `token_usage` row exists for every assistant message that reported usage. `peak_context_tokens` on the session equals `MAX(input + cache_read + cache_creation)` over its messages.
- **Compaction events are recorded.** A fixture session with a `/compact` boundary produces a `compaction_events` row.
- **Indexing is observable.** `index_runs` records started_at, ended_at, sessions_seen, sessions_indexed, sessions_errored. A session with a malformed JSONL row sets `parse_status='partial'` and records the error in `parse_errors`; indexing continues.
- **Identity is `(tool, session_id)`.** Two sessions with the same UUID under different tools are distinct rows. Renaming a project does not orphan historical data.
- **CLI works end-to-end.** `conv-index index` then `conv-index session <tool> <id>` returns structured data on a real project.
- **`cost-comparison` formatter emits the eval schema.** Output is paste-ready into `cost-comparison.md` and matches the section format from `skills/transcript-parser/SKILL.md`.
- **No credentials leak.** The fixture corpus and any real indexed data never include API keys, tokens, or full message bodies.

## Out of Scope (v1)

Explicit non-goals to prevent scope creep:

- Cost / pricing model and `cost_usd` computation. (Data capture supports it; the calculator is v2.)
- Copilot and codex parsers. (Storage research is a separate small task before they are scoped.)
- A `pip install` release. (Checkout and `pip install -e .` are sufficient for v1.)
- A web UI, server, or MCP interface.
- Live indexing of in-progress sessions. (v1 indexes completed sessions whose mtime is stable. Live support is v2.)
- Re-architecting the `transcript-parser` skill to query the indexer. (Follow-on plan.)
- Backfilling historical sessions across many projects. (The CLI exposes the operation; the user opts in.)

## Provenance Notes

This is a new parent program. It does not depend on the completed `01-workflow-improvements` program; both are independent, and both demonstrate the workflow-plugin by dogfooding it.

The progressive provenance model from `01-provenance-capture` is used here: PROVENANCE.md is written at the moment the request is captured, each Q&A turn is appended as it happens, and agent decisions are recorded before finalizing. This `PROVENANCE.md` is itself an example of the correct output shape.

If `conv_index/` grows beyond a single tool, this parent program can be split into a separate repository. For v1, in-repo is the right call: it keeps the change reviewable in one diff, and it lets the workflow-plugin use the indexer as soon as it lands.
