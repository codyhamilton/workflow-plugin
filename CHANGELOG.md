# Changelog

## 2.9.1 — 2026-10-05

- Codex hooks ship with the plugin. `.codex-plugin/plugin.json` selects `hooks/codex.json` (`spool.sh --harness codex`,
  `$PLUGIN_ROOT` paths) and declares the skills and `.mcp.json`. Before this, Codex fell back to `hooks/hooks.json`, so
  every Codex event was recorded twice when `~/.codex/hooks.json` was also set up, once mislabelled `claude`.
  `tools/hooklog/codex-hooks.example.json` is removed; delete its entries from `~/.codex/hooks.json` and re-trust the
  plugin hooks in `/hooks`.

## 2.9.0 — 2026-10-04

- Hooklog capture is now a bash spooler plus an async drain. Hooks run `tools/hooklog/spool.sh`, which writes the raw payload
  to a local spool directory and returns (no python or network on the hot path; Cursor permissive replies preserved).
  `tools/hooklog/drain.py` normalises and scrubs, posts batches to the quality service with the bearer token, archives to the
  per-session JSONL, and retries after downtime (idempotent; rows keep their original `ts`). `install-drain.sh` adds a
  systemd timer; session end also kicks a drain.
- All shipped registrations (Claude, Cursor, Codex examples) call `spool.sh`; Claude registrations now pass `--event`.
  `hooklog.py record` stays as a spooling shim for older installs; `post_to_service` is removed.
- OpenCode hooks package writes spool files directly (`WORKFLOW_HOOKLOG_CLI` removed; `WORKFLOW_HOOKLOG_SPOOL` added).

## 2.8.0 — 2026-10-03

- Add the quality service (`tools/quality`): a local HTTP MCP + REST server with a SQLite ledger, registered in
  `.mcp.json` on `127.0.0.1:8765` and installable as a systemd user unit (`install-service.sh`).
  Design, refine and execute post to it (`post_design`, `post_brief`, `start_execution`, `complete_execution`);
  design and refine write the returned id to frontmatter, and execute puts `[exec <id>]` in commit titles.
- Hooklog posts every row to the service (`WORKFLOW_QUALITY_URL`) and spools to the JSONL store when it is down;
  conversations bind to plans and executions from the hook stream.
- Store design and brief text (`bodies.db`, FTS5, scrubbed) with search and rescore; Jev checks are service-defined
  data (`define_checks`), including the acceptance-criterion provenance checks.
- Jev variants: per-session checkpoints and `hide_next_prompt` for labelled rounds. Lab method and mining notes
  under `docs/lab/`.
- Merged onto 2.7.0 (hooklog catalog coverage); the service posting is layered on its `normalize`/`record`.

## 2.7.0 — 2026-10-03

- Expand Claude hooklog to 33 catalog keys: 31 active commands and 2 integration-only worktree
  slots. WorktreeCreate/WorktreeRemove replace host operations, so leave their standalone
  registrations empty to preserve observe-only behavior; document existing-handler integration.
- Select native Cursor hooks through the plugin manifest and expand the standalone example
  to every named agent/Tab/workspace event. The catalog requires 22 but enumerates 21 (18 agent,
  2 Tab, 1 app); capture all named events and document that discrepancy and cloud gaps.
- Capture OpenCode's 18 Hooks callbacks and 28 catalog bus types (plus future bus types), with
  native event names and nested session routing. Leave all mutable hook outputs unchanged.
- Add command registration for all 12 Codex hooks in user/project hooks.json. Codex is not N/A;
  hosted tools such as WebSearch skip PreToolUse/PostToolUse.
- Preserve lifecycle and unknown named events as bounded, redacted observations in the same
  JSONL store. Add pre-tool observations and retain existing turn markers without counting
  SessionEnd or duplicate Cursor shell/MCP/edit events twice.
- Return schema-valid permissive Cursor pre-action responses even on capture failure or disable.
  Tighten credential/header redaction and add command, callback/bus and loader smoke coverage.
- Bump core Claude/Cursor manifests from 2.6.0 to 2.7.0; OpenCode's independently versioned
  package moves from 0.1.0 to 0.2.0.

## 2.6.0

- Introduce shared hooklog capture and hook-backed turn data for Claude Code, Cursor and OpenCode.
