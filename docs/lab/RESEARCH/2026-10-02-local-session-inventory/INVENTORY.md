# Local session transcript inventory (2026-10-02)

**Host:** codyh-ubuntu (`090ebdb6-1309-4527-9c34-1135deb7968b`)  
**Generated:** 2026-10-02 00:28 AEST  
**Scope:** Docs/analytics only — Soft Standard HOLD; no TypeSafe / hooks unlock / Pilot live Jev.  
**Privacy:** Paths + length/shape stats + brief metadata only. No full chat bodies.  

## Framing (evidence thread)

This folder is an **evidence thread for comparing session-selection approaches**
(white paper / lab). It inventories where transcripts live and how long they are,
and offers **provisional** shortlist candidates. It does **not** commit a single
selection rule as "the" answer. Length-biased ranking here is one lens among
several (shape, thrash, diversity, recency, harness-balance) to be compared later.

## Roots found

### claude-code
- **Primary:** `/home/codyh/.claude/projects`
- Also: `/home/codyh/.claude/history.jsonl`
- Also: `/home/codyh/.claude/sessions`

### codex
- **Primary:** `/home/codyh/.codex/sessions`
- Also: `/home/codyh/.codex/history.jsonl`
- Also: `/home/codyh/.codex/session_index.jsonl`
- Also: `/home/codyh/.codex/thread_history_1.sqlite`

### opencode
- **Primary:** `/home/codyh/.local/share/opencode/opencode.db`
- Also: `/home/codyh/.local/share/opencode/storage`
- Also: `/home/codyh/.config/opencode`
- Also: `/home/codyh/workspace/workflow-plugin/.opencode`
- Legacy storage session JSON files: 13

### cursor
- **Primary:** `/home/codyh/.cursor/projects/*/agent-transcripts/`
- Also: `/home/codyh/.cursor/chats`

## Counts by harness

| Harness | Sessions | Length metric | Median | P90 | Max | Date range (UTC) |
|---------|----------|---------------|--------|-----|-----|------------------|
| claude-code | 160 | user_turns | 2.0 | 36 | 284 | 2026-09-01 → 2026-10-01 |
| codex | 278 | user_messages | 5.0 | 16 | 59 | 2026-03-29 → 2026-10-01 |
| opencode | 318 | messages | 6.0 | 22 | 257 | 2026-01-21 → 2026-10-01 |
| cursor | 393 | user_turns | 2 | 8 | 61 | 2026-02-28 → 2026-09-25 |
| cursor-chat | 6 | bytes | 10399.5 | 20644 | 1928358 | — → — |

**Overall (normalized length):** n=1149, median=3.0, p90=12.0, max=284.0, mean=6.71

Normalized metric: claude/cursor/codex ≈ user turns/messages; opencode ≈ messages/2. cursor-chat excluded from overall length (bytes-only).

## Projects (top per harness)

- **claude-code:** workflow-plugin (96), open-pajero-maps (30), tmp-expansion-panel (20), tmp-thrash-screen-panel-sonnet (12), open-pajero-maps (worktree ceiling-only) (2)
- **codex:** lemmings (129), silver-chronicle (53), garcia-music (52), workflow-plugin (33), sc-redesign-public (3), sc-redesign-global (2), sc-redesign-reader (2), sc-redesign-authoring (2)
- **opencode:** lemmings (151), workflow-plugin (94), garcia-music (32), open-pajero-maps (16), free-frontier (13), llama.cpp (4), codyh (2), stelclone (2)
- **cursor:** garcia-music (318), stelclone (29), garcia-music (workspaces) (18), workflow-plugin (9), empty-window (8), lemmings (5), instant-host (3), silver-chronicle (1)
- **cursor-chat:** cursor-chat (6)

## Gaps / thin harnesses

- **copilot**: discoverable=True; session-store.db + session-state present; not primary coding harness for Jev
- **continue**: discoverable=True; logs only; no rich session transcripts found
- **aider**: discoverable=True; caches/analytics only; no conversation dumps
- **grokbot**: discoverable=True; present but not inventorying agent chat bodies here
- **cursor-chat**: 6 stores only; bytes metric; null dates — weak for lever-test selection.
- **OpenCode bytes**: not populated from DB (messages/parts counts used instead).
- **Claude subagent jsonl**: inventoried main session `*.jsonl` only (subagents omitted from session count).

## Method notes

1. Discover roots via `find`/`ls` across `~/.claude`, `~/.codex`, `~/.local/share/opencode`, `~/.cursor`, workspace dumps.
2. Deterministic Python inventory → `stats.json` / `stats-compact.json`.
3. OpenCode DeepSeek Flash qualitative shortlist (see `SHORTLIST.md`, `flash-run.json`).
4. Soft Standard HOLD throughout.

## Related lab threads

- `docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/`
- `docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/`

