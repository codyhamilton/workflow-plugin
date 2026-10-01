# Research pack — cheap analysis, TypeSafe, OpenCode

**Date:** 2026-10-01  
**Slug:** `cheap-analysis-typesafe-opencode`  
**Status:** researching. **Confidence: not high.** The harness is specified and not run.  
**Question:** How should Flash, a local llama.cpp server, and TypeSafe split the work of reading Maps-length transcripts, so that framing trials are cheap, cached, and scored against a gold set that is not the failed checkout panel?  
**Success metric (for a later lock, not met here):** On a pre-registered prose field whose own α is at least 0.40, with at least three workers of real prose and at least two framings, one framing's precision beats the other on the same segments, at a recorded token cost, with a duplicate POST rate of 0. A failed rubric version cannot be re-labeled into a pass. Until that gold exists, the honest metrics are cost, throughput, mechanical `reread_cluster_accuracy`, and `gold_missing`.  
**Bounding plan:** [`docs/plans/07-cheap-analysis-harness/DESIGN.md`](../../../plans/07-cheap-analysis-harness/DESIGN.md).  
**Behaviour:** not shipped. No live `--call-jev`, no hook edit, no change to progressive TERMS.

This pack designs the harness. It does not replace the progressive session-gate study or the resolved cheap-Jev paper.

## Map

| File | Role |
|------|------|
| [`RESEARCH.md`](RESEARCH.md) | Inventory: plugin, Jev client, replay, gold seats, what the committed fixtures can and cannot show |
| [`DESIGN.md`](DESIGN.md) | System design and resolved recommendations |
| [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) | Ordered spikes, still no behaviour ship |
| [`TOOLS.md`](TOOLS.md) | Tool surfaces as markdown schemas. Not wired |

## How this sits on earlier packs

| Earlier record | This pack |
|----------------|-----------|
| [Progressive TERMS](../2026-10-01-progressive-jev-session-gates/TERMS.md) | Read-only. `api_turn`, `prefix(c)`, P0 `(75, 15)`, `hybrid_v0`, `A0`, `R(t)`, `confidence_min` stay theirs |
| [Progressive gold](../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/README.md) | Checkout panel. Flash drafts stay excluded. This study does not score against `A0` |
| [Cheap Jev signals](../2026-09-30-jev-cheap-judgement-signals/INDEX.md) | `jev-1.13.0`, 12_000 character state guard, classify is not a KPI, `assert_phase --deterministic` is the kill line |
| [OpenCode hooks](../2026-09-30-opencode-hooks-plugin/INDEX.md) | Signals plugin stays hooks-only. Custom tools are a sibling `tool` init hook, unwired |
| [Analytics sink](../2026-09-30-durable-analytics-sink/INDEX.md) | No `TYPESAFE_API_KEY` in any envelope. This pack adds no sink event |
| [Flash review gate](../../GUIDANCE-flash-review-gate.md) | Unchanged rule. Summaries and steer drafts from Flash wait on Sonnet 5.5, then Claude or Grok |

## Links

- Plan: [`../../../plans/07-cheap-analysis-harness/DESIGN.md`](../../../plans/07-cheap-analysis-harness/DESIGN.md)
- Open field (competing approaches, not a replacement for this harness): [`../2026-10-01-session-analysis-open-field/INDEX.md`](../2026-10-01-session-analysis-open-field/INDEX.md)
- Parent index: [`../INDEX.md`](../INDEX.md)
- Maps evidence: [`../2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md`](../2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md)
- Corpus manifest: [`../2026-10-01-progressive-jev-session-gates/proofs/corpus/MANIFEST.md`](../2026-10-01-progressive-jev-session-gates/proofs/corpus/MANIFEST.md)
