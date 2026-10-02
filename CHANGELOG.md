# Changelog

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
