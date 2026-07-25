# 03 — CLI Queries and Cost-Comparison Formatter

## Intent

The third child of the [conversation-indexer](../PLAN.md) parent program. Land the full CLI query surface, the `cost-comparison` formatter that renders a session in the eval schema, and the user-facing documentation.

## Why This Plan Exists

Children 01 and 02 produced a tested library and a minimal CLI. This child turns that into a real tool: a CLI that answers common analytics questions (tool usage frequency, project rollups, time-series stats) and a `cost-comparison` formatter that replaces the ad-hoc markdown output the current `transcript-parser` skill produces.

The cost-comparison formatter is the bridge to the existing eval system. Once it ships, future eval runs can use `conv-index cost-comparison <tool> <id>` to populate `cost-comparison.md` mechanically rather than relying on the LLM to follow the parser instructions.

## Scope

Add the remaining CLI commands from DESIGN.md, the cost-comparison formatter, and a `conv_index/README.md`. Add tests for every command and the formatter.

Out of scope: a web UI, an MCP/server interface, a `pip install` release, the `transcript-parser` skill rewrite, cost/pricing model.

## Architectural Implications

- **No schema or library changes.** The library from child 01 is the contract. This child plan adds CLI commands and a formatter; both consume the library.
- **The `cost-comparison` formatter is a peer of the library, not a child of the CLI.** It can be called from Python: `from conv_index.formatters.cost_comparison import render; print(render(session))`. The CLI command is a thin wrapper.
- **Documentation lives at the package level.** `conv_index/README.md` describes installation, quickstart, and command reference. It is the first thing a new user reads.

## Intent Validation

- **No scope-shaping questions.** The parent PLAN.md and DESIGN.md captured the full CLI surface. This child implements against those contracts.

## Open Questions

- **`cost-comparison` Baseline + Candidate side-by-side.** The eval schema has both. Implemented as a `--baseline <tool> <id>` flag (per DESIGN.md); default behavior is a single session. The multi-session design ships in v1 because the eval run can use it immediately.
- **Output formats.** Per DESIGN.md, output commands accept `--format json|table` (default `table` for stats/sessions/etc., `md` for cost-comparison). The cost-comparison formatter also supports `--format json` for downstream tools.
- **Project label mutability.** v1 supports `project attach` and `project <label>` (read). Renaming a label and deleting a label are not in the v1 CLI; the `session_projects` table is append-only. A v2 command can add label mutation.
- **`conv-index history` and `conv-index doctor`.** Both ship in v1 per DESIGN.md. `history` reads `index_runs`; `doctor` reports schema version, WAL mode, FK enforcement, file permissions, lock status.

## Execution Phases

 1. **Stats and tool-usage queries**
    - `conv_index/query.py` `stats(...)` returns aggregate counts and durations, parameterized by `project`, `tool`, `since`, and `group_by`. `group_by` accepts `tool`, `agent_type`, `day`, `week`, `project`, `model` (per DESIGN.md).
    - `conv_index/query.py` `tool_usage(...)` returns `(tool_name_canonical, count)` rows, parameterized by `project`, `tool`, `since`.
    - CLI: `conv-index stats --group-by <value>` and `conv-index tool-usage`, both with `--format json|table`, `--quiet`, and the standard filters.
    - Tests: each command tested against the synthetic fixtures from children 01 and 02. Output format and column alignment are tested.

 2. **Projects command and cross-tool queries**
    - `conv_index/query.py` `list_projects()`, `get_project(label)`, and `attach_project(tool, session_id, label)` (the latter was introduced in DESIGN.md's Library API Naming).
    - CLI: `conv-index projects` (list), `conv-index project <label>` (show), and `conv-index project attach <tool> <id> <label>` (write).
    - Tests covering project attach, project detail query, and the `sessions --project` filter from child 01.
    - `conv_index/query.py` `history(limit=20)` reads `index_runs`; `doctor()` returns DB health dict. CLI wrappers: `conv-index history` and `conv-index doctor`.

3. **Cost-comparison formatter**
   - `conv_index/formatters/__init__.py` and `conv_index/formatters/cost_comparison.py`.
   - `render(session: Session) -> str` returns Markdown in the eval schema.
   - `render_json(session: Session) -> dict` returns structured data.
   - CLI: `conv-index cost-comparison <tool> <id> [--format md|json] [--baseline <tool> <id>]`.
   - Tests: snapshot tests against known session fixtures, including one with a subagent and one without.
   - The output matches the section format from `skills/transcript-parser/SKILL.md`.

 4. **Reindex-all, --since filter, and reset/vacuum**
    - `conv_index/indexer.py` `index_all(tools=None, since=None)`.
    - CLI: `conv-index index --all` and `conv-index index --since 2026-01-01` (per DESIGN.md, `--since` accepts ISO 8601 `YYYY-MM-DD`).
    - CLI: `conv-index reset --yes` deletes the DB and re-initializes; `conv-index vacuum` runs `VACUUM` to reclaim disk space.
    - Tests covering the time-window filter, the reset path (with a fresh DB afterwards), and the vacuum path (file size shrinks after a delete-and-reindex).

5. **Documentation and packaging polish**
   - `conv_index/README.md` with installation, quickstart, command reference, and a worked example.
   - Update root `README.md` with a one-paragraph pointer to `conv_index/`.
   - Verify `pyproject.toml` has the right entry points and metadata.

6. **End-to-end test**
   - A test that indexes both an opencode and a cursor fixture, then runs every CLI command and asserts on output.

## Acceptance Criteria

- **All CLI commands work.** `conv-index --help` lists every command from DESIGN.md (`init`, `index`, `sessions`, `session`, `stats`, `tool-usage`, `projects`, `project`, `project attach`, `cost-comparison`, `history`, `doctor`, `reset`, `vacuum`); each command runs without error against the test fixtures. Output discipline (data → stdout, progress → stderr) is verified by the E2E test.
- **`cost-comparison` formatter matches the eval schema.** Given a session with a parent and a subagent, the formatter emits a Markdown section that matches the format in `skills/transcript-parser/SKILL.md` (`## Candidate`, agents-spawned line, tool-use-turns-per-agent block, total, context estimate, wall time). `--format json` returns a dict that round-trips through `json.dumps` without modification. `--baseline <tool> <id>` produces a side-by-side `## Baseline` and `## Candidate` block.
- **Cross-tool queries work.** `conv-index tool-usage` aggregates across both opencode and cursor fixtures, with `tool_name_canonical` values rather than raw names.
- **Stats grouping works.** `conv-index stats --group-by day` returns a row per UTC day with active sessions, total turns, and total wall time. `--group-by tool|agent_type|day|week|project|model` is supported; default is `tool`.
- **Project attach works.** After `conv-index project attach <tool> <id> <label>`, `conv-index project <label>` shows the attached session, and `conv-index sessions --project <label>` returns it in the list.
- **`--since` filter works.** `conv-index index --since 2026-01-01` only re-indexes sessions whose `started_at` is on or after the cutoff. `conv-index sessions --since 2026-01-01` filters the list view the same way. Both accept ISO 8601 `YYYY-MM-DD` only.
- **History and doctor report the right thing.** After a run, `conv-index history` lists recent `index_runs` rows. `conv-index doctor` reports the schema version, WAL=on, FK=on, file mode 0600, parent dir mode 0700, and lock status (locked/unlocked only). Output supports `--format json`. Read commands detect uninitialized DB and print a clear error message.
- **Reset and vacuum are safe.** `conv-index reset --yes` deletes the DB and re-initializes; without `--yes`, the command refuses (and also refuses in non-TTY environments if `--yes` is missing). `conv-index vacuum` reduces the DB file size after a large reindex that deletes rows.
- **`--tool` flag is validated against known tools. Unknown values produce exit code 1 and an error message.**
- **JSON output is stable.** `conv-index cost-comparison opencode <id> --format json` returns a dict that round-trips through `json.dumps` without modification. The same is true for `conv-index sessions --format json` and `conv-index stats --format json`.
- **Documentation is complete.** `conv_index/README.md` covers install, quickstart, all commands, common flags (`--format`, `--quiet`, `--limit`), the cost-comparison output format, and the test strategy.
- **End-to-end test passes.** Indexing both fixtures, running every command, and asserting on output succeeds. The E2E harness uses `subprocess.run([sys.executable, '-m', 'conv_index.cli', ...])` (not `CliRunner`).
- **No credentials leak.** Test fixtures and the formatter output contain no real keys, tokens, or message bodies. The `test_privacy.py` test enforces this.

## Out of Scope

- Cost/pricing model and `cost_usd`. (The data shape supports it; the calculator is v2.)
- `pip install` release. (v1 ships as a checkout.)
- `transcript-parser` skill rewrite to query the indexer. (Post-program follow-on.)
- Web UI, MCP/server interface.
- Live session handling.

## Provenance Notes

This is the user-facing slice. Every command and every output format is what a real user sees. The cost-comparison formatter is the most important artifact here: it is the bridge from the indexer to the existing eval system, and a precondition for any future work that wants to consume indexed session data.

Snapshot tests for the cost-comparison formatter are the right defense against silent format drift. If the eval schema changes, the snapshots flag it explicitly rather than letting an LLM-rendered output drift unnoticed.
