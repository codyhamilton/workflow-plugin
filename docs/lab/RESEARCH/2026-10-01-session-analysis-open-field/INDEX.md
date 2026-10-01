# Research pack — session analysis, open field

**Date:** 2026-10-01  
**Slug:** `session-analysis-open-field`  
**Status:** exploring. **Confidence: not high.** No approach here has been run. None is the plan of record.  
**Question:** Which combinations of abstract summaries, early-window markers, TypeSafe framings, and agent cadence can score Maps session shape from the first ~120 `api_turn`s, cheaply enough to search that space, without feeding raw transcripts into an expensive seat and without treating checkout `A0` as the target?  
**Success metric (for a later lock, not met here):** Two or more named approaches each publish a pre-registered result on the same `shape-qual-full-maps-v1` workers, with a recorded cost, and at least one kill criterion fires or a proof gate clears. A single narrative that all five "could work" is not success. Until a cycle runs, the honest output of this pack is the comparison itself.  
**Behaviour:** not shipped. No live `--call-jev`, no hook edit, no OpenCode tool registration, no change to progressive TERMS.

This pack sits beside the cheap-analysis harness. It does not replace that harness design, the shape-qual agreement, or the progressive session-gate study.

## Map

| File | Role |
|------|------|
| [`OPEN-FIELD.md`](OPEN-FIELD.md) | Problem space, constraints, and the option sets for summaries, markers, framings |
| [`CANDIDATE-APPROACHES.md`](CANDIDATE-APPROACHES.md) | Five named end-to-end approaches, proof gates, kill criteria, comparison |
| [`RESEARCH-OPS.md`](RESEARCH-OPS.md) | How Workflow System Manager runs the cycles, closes threads, and escalates |
| [`TOOLING-MVP.md`](TOOLING-MVP.md) | What to build first, and what waits |
| [`proofs/README.md`](proofs/README.md) | Phase 1b framing dry-run + 1c mount probe (0 live POSTs) |
| [`cycles/CYCLE-LOG.md`](cycles/CYCLE-LOG.md) | WSM cycle log |

## How this sits on earlier packs

| Earlier record | This pack |
|----------------|-----------|
| [Cheap-analysis DESIGN](../2026-10-01-cheap-analysis-typesafe-opencode/DESIGN.md) and [NEXT-EXPERIMENTS](../2026-10-01-cheap-analysis-typesafe-opencode/NEXT-EXPERIMENTS.md) | Read. Spikes 0–8 stay scheduled there. Role split, `early_window_end`, dry-run default, 32-call cap, and `shape-rubric-v0` are reused, not rewritten |
| [Cheap-analysis TOOLS.md](../2026-10-01-cheap-analysis-typesafe-opencode/TOOLS.md) | Unwired schemas. Tooling rank points at them; this pack does not register a plugin |
| [Progressive TERMS](../2026-10-01-progressive-jev-session-gates/TERMS.md) | Read-only. §11–§14 are the shape vocabulary. `A0`, `P0`, `confidence_min` stay theirs |
| [shape-qual agreement](../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/shape-qual-full-maps-v1/AGREEMENT-SUMMARY.md) | Theme target for scoring. n = 34. Exit-turn spread stays secondary |
| [shape-signal agreement](../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md) | 7-worker precursor. Full Maps is the corpus this pack cites |
| [Flash review gate](../../GUIDANCE-flash-review-gate.md) | Unchanged. Flash drafts wait on Sonnet 5.5, then Claude or Grok, as a study convention |

## Links

- Parent index: [`../INDEX.md`](../INDEX.md)
- Harness pack: [`../2026-10-01-cheap-analysis-typesafe-opencode/INDEX.md`](../2026-10-01-cheap-analysis-typesafe-opencode/INDEX.md)
- Combined packs: [`../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/packs/shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl`](../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/packs/shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl) (104 rows, 82 with `checkpoint_turn` ≤ 120)
