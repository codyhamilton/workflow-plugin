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

This pack completes the definitions, the citations, and the proof plan. A dry-run harness now replays the redacted fixtures (`proofs/run_proofs.sh`). The P0 agreement numbers in (2) exist and **fail H5** (α = 0.1189). Jev calls in (1) are still absent. Literature in [`LITERATURE.md`](LITERATURE.md) is input to (3), not a substitute for (2). The coordinator should treat every default below as unvalidated. **Confidence remains not high.**

| Bar | State on 2026-10-01 |
|-----|---------------------|
| Terms locked enough to implement a replay | Yes, in [`TERMS.md`](TERMS.md) |
| Hypotheses falsifiable before looking at outcomes | Yes, in [`HYPOTHESIS.md`](HYPOTHESIS.md) |
| Gold protocol and rubric written | Yes, [`TUNING-PLAN.md`](TUNING-PLAN.md), [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) |
| Public studies cited with what transfers | Yes, [`LITERATURE.md`](LITERATURE.md) |
| JSONL corpus in hand | Ubuntu raw + redacted fixtures; manifest under [`proofs/validated/corpus_manifest.json`](proofs/validated/corpus_manifest.json) |
| Gold labels | P0 panel on 21 cps (two smoking guns); **A0 null**; α **0.1189**; **H5 failed**. **(b)** `parent-pull-v1` Sonnet re-label **failed** (discarded). Next **(c)** corpus + original-rubric panel — [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) |
| Jev replay metrics | No live Jev cache / sweep yet |
| Design high-confidence | **No** |

## Map

| File | Role |
|------|------|
| [`TERMS.md`](TERMS.md) | Definitions: turn, schedule, continue vs checkout, fail-open, snapshot modes, v0 questions, gold, metrics; §11 shape-signal; §12–§13 WSM progressive decay + validation handoff (design only); §14 `shape-qual-full-maps-v1` (full T≥75 + early ≤~120T); §15 signal closeness (2026-10-02) |
| [`HYPOTHESIS.md`](HYPOTHESIS.md) | What would falsify the progressive gate, the hybrid snapshot, and the v0 questions |
| [`TUNING-PLAN.md`](TUNING-PLAN.md) | Corpus, multi-model gold, aggregation, param grid, staged calls, lock rule |
| [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) | What “pull the exit hatch” means, with maps examples. Draft delta at the end is not in force |
| [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) | **(b)** fail; **(c)–(f)** recorded; **`shape-signal-panel-v1`** seats done; **`shape-qual-full-maps-v1`** packs done, seats not launched; decay/handoff harness not started; **`signal-closeness-v0`** is the 2026-10-02 measurement grammar (unsigned, no seats) |
| [`LITERATURE.md`](LITERATURE.md) | Prior art and the limit of each citation |
| [`proofs/README.md`](proofs/README.md) | Offline harness plan and the files that must exist before any recommendation |
| [`DESIGN-progressive-decay-bar-v0.md`](DESIGN-progressive-decay-bar-v0.md) | Written D0 discount schedule and validation-handoff sketch. Harness not started. §8 points at the 2026-10-02 float-input grammar |
| [`ADVERSARIAL-progressive-decay-bar-v0.md`](ADVERSARIAL-progressive-decay-bar-v0.md) | WSM adversarial pack (design-grounded); D0 comparison, proposed D1 — not shipped |
| [`DESIGN-signal-closeness-v0.md`](DESIGN-signal-closeness-v0.md) | 2026-10-02 measurement grammar: float closeness, independent multi-ask, per-signal prove/kill, then state subsets, then WSM union + D0 discount. Unsigned drafts only. No behaviour ship |

## How this sits on the resolved paper

| Resolved use case 1 | This pack |
|----------------------|-----------|
| One `band_exit` log at API turn 76, no Jev | Unchanged. Replay may *compare* to it. It does not retune it |
| One optional `session-progress` call when `jev_eligible` | Baseline question set `Y_legacy` in the sweep |
| State guard 12_000 characters, pin `jev-1.13.0` | Same guard, same pin, new question id `session-checkout` |
| Hook exits 0, no block | Stays true. This pack never installs the hook |
| Soft until product wiring | Stays true. Progressive checkout is soft until Cody accepts behaviour |

Use cases 2–4 (refine complexity, unit needs-review, phase alignment) are out of this pack.

## Proof plan (Jev numbers still absent)

Stages, in order. Details and output schemas: [`proofs/README.md`](proofs/README.md).

1. **Manifest.** Count JSONLs with at least 75 assistant turns. Record sha256, turn count, bytes. Priority rows: `92a48e004519` (296), `bb6165018de0` (154). Negative control, not in the corpus: `6c87c96bd9bb` (70).
2. **Schema budget.** Build each snapshot mode at each labeled prefix and record state-JSON length. A mode that cannot shrink under 12_000 characters is ineligible.
3. **Gold.** Independent prefix judgements from Grok 4.7 high, Claude Sonnet, Claude Opus, and Composer when available. Agreement first. The P0 three-seat panel is below the floor (H5 failed, A0 null). Experiment **(b)** re-label failed; next is corpus expansion + original-rubric panel **(c)** in [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md), not a Jev sweep. `A_maj` and `A_gc` are computed in `proofs/validated/gold/p0-alt-gold-targets-20261001.json` and are not the fit rule.
4. **Jev cache.** Call Jev, or record a dry-run when the key is absent. A dry-run can check the schema. It cannot score hypotheses H1–H4 or H6–H7.
5. **Sweep.** Apply schedule, confidence, and fail-open policy to the cache. Emit overshoot, false early, false late, `max_allowed_turns`, stratified by length.
6. **Lock memo.** Only after (3) and (5). Until then the proposal stays `status: researching`.

Live Claude `PostToolBatch`, hook `additionalContext`, and any parent-surface format are outside every stage.

## Links

- Signal-closeness measurement grammar (2026-10-02, unsigned): [`DESIGN-signal-closeness-v0.md`](DESIGN-signal-closeness-v0.md). Interception contrast: [`../2026-10-02-interception-steer-to-stop/SIGNAL-CLOSENESS-CONTRAST.md`](../2026-10-02-interception-steer-to-stop/SIGNAL-CLOSENESS-CONTRAST.md)
- Sibling harness design (does not change these terms, `A0`, or this pack's proofs): [`../2026-10-01-cheap-analysis-typesafe-opencode/INDEX.md`](../2026-10-01-cheap-analysis-typesafe-opencode/INDEX.md)
- Stub: [`../../PROPOSALS/2026-10-01-progressive-jev-session-gates.md`](../../PROPOSALS/2026-10-01-progressive-jev-session-gates.md)
- Resolved predecessor: [`../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md)
- Predecessor pack: [`../2026-09-30-jev-cheap-judgement-signals/INDEX.md`](../2026-09-30-jev-cheap-judgement-signals/INDEX.md)
- Maps evidence: [`../2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md`](../2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md)
- Band caveat: [`../../../analysis/2026-09-08-workflow-vs-field.md`](../../../analysis/2026-09-08-workflow-vs-field.md)
- Parent index: [`../INDEX.md`](../INDEX.md)
