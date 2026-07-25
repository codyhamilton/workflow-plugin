# 01 — Schema and Opencode/Claude-Code Parser + Indexer Core

## Intent

The first child of the [conversation-indexer](../PLAN.md) parent program. Land the foundation: project skeleton, schema v1, parser interface, opencode/claude-code parser, indexer core, library types, test fixture, and a minimal CLI.

## Why This Plan Exists

Without a schema and a working parser for at least one tool, the rest of the program is unanchored. The cursor parser (02) and the CLI/formatters (03) are adaptations and consumers; both depend on a tested `conv_index` library.

This plan is also the proof of concept: it demonstrates that the parent program's design (parser abstraction, normalized schema, incremental indexing, observability) works on real opencode JSONL files.

## Scope

Deliver the first runnable version of the indexer that:

1. Compiles and installs (`pip install -e .`).
2. Initializes a SQLite DB at `~/.conv-index/analytics.db`.
3. Discovers opencode and claude-code sessions in `~/.claude/projects/{project_hash}/`.
4. Parses parent and subagent JSONL into `SessionRecord` / `AgentRecord` / `TurnRecord` / `TokenUsageRecord` / `CompactionEvent`.
5. Upserts them into the schema.
6. Exposes library types and a query API.
7. Exposes a minimal CLI: `conv-index init`, `conv-index index <project-path> [--tool X]`, `conv-index sessions`, `conv-index session <tool> <id>`, `conv-index doctor`.

Out of scope: cursor parser (02), cost-comparison formatter (03), full CLI surface (03), the `transcript-parser` skill migration (post-program).

## Architectural Implications

- **New directory at repo root**: `conv_index/`. Independent of `skills/` and `docs/`. Adds a `pyproject.toml`.
- **Stable docs unchanged.** `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` describe the workflow-plugin; the indexer is a separate tool and does not modify them.
- **No coordination with other plans.** The three child plans are sequenced; this one has no upstream dependency.

## Intent Validation

No further questions at the child-plan level. The parent PLAN.md and DESIGN.md captured all scope-shaping decisions. Open questions are recorded in the parent program.

## Open Questions

- **Live session handling.** v1 indexes sessions whose mtime is older than the most recent assistant message (i.e., the session looks complete). Detecting "live" requires tracking the last user prompt, which adds complexity. Defer to v2.
- **Should the indexer follow symlinks in `~/.claude/projects/`?** Recommend no for v1; add a `--follow-symlinks` flag in v2 if needed.

## Execution Phases

1. **Project skeleton**
   - `pyproject.toml` (Python 3.10+, deps: `click`, `pytest`; dev deps)
   - `conv_index/__init__.py` exposing the library types
   - `conv_index/schema.sql` containing the v1 DDL from DESIGN.md
   - `conv_index/migrations/001_initial.sql` referencing the same DDL
    - `tests/__init__.py` and `tests/conftest.py` with a `tmp_db` fixture (wrapping `tmp_path`), a `frozen_time` fixture using `freezegun`, and a subprocess E2E harness for `conv-index` binary tests

2. **Parser interface and opencode parser**
   - `conv_index/parsers/__init__.py` exporting the registry
   - `conv_index/parsers/base.py` with the `BaseParser` abstract class and dataclasses
   - `conv_index/normalize.py` with `normalize_tool_name(raw, tool) -> canonical`
   - `conv_index/parsers/opencode.py` covering both opencode and claude-code
   - `conv_index/parsers/registry.py` with `get_parser(tool: str) -> BaseParser`

3. **Indexer core**
   - `conv_index/indexer.py` with `Indexer` class
   - Migration runner: applies pending SQL files in order, records in `schema_version`
   - `index_project(project_path, tools)` with staleness check (mtime vs `indexed_at`)
   - `upsert_session(SessionRecord)` in a single transaction
   - `IndexRunReport` dataclass returned to the caller
    - `conv_index/query.py` with the canonical library API from DESIGN.md: `list_sessions(...)`, `get_session(tool, id)`, `list_projects()`, `get_project(label)`, `attach_project(tool, session_id, label)`, `history()`, `doctor()`. `stats()` and `tool_usage()` are stubbed here; full implementations land in child 03.

4. **Library types and minimal CLI**
   - Library dataclasses in `conv_index/__init__.py` (Session, Agent, Turn, TokenUsage, Compaction)
   - `conv_index/cli.py` with `click` group and the four commands
   - `conv-index init` → creates the DB
    - `conv-index index <project-path> [--tool X]` → runs the indexer
    - `conv-index sessions [--project LABEL] [--tool X] [--since YYYY-MM-DD] [--limit N] [--format json|table]` → tabular (default) or JSON output to stdout
    - `conv-index session <tool> <id>` → JSON output of the full session tree

 5. **Test fixture and tests**
   - Fixtures are generated synthetically by `tests/fixtures/build_fixtures.py` (not a copy of real session data). The generator rejects any content matching `sk-[A-Za-z0-9]{20,}`, `BEGIN PRIVATE KEY`, `ghp_`, or `xoxb-` patterns. Real session data must never be committed.
   - Required fixture scenarios (per DESIGN.md's Test Strategy): `opencode/session-with-subagent/`, `claude-code/simple/`, `malformed/`, `malformed-structural/`, `empty/`, `deeply-nested/`, `same-uuid-different-tool (cross-tool identity verification)`, `multi-compact/`, `cross-day/`, `grown-on-disk/`. (`cursor/` fixtures are in child 02.)
   - `tests/test_opencode_parser.py` — unit tests for the parser, including subagent resolution, malformed rows, orphaned sidechain fallback, and the tool-format discriminator
   - `tests/test_normalize.py` — tool-name normalization mapping for all known tools
   - `tests/test_indexer.py` — indexer upsert, staleness check, summary-column recomputation
   - `tests/test_migrations.py` — `init` idempotence; a test that simulates a future migration 002 by inserting a fake `002_*.sql` and verifying it applies on the next indexer start (not just on `init`)
   - `tests/test_query.py` — query API on indexed fixtures
   - `tests/test_cli.py` — `click.testing.CliRunner` smoke tests plus `subprocess.run` E2E tests
   - `tests/test_failure_paths.py` — `PermissionError`, `SQLiteError`, missing project dir, file deleted between discovery and parse, lock contention
   - `tests/test_privacy.py` — post-index scan of the DB for credential patterns; asserts the generator rejects seeded patterns
   - `tests/test_concurrency.py` — two indexer threads with a shared DB; verifies the second blocks or fails cleanly
   - `tests/test_parser_snapshot.py, tests/test_scanner.py, tests/test_init_detection.py` — snapshot test of `parse_session` output, catching normalization regressions

## Acceptance Criteria

- **Project installs.** `pip install -e .` succeeds; `conv-index --help` prints the command list.
- **DB initializes.** `conv-index init` creates `~/.conv-index/analytics.db` (mode 0600) inside a parent directory at mode 0700, applies migration 001 inside a transaction, and inserts a `schema_version` row. Running `conv-index init` again is a no-op (the lock protects against concurrent inits, and the migration runner detects no pending migrations). The connection runs `PRAGMA journal_mode=WAL;` and `PRAGMA foreign_keys=ON;`.
- **Migration runner triggers on every indexer start.** Running `conv-index init` applies pending migrations. Running `conv-index index` (or any other command that opens the DB) also applies any pending migrations. A simulated future migration 002 lands on the next indexer start, not only on `init`.
- **Opencode fixture indexes correctly.** Given the synthetic fixture with one parent and one subagent:
  - `sessions` has one row with `parse_status='success'`, `parser_version` set to the current conv_index version, and the four timestamp columns in ISO 8601 UTC.
  - `agents` has two rows (parent + subagent), with `parent_agent_id` set on the subagent.
  - `tool_turns` covers the parent's tool calls and the subagent's tool calls, with `message_index` linking each turn to the assistant message that produced it.
  - The parent's `Agent` tool-use turn has `delegates_to_agent_id` pointing at the subagent.
  - `token_usage` has one row per assistant message that reported usage.
  - `peak_context_tokens` equals the max of `input + cache_read + cache_creation` over all `token_usage` rows for the session.
  - `compaction_events` has one row for the `/compact` boundary.
  - Summary columns (`wall_time_sec`, `active_time_sec`, `peak_context_tokens`) are recomputed inside the same transaction as the upsert; a re-index that produces a different turn set replaces the old values.
- **Claude-code fixture indexes correctly.** The same parser indexes a claude-code fixture without code changes. The `tool-format discriminator` correctly identifies the file as claude-code (vs opencode) by the `sessionId` camelCase check.
- **Malformed row is handled.** The `malformed/` fixture sets `parse_status='partial'` and records the error in `parse_errors`; the rest of the session is indexed. The `malformed-structural/` fixture sets `parse_status='failed'` and still records the session.
- **Staleness check works.** Re-indexing a session whose mtime has not changed does not re-parse. Re-indexing after a mtime change does. The `grown-on-disk/` fixture verifies this. Sessions whose mtime is within the Session Completeness grace period follow the two-case rule: never-before-seen sessions are skipped entirely (counted in `index_runs.sessions_skipped`); previously-indexed sessions have their `parse_status` set to `'live'` and data kept intact.
- **Empty and deeply-nested fixtures index correctly.** The `empty/` fixture produces a `SessionRecord` with empty agent list and a `parse_status='success'` row. The `deeply-nested/` fixture produces a 3+ level agent tree with a chain of `delegates_to_agent_id` values.
- **Multi-compaction and cross-day fixtures index correctly.** The `multi-compact/` fixture produces 3+ `compaction_events` rows. The `cross-day/` fixture produces a session whose `started_at` and `ended_at` are on different UTC days.
- **Orphaned sidechain fallback works.** A test session with a sidechain message missing both `input.subagent_type` and `toolUseId` produces a `parse_errors` entry naming the orphan, and the sidechain's turns are attached to a synthetic `orphan-{session_id}-{n}` agent.
- **CLI commands work.** `conv-index sessions` lists the indexed fixture; `conv-index session opencode <id>` prints a JSON tree; `conv-index doctor` reports WAL=on, FK=on, file mode 0600; `conv-index history` returns rows after a run.
- **Lock contention exits with code 3.** Starting a second `conv-index index` while the first is running exits with code 3 and a clear error message naming the locked path.
- **No credentials leak.** The synthetic fixture, the parser output, and the post-index DB contain no real keys, tokens, message bodies, or `arguments` content. A `test_privacy.py` scan verifies this.
- **Tests pass.** `pytest` runs all tests green, including failure-path, privacy, concurrency, snapshot, and migration tests.

## Out of Scope

- Cursor parser, cost-comparison formatter, full CLI surface (children 02 and 03).
- Live session handling, symlink following, manifest-based incremental discovery (v2).
- `transcript-parser` skill migration (post-program follow-on).

## Provenance Notes

This is the foundational child. The parser interface, schema, and library types defined here are the contracts that 02 and 03 build on. The synthetic test fixture generator (`tests/fixtures/build_fixtures.py`) is the only place that creates JSONL; the rest of the test corpus is generated, not copied from real sessions, to avoid leaking private content.

The indexer is intentionally permissive on parse errors: a single malformed row should not block the rest of the session from being indexed. This is observable via `parse_status` and `index_runs.sessions_errored`.
