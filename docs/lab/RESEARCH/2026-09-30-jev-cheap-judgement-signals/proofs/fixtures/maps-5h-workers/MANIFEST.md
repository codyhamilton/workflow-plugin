# MANIFEST — maps-5h-workers (redacted fixtures)

Commit-friendly, **redacted** Claude Code subagent JSONLs for Workflow System Manager progressive Jev lab (PR #35) and cheap-judgement proofs.

**Repo path:** `docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers/`

**Ideal band:** 50–75 API turns (unique `message.id` on `type=assistant` rows).

## How turns / peak ctx are counted

- `api_turns` = count of unique `message.id` values on rows with `type == "assistant"`.
- `peak_ctx` = max over assistant rows of `input_tokens + cache_read_input_tokens + cache_creation_input_tokens` from `message.usage`.
- Redaction preserves those fields and tool_use `name`/`id` markers; free text, thinking bodies, tool inputs/outputs, cwd, and attachment payloads are `[REDACTED]`.
- Regenerate from Ubuntu sources: `python3 redact_maps_worker.py --src <abs.jsonl> --dst <short_id>.jsonl --short-id <id>`.

## Corpus

| short_id | band | api_turns | peak_ctx | fixture | source (Ubuntu local only) |
|----------|------|----------:|---------:|---------|------------------------------|
| `92a48e004519` | smoking_gun_over75 | 296 | 129961 | `92a48e004519.jsonl` | `/home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/d006f5a0-267f-402e-bed7-b13d1a65a961/subagents/agent-a23c692a48e004519.jsonl` |
| `bb6165018de0` | smoking_gun_over75 | 154 | 146781 | `bb6165018de0.jsonl` | `/home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/bd4f6c0d-5061-4e77-9a4c-2e083814b952/subagents/agent-ad325bb6165018de0.jsonl` |
| `6c87c96bd9bb` | control_inband_50_75 | 70 | 125993 | `6c87c96bd9bb.jsonl` | `/home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/af9b5cb1-edc5-4155-b521-a56bad1c7f13/subagents/agent-a95386c87c96bd9bb.jsonl` |
| `0aab88c525de` | over75 | 192 | 166836 | `0aab88c525de.jsonl` | `/home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/a59a5415-458e-41ab-b2d7-499377c18811/subagents/agent-a4a960aab88c525de.jsonl` |
| `036ff3ed4a89` | over75 | 161 | 156769 | `036ff3ed4a89.jsonl` | `/home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/670245db-d72a-4875-86cf-4f4b98803720/subagents/agent-a8024036ff3ed4a89.jsonl` |
| `3ff8479be14a` | inband_50_75 | 68 | 124156 | `3ff8479be14a.jsonl` | `/home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/a59a5415-458e-41ab-b2d7-499377c18811/subagents/agent-a9dfa3ff8479be14a.jsonl` |
| `6135cffdf32a` | inband_50_75 | 68 | 106679 | `6135cffdf32a.jsonl` | `/home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/bd4f6c0d-5061-4e77-9a4c-2e083814b952/subagents/agent-a1f166135cffdf32a.jsonl` |

## Roles

- **92a48e004519** — smoking gun (296 API turns) (source agent file `agent-a23c692a48e004519.jsonl`, parent session `d006f5a0-267f-402e-bed7-b13d1a65a961`). Raw size 12,674,034 B → redacted 743,285 B.
- **bb6165018de0** — smoking gun (154 API turns) (source agent file `agent-ad325bb6165018de0.jsonl`, parent session `bd4f6c0d-5061-4e77-9a4c-2e083814b952`). Raw size 3,602,690 B → redacted 314,194 B.
- **6c87c96bd9bb** — control / refine-phase in-band (source agent file `agent-a95386c87c96bd9bb.jsonl`, parent session `af9b5cb1-edc5-4155-b521-a56bad1c7f13`). Raw size 2,059,935 B → redacted 163,060 B.
- **0aab88c525de** — additional 75+ worker (source agent file `agent-a4a960aab88c525de.jsonl`, parent session `a59a5415-458e-41ab-b2d7-499377c18811`). Raw size 2,860,607 B → redacted 415,572 B.
- **036ff3ed4a89** — additional 75+ worker (source agent file `agent-a8024036ff3ed4a89.jsonl`, parent session `670245db-d72a-4875-86cf-4f4b98803720`). Raw size 1,151,433 B → redacted 321,250 B.
- **3ff8479be14a** — additional in-band (source agent file `agent-a9dfa3ff8479be14a.jsonl`, parent session `a59a5415-458e-41ab-b2d7-499377c18811`). Raw size 705,179 B → redacted 147,513 B.
- **6135cffdf32a** — additional in-band (source agent file `agent-a1f166135cffdf32a.jsonl`, parent session `bd4f6c0d-5061-4e77-9a4c-2e083814b952`). Raw size 918,895 B → redacted 158,579 B.

## WSM / PR #35 pointer

Point progressive Jev session-gates research at this directory (cloud-readable, no `/home/codyh` dependency):

```text
docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers/
```

Suggested default replay set:

- Smoking: `92a48e004519.jsonl`, `bb6165018de0.jsonl`
- Control (in-band): `6c87c96bd9bb.jsonl`
- Extra 75+: `0aab88c525de.jsonl`, `036ff3ed4a89.jsonl`
- Extra in-band: `3ff8479be14a.jsonl`, `6135cffdf32a.jsonl`

Cross-link from `docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/` (PR #35 branch) to this MANIFEST when wiring the offline corpus.

## Git / secrets

- These redacted JSONLs are **intended to be committed** (cloud agents cannot read `/home/codyh`).
- Do **not** commit raw Claude project transcripts from `~/.claude/projects/…`.
- No Ubuntu-only symlinks in this directory.

