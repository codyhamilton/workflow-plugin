# Research pack — progressive Jev session gates

**Date:** 2026-10-01  
**Slug:** `progressive-jev-session-gates`  
**Status:** researching. **Confidence: not high.**  
**Question:** On stored Claude transcripts of at least 75 assistant turns, does repeating one Jev checkout test every 15 turns from a first checkpoint near 75 stop the counterfactual run near a multi-model gold exit, with a bounded rate of early stops?  
**Success metric (for a later lock, not met here):** A parameter cell whose overshoot, false-early rate, and false-late rate beat the closed single-shot gate on a pre-registered gold rule, after the judge panel clears a reliability floor.  
**White paper stub:** [`../../PROPOSALS/2026-10-01-progressive-jev-session-gates.md`](../../PROPOSALS/2026-10-01-progressive-jev-session-gates.md).

This pack elaborates use case 1 of the resolved cheap-Jev paper. It does not replace that paper.

## Confidence bar

High confidence, in Cody’s sense for this design, means all three of the following are done:

1. The schedule, snapshot, question set, fail-open rule, and gold rule have been **run**, not only defined.
2. The run produced **hard numbers** on offline replay: corpus counts, inter-rater agreement, overshoot, false early, false late, `max_allowed_turns`.
3. Those numbers have been read **against public studies** where a study actually measures a related quantity, with the non-transfers written down.

This pack completes the definitions, the citations, and the proof plan. It does not complete (1) or (2). Literature in [`LITERATURE.md`](LITERATURE.md) is input to (3), not a substitute for (2). The coordinator should treat every default below as unvalidated.

| Bar | State on 2026-10-01 |
|-----|---------------------|
| Terms locked enough to implement a replay | Yes, in [`TERMS.md`](TERMS.md) |
| Hypotheses falsifiable before looking at outcomes | Yes, in [`HYPOTHESIS.md`](HYPOTHESIS.md) |
| Gold protocol and rubric written | Yes, [`TUNING-PLAN.md`](TUNING-PLAN.md), [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) |
| Public studies cited with what transfers | Yes, [`LITERATURE.md`](LITERATURE.md) |
| JSONL corpus in hand | No. Smoking-gun paths are not in this repo |
| Gold labels | No |
| Jev replay metrics | No |
| Design high-confidence | **No** |

## Map

| File | Role |
|------|------|
| [`TERMS.md`](TERMS.md) | Definitions: turn, schedule, continue vs checkout, fail-open, snapshot modes, v0 questions, gold, metrics |
| [`HYPOTHESIS.md`](HYPOTHESIS.md) | What would falsify the progressive gate, the hybrid snapshot, and the v0 questions |
| [`TUNING-PLAN.md`](TUNING-PLAN.md) | Corpus, multi-model gold, aggregation, param grid, staged calls, lock rule |
| [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) | What “pull the exit hatch” means, with maps examples |
| [`LITERATURE.md`](LITERATURE.md) | Prior art and the limit of each citation |
| [`proofs/README.md`](proofs/README.md) | Offline harness plan and the files that must exist before any recommendation |

## How this sits on the resolved paper

| Resolved use case 1 | This pack |
|----------------------|-----------|
| One `band_exit` log at API turn 76, no Jev | Unchanged. Replay may *compare* to it. It does not retune it |
| One optional `session-progress` call when `jev_eligible` | Baseline question set `Y_legacy` in the sweep |
| State guard 12_000 characters, pin `jev-1.13.0` | Same guard, same pin, new question id `session-checkout` |
| Hook exits 0, no block | Stays true. This pack never installs the hook |
| Soft until product wiring | Stays true. Progressive checkout is soft until Cody accepts behaviour |

Use cases 2–4 (refine complexity, unit needs-review, phase alignment) are out of this pack.

## Proof plan (numbers still absent)

Stages, in order. Details and output schemas: [`proofs/README.md`](proofs/README.md).

1. **Manifest.** Count JSONLs with at least 75 assistant turns. Record sha256, turn count, bytes. Priority rows: `92a48e004519` (296), `bb6165018de0` (154). Negative control, not in the corpus: `6c87c96bd9bb` (70).
2. **Schema budget.** Build each snapshot mode at each labeled prefix and record state-JSON length. A mode that cannot shrink under 12_000 characters is ineligible.
3. **Gold.** Independent prefix judgements from Grok 4.7 high, Claude Sonnet, Claude Opus, and Composer when available. Agreement first. If reliability is below the floor, stop and revise the rubric.
4. **Jev cache.** Call Jev, or record a dry-run when the key is absent. A dry-run can check the schema. It cannot score hypotheses H1–H4 or H6–H7.
5. **Sweep.** Apply schedule, confidence, and fail-open policy to the cache. Emit overshoot, false early, false late, `max_allowed_turns`, stratified by length.
6. **Lock memo.** Only after (3) and (5). Until then the proposal stays `status: researching`.

Live Claude `PostToolBatch`, hook `additionalContext`, and any parent-surface format are outside every stage.

## Links

- Stub: [`../../PROPOSALS/2026-10-01-progressive-jev-session-gates.md`](../../PROPOSALS/2026-10-01-progressive-jev-session-gates.md)
- Resolved predecessor: [`../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md)
- Predecessor pack: [`../2026-09-30-jev-cheap-judgement-signals/INDEX.md`](../2026-09-30-jev-cheap-judgement-signals/INDEX.md)
- Maps evidence: [`../2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md`](../2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md)
- Band caveat: [`../../../analysis/2026-09-08-workflow-vs-field.md`](../../../analysis/2026-09-08-workflow-vs-field.md)
- Parent index: [`../INDEX.md`](../INDEX.md)
