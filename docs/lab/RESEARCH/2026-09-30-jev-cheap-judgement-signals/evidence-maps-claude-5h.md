# Evidence — open-pajero-maps Claude 5h analysis (2026-09-30)

**Artifacts (user upload / workspace copy):**

- `maps-claude-5h-analysis.md` (summary)
- `maps-claude-5h-analysis.json` (structured)

**Ideal band (workflow-plugin):** **50–75** API turns / **100–125k** final context (crossover; quality argues smaller). Source note in JSON: `docs/analysis/2026-09-08-workflow-vs-field.md`.

## Headline numbers

| Metric | Value |
|--------|--------|
| Subagents analyzed | **150** |
| Over ideal (flagged) | **24** (**16%**) |
| Over ctx > 125k | 17 |
| Over turns > 100 | 8 |
| Worst peak/final contexts | ~160k, 156k, 154k, 145k, 143k |

**Verdict:** YES — mis-sized subagents exist; they are **not** the majority but drive disproportionate burn.

## Heaviest rolling 5h windows (tokens ≈ input + cache_creation + cache_read + output)

| Rank | Tokens | Calls | Window (AEST) |
|------|--------|-------|----------------|
| 1 | **63.35M** | 764 | 2026-09-25 10:54 → 15:54 |
| 2 | **62.87M** | 652 | 2026-09-14 18:29 → 23:29 |
| 3 | **56.95M** | 667 | 2026-09-25 09:29 → 14:29 |
| 4 | **52.66M** | 532 | 2026-09-22 20:06 → 2026-09-23 01:06 |
| 5 | **50.27M** | 586 | 2026-09-25 06:53 → 11:53 |

Densest single window: **~63M tokens** in five hours — driven by **few large contributors**, not uniform session bloat.

## Active session pattern (d006f5a0…)

- Wall ~**43.8h**; parent modest; **subagents 8 · 778 API calls · 66.25M sub tokens** (of 71.53M total).
- **Over-ideal subagents: 4/8 (50%)** in this session.
- **Smoking gun worker:** `92a48e004519` — **296 API calls** (≫75), **12.7MB** JSONL, peak ctx **130k**, flags `OVER_TURNS`, `FAT_JSONL`.
- Pattern probes on that worker: **6 paths re-read ≥3×**, **~60 compact-ish events**, sleep/poll bash ≈3.

Interpretation for proposal **Signal** section: one **296-call** worker dominates an active multi-day session; PostToolBatch + turn gate would have fired long before post-hoc analysis.

## Other sessions (skim)

- **af9b5cb1…:** 19 subagents, **107.77M** tokens; only **2/19** over ideal — yet top 5h windows still cluster here when workers overlap.
- **bd4f6c0d…:** **54** subagents, **194.80M** tokens, **7/54** over ideal — long wall clock (54h) with many small workers + few fat ones (`bb6165018de0` **154** API calls).

## Method caveats (from analysis)

- Token totals from transcript `message.usage` (deduped by message id); may differ slightly from Anthropic meter.
- OVER_CTX often **125–147k** = compaction ceiling neighborhood; peak is the sizing signal.
- Turn counts = deduped assistant API calls, not user turns.
- Parallel overlapping fat workers > per-agent thrashing as 5h driver.

## Mapping to use cases

| Evidence | Use case |
|----------|----------|
| 296-call / 12MB worker | **1** PostToolBatch deterministic gate + Jev progress signal |
| 4/8 over ideal in one parent session | **1** signal to parent orchestrator |
| Phase refine agents (e.g. 6c87c96bd9bb “Refine Phase 3C”, 70 turns) | **2** complexity rating |
| Unit workers with thin vs fat verification | **3** needs-review confidence |
| Phase assert already on closure | **4** sanity layer only after deterministic pass |

## Suggested levers (analysis author — for proposal “Next spikes”, not automatic policy)

1. Hard-cap worker lifetime near **~75 turns / ~100k ctx** (handoff not resume).
2. Fresh handoff after compaction on fat agents (cache-read tax in 5h window).
3. Serialize heavy workers across 5h boundaries when multiple ≥1M-token agents overlap.

These align with **soft signals first**; hard caps remain a separate Cody decision.
