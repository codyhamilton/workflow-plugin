# Provisional Session Shortlist — Offline Jev Lever-Test Candidates

**Status:** provisional evidence inputs for comparing session-selection approaches (white paper / lab). Not a selection rule.
**Privacy:** paths, stats, and rationale only — no chat bodies reproduced.

## 1) Provisional shortlist (~18)

Length metric per harness: claude-code/cursor = `user_turns`; codex = `user_messages`; opencode = `messages` (norm ÷2). Sessions chosen for length **plus** harness/project spread and recoverable shape signals.

| # | Path | Harness | Length metric | Project | Why selected |
|---|------|---------|---------------|---------|--------------|
| 1 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/8f018224-5f7f-4713-a2bc-a2e9f853749d.jsonl` | claude-code | 284 turns / 773 msgs / 7.5 MB | open-pajero-maps | Longest transcript; ~22h span; best "Maps-style" multi-hour replay substrate |
| 2 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/6c5f98ce-1345-4287-914c-a8d0a590128a.jsonl` | claude-code | 254 / 567 / 4.2 MB | open-pajero-maps | Second-longest; ~24h span; distinct problem thread from #1 |
| 3 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/a59a5415-458e-41ab-b2d7-499377c18811.jsonl` | claude-code | 191 / 478 / 2.8 MB | open-pajero-maps | Early-Sept long run; 3rd length tier |
| 4 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/f06c7365-e8be-4dbf-b6c3-730a03ecdc0d.jsonl` | claude-code | 165 / 402 / 2.7 MB | open-pajero-maps | Multi-day span (9/13–9/16); good replay window |
| 5 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/af9b5cb1-edc5-4155-b521-a56bad1c7f13.jsonl` | claude-code | 162 / 379 / 2.8 MB | open-pajero-maps | Recent (9/24–9/25); comparable length to #4, later baseline |
| 6 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/670245db-d72a-4875-86cf-4f4b98803720.jsonl` | claude-code | 135 / 341 / 2.4 MB | open-pajero-maps | Long span (9/7–9/13); sustained arc |
| 7 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/9459fd4a-5d39-4c5e-b2e2-9659bf4fc9f4.jsonl` | claude-code | 130 / 321 / 2.5 MB | open-pajero-maps | Single-session burst (~6h) — shape contrast to multi-day runs |
| 8 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/d006f5a0-267f-402e-bed7-b13d1a65a961.jsonl` | claude-code | 99 / 246 / 2.0 MB | open-pajero-maps | Most recent long run (through 10/01); recency lens |
| 9 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps--claude-worktrees-brief-34-ceiling-only/107c3d34-cc31-4b60-8994-aa9e5be26e92.jsonl` | claude-code | 98 / 231 / 1.6 MB | open-pajero-maps (worktree ceiling-only) | Worktree-scoped brief; distinct execution shape (ceiling-only constraint) |
| 10 | `~/.claude/projects/-home-codyh-workspace-open-pajero-maps/bd4f6c0d-5061-4e77-9a4c-2e083814b952.jsonl` | claude-code | 79 / 167 / 2.2 MB | open-pajero-maps | High bytes-per-turn (dense payloads) — length-vs-density probe |
| 11 | `sqlite:…/opencode.db#session/ses_1a0369734ffeqlVOz4S81bAuz0` | opencode | 257 msgs (norm 128.5) | lemmings | Longest opencode session; title "Plan Execution workflow" — plan/execute shape signal |
| 12 | `sqlite:…/opencode.db#session/ses_1a0328cd5ffe6iabFeMKOf28Ad` | opencode | 169 msgs (84.5) | lemmings | Subagent-driven refactor; high output tokens; delegation shape |
| 13 | `sqlite:…/opencode.db#session/ses_1a6280e0dffeW0FRROYzKNpNV8` | opencode | 109 msgs (54.5) | llama.cpp | Non-harness-repo project; debugging topic ("high RAM when idle") |
| 14 | `sqlite:…/opencode.db#session/ses_42080a163ffer9OHMlFrbh7mID` | opencode | 85 msgs (42.5) | free-frontier | Oldest session in corpus (2026-01) — recency/era contrast |
| 15 | `~/.codex/sessions/2026/04/07/rollout-2026-04-07T04-10-34-019d6622-9229-7f50-85dc-dfcf9b64e188.jsonl` | codex | 59 user_msgs / 294 msgs / 1.7 MB | garcia-music | Longest codex session by user messages; high msg/turn ratio (tool-heavy) |
| 16 | `~/.codex/sessions/2026/04/16/rollout-2026-04-16T15-02-55-019d96d1-0a25-73c1-b327-66727ffc00dc.jsonl` | codex | 20 user_msgs / 169 msgs / 1.74 MB | lemmings | Second-highest codex bytes; very high msgs-per-user-msg — shape contrast to #15 |
| 17 | `~/.cursor/projects/home-codyh-workspace-garcia-music/agent-transcripts/b784e674-febe-4eb4-a2ca-ea2b1c5f7f26/b784e674-febe-4eb4-a2ca-ea2b1c5f7f26.jsonl` | cursor | 61 turns / 143 msgs / 123 KB | garcia-music | Longest cursor session by user turns; small bytes → short turns |
| 18 | `~/.cursor/projects/home-codyh-workspace-garcia-music/agent-transcripts/87e55915-f481-4dcc-8b6a-54c69392fcf9/87e55915-f481-4dcc-8b6a-54c69392fcf9.jsonl` | cursor | 49 turns / 247 msgs / 451 KB | garcia-music | Largest cursor transcript by bytes; dense vs #17 |

**Coverage:** claude-code 10, opencode 4, codex 2, cursor 2. All four length-ranked harnesses represented; no harness >~55%.

## 2) Gaps

**Harnesses with thin/no transcripts (excluded from shortlist):**
- **copilot** — `session-store.db` + `session-state`, 39 session files, discoverable but flagged "not primary coding harness for Jev." No rich transcript extraction attempted.
- **continue** — logs only; no session bodies.
- **aider** — caches/analytics only; no conversation dumps.
- **grokbot** — present but not inventoried (chat bodies deliberately skipped).
- **cursor-chat** — only 6 sessions, `bytes`-only metric, **null dates**, single project label (`cursor-chat`). Cannot rank by turns or recency; one 1.9 MB outlier otherwise tiny.

**Projects under-represented in long-session pool:**
- `workflow-plugin` (96 claude-code + 94 opencode sessions) appears in the top ranks only via small opencode sessions — no long claude-code candidate.
- `silver-chronicle`, `stelclone`, `free-frontier`, `instant-host`, `devcontainers`, `ansible-dev-config`, `sebissigma`, `empty-window` each have few sessions and none in the length top ranks.
- `open-pajero-maps` supplies 9 of the top-15 length ranks (30 of 160 claude-code sessions) — heavy concentration.

**Length-only bias risks:**
- **Verbosity ≠ depth:** high `messages`/`bytes` can come from repeated tool loops or thrash, not substantive lever-test material.
- **Cross-harness normalization is crude:** opencode `messages ÷ 2` is a heuristic, not equivalent to `user_turns`; opencode bytes are entirely missing, so it is structurally disadvantaged on size dimensions.
- **Cursor timestamps degenerate:** several rows have `first_ts == last_ts`, so duration/wall-clock lenses are unreliable there.
- **Codex splits:** high `messages` with low `user_messages` inflates apparent length relative to user-driven turns.
- **Duration vs turns:** #7 (6h, 130 turns) and #6 (5 days, 135 turns) are near-equal length but very different replay shapes.

**Alternative selection lenses to compare later:**
- **Shape** — tool-call ratio, plan/design markers, subagent usage, single-burst vs multi-day arc.
- **Thrash** — error/retry/edit-churn density as a signal of hard sessions.
- **Diversity** — stratification by project and harness before length ranking.
- **Recency** — last 30 days (favors #8, #5, and 10/01 runs) vs the March–May codex/opencode era.
- **Harness-balance** — quota-per-harness sampling so claude-code cannot sweep the list.

## 3) Deterministic ranking vs qualitative judgment

**Agree:**
- Top claude-code Maps sessions (#1–#7) are genuinely long *and* multi-hour/multi-day (first→last timestamps span hours to days), so length and "real sustained arc" concur.
- #11 (opencode "Plan Execution workflow") is legitimately the longest opencode session and carries an on-theme title.

**Diverge:**
- Deterministic order is ~60% single-harness/single-project; a diversity/harness-balance lens would promote codex lemmings/garcia-music, opencode lemmings, and cursor garcia-music far above their raw length rank.
- **Density vs turn count conflicts:** #10 (79 turns but 2.2 MB) and #16/#17 outrank or rival longer-turn but byte-light sessions depending on lens.
- **Data-quality divergence:** codex ranks 17 and 18 share `session_id 019d6386-62a1-7eb3-99d6-e4ca1499bd37` (two rollout files, same logical session); rank 19's filename timestamp and its `session_id` field disagree. Length ranking treats these as separate sessions — dedup is required before any committed rule.
- **Metric asymmetry:** opencode's null bytes and ÷2 normalization and codex's `user_messages` vs other harnesses' `user_turns` mean the "same" rank position is not the same quantity across harnesses.

Framing: provisional candidates for approach comparison — not a committed selection rule.
