---
title: Codex and OpenCode parsers for tools/transcript
status: proposed
date: 2026-10-05
signal: tools/transcript only reads Claude Code and Cursor, but most local build seats now run on Codex and OpenCode.
owners: Workflow Optimiser, Cody
---

# Codex and OpenCode parsers for tools/transcript

## Signal

The weekly lab review on 2026-10-05 ran `tools/transcript/find.py --all --since 2026-09-28` on codyh-ubuntu. It returned 811 sessions: 460 claude-code, 348 cursor-cloud, and 3 cursor. It returned no Codex or OpenCode sessions, because `tools/transcript/parsers/` only has `claude.py`, `cursor.py`, and `cursor_cloud.py`.

Over the same seven days, `~/.codex/sessions` gained 557 rollout files, and `~/.local/share/opencode` had more than 11,000 modified files. Local Codex and OpenCode are the preferred build seats, so the session tooling (find, stats, cost, search, extract, classify) cannot see most of the build work it is meant to measure.

The interception trials already worked around this by hand: Codex sessions entered the corpus only as `lite_prefix` snapshots with no full-session length fields, and OpenCode as "checkpoint index only". That is why those strata were thin.

## Proposal

1. Add `parsers/codex.py`. Read `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` (honour `CODEX_HOME`). Map `session_meta` to session fields, `turn_context` to turn boundaries, and `response_item` function calls and outputs (paired by `call_id`) plus assistant messages into the normalized session JSON. Use `event_msg` only for what `response_item` lacks, such as token counts. Read defensively: the format is not a stable interface (see the Codex hooks docs), so unknown types are skipped and counted, not fatal. Dedupe rollouts that share a session id.
2. Add `parsers/opencode.py` against the OpenCode storage layout already inventoried in `RESEARCH/2026-10-02-local-session-inventory/`.
3. Register both in `find.py` and `--tool` filters as `codex` and `opencode`.
4. Tests: one small redacted fixture per harness under `tools/transcript/tests/`, covering a tool call pair, an orphan output, and an unknown line type.

## Success criteria

- `find.py --all --since <7 days ago>` lists Codex and OpenCode sessions, and the per-harness counts are within 5% of the file counts on disk after dedupe.
- `stats.py --session <codex rollout>` reports turns, tool histogram, and token totals that match a hand count on one fixture.
- Existing Claude and Cursor tests still pass.

## Scope and risk

Read-only analysis tooling. No hook, skill, or service behaviour changes. Non-breaking, so it can land on master by local merge once built. Build on a local Codex or OpenCode seat through Coding Harness Manager, not a cloud agent.

## Decision needed

Approve building this, or leave it parked in the backlog.
