# Claude Code hook events (soft escalation surface)

No in-repo hook implementations for these events yet; this note captures **public Claude Code hooks** knowledge and maps them to the cheap-Jev proposal. Confirm against current Anthropic docs when implementing.

## Events relevant to soft escalation

| Event | Typical payload / moment | Soft escalation role |
|-------|--------------------------|----------------------|
| **PostToolBatch** | After a batch of tool calls completes | Deterministic turn/size gate; optional Jev on progress, remaining work, or session size → **signal** for actor (not hard stop). Primary anchor for use case 1. |
| **PreCompact** | Before context compaction | Log + optional Jev: “is compaction likely to hide unresolved work?” — steer handoff vs resume-in-place. |
| **PostCompact** | After compaction | Compare pre/post context; flag fat sessions that should fresh-handoff (ties to 5h burn evidence). |
| **SubagentStart** | Child agent spawned | Correlate spawn with brief id; baseline for per-worker budgets. |
| **SubagentStop** | Child agent finished | Unit-complete hook surface (use case 3) when paired with workflow trailers. |
| **Stop** | Session or agent stop | Finalize metrics row; attach Jev summary if any in-flight signals. |
| **StopFailure** (e.g. `rate_limit`) | Abnormal stop | Escalation to bot/human without treating as quality pass. |
| **UserPromptSubmit** | User sends message | Optional nudge when deterministic gates already fired (avoid spam). |

## Design constraints (from lab policy)

- Hooks **emit signals** (log, JSONL, driver-visible row) by default — not merge gates.
- Any **enforcement** at phase boundaries stays on **`assert_phase --deterministic`** until Cody promotes a rule.
- Jev questions must use **compact state** (counts, headings, brief ids, last N tool summaries) — not full transcript snapshots (Jev context budgets; see [`../INDEX.md`](../INDEX.md) TypeSafe rows).

## In-repo mentions

- `docs/lab/README.md` — SessionStart / unattended skills (related bootstrap, not PostToolBatch).
- `docs/lab/ANALYSIS/2026-09-30-grokbot-driver-reorient.md` — hooks + cloud-safe skills; bot event log = driver stdout + assert JSONL + git.

## Open implementation questions (for white paper)

- Which events are available in **headless / cloud** vs local Claude Code only?
- How to pass **brief id / phase / unit** into hook state without reloading full skills?
- Where to write hook signal JSONL so Grok Bot and weekly FINDINGS can skim it (parallel to `.run-record.jsonl`)?
