# 02 — Cursor Parser

## Intent

The second child of the [conversation-indexer](../PLAN.md) parent program. Add a Cursor parser that uses the same parser interface, schema, and library types as the opencode parser from child 01.

## Why This Plan Exists

Cursor is the second distinct format. It validates that the parser abstraction and the canonical tool-name enum from DESIGN.md generalize beyond the opencode format. If they don't, this is the cheapest place to discover that — before the cost-comparison formatter and the full CLI surface (child 03) are built on top.

It also gives the user real coverage of the two tools they explicitly named: opencode (with claude-code as a free bonus) and cursor.

## Scope

Add `conv_index/parsers/cursor.py` and a synthetic Cursor test fixture. The parser reads `~/.cursor/projects/{hash}/agent-transcripts/{session}/` and produces a `SessionRecord` that drops into the same schema and library types as the opencode parser.

Out of scope: copilot, codex, cost/pricing model, live session handling, the `transcript-parser` skill migration.

## Architectural Implications

- **No schema changes.** The cursor parser fits the existing schema. It uses `tool='cursor'`, the canonical tool-name enum, and the same `SessionRecord` shape.
- **Library types unchanged.** The cursor parser produces a `SessionRecord`; downstream code does not need to know which tool produced it.
- **Subagents in Cursor.** Cursor DOES store subagent transcripts. Confirmed by inspecting a real session with 67 subagents (garcia-music, 2026-06-25). The session directory contains a parent JSONL at `{session-id}/{session-id}.jsonl` and a `subagents/` subdirectory with one `{agent-id}.jsonl` per spawned agent. The v1 cursor parser must read both and produce one `AgentRecord` per subagent JSONL. The earlier assumption of "single parent agent, no subagents" was incorrect.

## Intent Validation

- **No scope-shaping questions.** The DESIGN.md already specifies the parser interface, the canonical tool-name enum, and the schema. This child plan implements against those contracts.

## Open Questions

- **Cursor version drift.** Cursor's transcript format may evolve. The parser must be tolerant of unknown fields and unknown tool names (mapping them to `'Other'`). If the format changes in a breaking way, that's a v2 problem.
- **Cursor's `agent-transcripts` directory layout.** v1 assumes the directory contains one or more JSONL files describing the session. The exact file naming and structure need to be confirmed by inspecting a real Cursor session during implementation.
- **Cursor token usage is not in the source.** Per DESIGN.md's "Cursor Token Usage Defaults", the parser populates `TokenUsageRecord` rows with all-zero values for cursor messages. This is observable: a query like `SELECT tool, SUM(input_tokens) FROM token_usage GROUP BY tool` shows zero for cursor. The `cursor-no-usage/` fixture and `test_cursor_no_usage.py` enforce this contract; downstream consumers must filter `WHERE tool != 'cursor'` for accurate cost data.

## Execution Phases

1. **Tool-name mapping for Cursor**
   - Extend `conv_index/normalize.py` with Cursor-specific mappings in the shared `normalize_tool_name` function.
   - Map `read_file` → `Read`, `run_command` → `Bash`, `edit_file` → `Edit`, `write_file` → `Write`, `glob` → `Glob`, `grep` → `Grep`, `web_fetch` → `WebFetch`, `todo_write` → `TodoWrite`, anything else → `Other`.
   - Tests in `tests/test_normalize.py` covering each mapping.

2. **Cursor parser**
   - `conv_index/parsers/cursor.py` implementing `BaseParser`.
   - `discover_sessions` walks `~/.cursor/projects/{hash}/agent-transcripts/`.
   - `get_raw_path` returns the session directory.
   - `parse_session` reads the JSONL file(s) in the directory.
   - Token usage, compactions, and parse errors handled per the BaseParser contract.
   - Subagent handling: emit a single parent agent. If a future Cursor version includes subagents, extend here.

3. **Parser registry**
   - `conv_index/parsers/registry.py` adds `cursor` to the registry.

 4. **Cursor fixture and tests**
   - `tests/fixtures/cursor/single/` — synthetic fixture with a few tool calls.
   - `tests/fixtures/cursor-no-usage/` — synthetic fixture where the source transcript has no `usage` field. Verifies the parser produces zero-default `TokenUsageRecord` rows.
   - `tests/fixtures/cursor/build_fixtures.py` (or extend the existing builder) generates the fixtures.
   - `tests/test_cursor_parser.py` — unit tests for the parser.
   - `tests/test_cursor_no_usage.py` — explicit test that the no-usage cursor fixture produces zero-default token rows and that all `tool_turns` rows still have correct `tool_name_canonical` values.
   - `tests/test_indexer_cursor.py` — end-to-end: index the fixture, query it back.

5. **Cross-tool query test**
   - A test that indexes both an opencode fixture and a cursor fixture, then queries with `--tool cursor` and confirms only the cursor rows are returned.
   - A test that runs `conv-index tool-usage` and confirms the normalized tool names from both tools are aggregated correctly.

## Acceptance Criteria

- **Cursor fixture indexes correctly.** Given the synthetic fixture, the indexer populates `sessions`, `agents`, `tool_turns`, and `token_usage` rows with `tool='cursor'`. `parse_status='success'`.
- **Cursor no-usage fixture indexes correctly.** Given the `cursor-no-usage/` fixture (no `usage` field in the source), the indexer populates `token_usage` rows with `input_tokens=0`, `output_tokens=0`, `cache_read=0`, `cache_creation=0`, and `tool_turns` rows with the correct `tool_name_canonical` values.
- **Tool names are normalized.** `tool_name_canonical` matches the enum for every `tool_turns` row, even when `tool_name_raw` is Cursor-specific.
- The `normalize_tool_name` function in `conv_index/normalize.py` handles Cursor tool names correctly when `tool='cursor'` is passed as the second argument.
- **Cross-tool aggregation works.** A query that joins across tools (e.g., `conv-index tool-usage` in child 03, or a unit test here) returns the right counts for `Bash`, `Read`, etc. across both tools.
- **Cursor session has a single agent.** No subagent rows are produced; `agents` for the cursor session has one row with `parent_agent_id IS NULL`.
- **Parser interface is not modified.** The cursor parser conforms to the existing `BaseParser` from child 01. No changes to `parsers/base.py` or `parsers/opencode.py`.
- **No credentials leak.** The synthetic fixture contains no real content.

## Out of Scope

- Cursor subagent support (Cursor does not store subagent transcripts in v1).
- Copilot and codex parsers.
- Cost/pricing model.
- Full CLI surface (child 03).

## Provenance Notes

This child is the validation step. If the opencode-specific decisions in DESIGN.md (canonical enum, parser interface, library types) do not generalize, this is where it shows. The fix should be small — adding a mapping or a registry entry — not a redesign. If a redesign is needed, that's a signal to revisit DESIGN.md before child 03 begins.
