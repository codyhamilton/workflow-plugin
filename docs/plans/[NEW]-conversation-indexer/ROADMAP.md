# [NEW] Conversation Indexer — Roadmap

## Parent Program Overview

Three linked child plans to build a SQLite-backed indexer for conversation logs, replacing the instruction-based `transcript-parser` skill with a queryable system.

1. Schema + opencode/claude-code parser + indexer core
2. Cursor parser (validates abstraction beyond opencode format)
3. CLI queries + cost-comparison formatter + polish

The work is independent of the completed `01-workflow-improvements` program and is not sequenced after it. Both are dogfooding artifacts of the workflow-plugin.

## Status: In Progress

`04-cursor-toolkit` is the first child to ship — standalone scripts, no SQLite dependency, immediate agent use. Plans 01–03 follow once the fast-track toolkit validates the Cursor format.

## Child Plans

| Order | Plan | Purpose | Status | Dependencies |
|-------|------|---------|--------|--------------|
| 4 | 04-cursor-toolkit | Standalone Cursor toolkit scripts + iterate analysis + analysis doc | **shipped** | none |
| 1 | 01-schema-and-opencode | Schema v1, opencode/claude-code parser, indexer core, minimal CLI, test fixture | planned | none |
| 2 | 02-cursor | Cursor parser integrated into conv-index SQLite backend | planned | 01 (parser interface, schema) |
| 3 | 03-cli-and-formatters | Full query CLI, cost-comparison formatter, documentation, comprehensive tests | planned | 01 (library, schema) |

## Sequencing Rationale

**04 first (fast track)**: An immediate need — a 67-agent Cursor session was analysed manually at high cost. Standalone Python scripts deliver agent-callable Cursor analysis without a DB installation or the SQLite schema work. The Cursor format is now confirmed from a real session (parent JSONL + `subagents/` directory); this grounds the 02 implementation.

**01 second**: schema and the opencode parser are the foundation. Once these land, the cursor parser is a small adaptation rather than a fresh design, and the CLI is a thin wrapper over a stable library.

**02 third**: Cursor parser integrated into the SQLite backend. `02-cursor/PLAN.md` was updated to reflect the real subagent format (subagents ARE stored separately in `{session-dir}/subagents/{agent-id}.jsonl`; the original plan incorrectly stated there were none).

**03 last**: the full CLI surface and the cost-comparison formatter are the user-facing pieces. Building them last means they consume a tested, validated library rather than driving the design.

## Parallelizable Work

- Once 01 ships its library types and parser interface, the cursor parser (02) can be developed in parallel with the CLI work that will become 03. The shared dependency is the schema and the `parsers/base.py` contract, both of which are stable after 01 phase 2.
- The `tools/cursor/iterate_analysis.py` logic from 04 can be ported into a `conv-index iterate-analysis` subcommand during 03 without rework.

## Current Blockers

None. `04-cursor-toolkit` has no dependencies and can begin immediately.

## Dogfooding Notes

This program is itself planned using the workflow-plugin. Its `PROVENANCE.md` is an example of the progressive provenance model. When 01 lands, the existing sessions in `~/.claude/projects/-home-codyh-workspace-workflow-plugin/` become real fixtures for the parser — the test corpus grows organically as the workflow-plugin is used.

## Post-Program Follow-On (Not in Scope)

- Rewrite `transcript-parser` skill to query the indexer instead of re-parsing JSONL.
- v2: cost/pricing model, copilot and codex parsers, manifest-based incremental discovery.
- Possible repo split: extract `conv_index/` into a standalone project once it has multiple consumers.
