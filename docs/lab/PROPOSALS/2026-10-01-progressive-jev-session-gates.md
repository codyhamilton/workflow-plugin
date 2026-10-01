---
title: Progressive PostToolBatch Jev session gates
status: researching
confidence: not-high
date: 2026-10-01
updated: 2026-10-01
signal: Maps workers run far past the ideal band (92a48e004519 to 296 turns, bb6165018de0 to 154) after a single band_exit log at turn 76. Cody wants the same Jev checkout test repeated every 15 turns from about 75, tuned offline against multi-model gold exits.
owners: Workflow Optimiser, Cody
extends: docs/lab/PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md use case 1
---

# Progressive PostToolBatch Jev session gates

**Status: researching. Confidence: not high.**

Cody’s bar for calling this design high-confidence is three parts together: the assumptions have been tested, the tests are hard numbers from offline transcript replay, and the framing has been checked against public studies where those studies exist. This stub and the research pack lock the vocabulary, the question set to try, and the measurement protocol. They do not contain those numbers. No recommendation in this file is accepted behaviour.

The resolved cheap-Jev paper stays as written. This pack extends **use case 1 only** (in-session progress). It does not reopen refine, unit-complete, or phase-complete judgements, and it does not edit `gate_thresholds.py` or `jev_signal_schemas.py`.

Research pack: [`../RESEARCH/2026-10-01-progressive-jev-session-gates/`](../RESEARCH/2026-10-01-progressive-jev-session-gates/INDEX.md).

## Signal

The 2026-09-30 maps pass scored 150 subagents against the workflow band of 50–75 API turns and 100–125k peak context. 24 of 150 (16%) were over that band. Eight exceeded 100 turns. Worker `92a48e004519` reached **296** API calls, a **12.7MB** JSONL, and **130k** peak context, with six paths re-read at least three times and about sixty compact-ish events. Worker `bb6165018de0` reached **154** API calls. The closed gate would have logged `band_exit` at turn 76 and become `jev_eligible` once, near turn 85 or on context and bytes. Nothing in that design asks again at 90, 105, and onward. The field note that the band comes from already says the 50–75 figure is a cost crossover, not a published optimum ([`docs/analysis/2026-09-08-workflow-vs-field.md`](../../analysis/2026-09-08-workflow-vs-field.md)).

## Problem

A single advisory row at band exit tells an archaeologist that a worker left the band. It does not keep testing whether continuing is still justified as the transcript grows. A worker can pass one soft check, or never receive a Jev call, and still run to 296 turns. The cost of that pattern is concentrated: a few fat workers dominate rolling windows of about 63M tokens.

The question this research has to answer, with numbers, is whether a repeated checkout test on stored transcripts fires near the turns where independent judges say continuing had already become a mistake, and how often it fires earlier than that.

## What is locked as a research protocol

These are definitions for the offline study, not shipped hook behaviour. Precise statements are in [`TERMS.md`](../RESEARCH/2026-10-01-progressive-jev-session-gates/TERMS.md).

- Replay on stored Claude JSONL. The turn counter is the deduped assistant API turn (`type=assistant`, not `isSidechain`). No live `PostToolBatch` run is required or planned for this spike.
- Proposed schedule to beat in the sweep: first checkpoint at turn **75**, then every **15** turns (90, 105, …) for as long as the transcript continues.
- The same question set at every checkpoint. Proposed v0 id `session-checkout`, pin `jev-1.13.0`.
- A checkpoint that does not affirmatively checkout leaves the worker notionally running. The next look is one interval later. That is fail-open for the worker.
- Jev sees a capped snapshot, not the raw JSONL. Proposed default is hybrid: cumulative stats for the prefix, the brief anchor, and a short tail. State JSON stays inside the existing **12_000**-character guard.
- Gold exits come from several models judging the same prefixes independently, then an aggregation rule. Jev is tuned against that gold. Judges and Jev are different calls.

## Open design axes

None of these are resolved. The sweep and the pre-registered hypotheses are in [`HYPOTHESIS.md`](../RESEARCH/2026-10-01-progressive-jev-session-gates/HYPOTHESIS.md) and [`TUNING-PLAN.md`](../RESEARCH/2026-10-01-progressive-jev-session-gates/TUNING-PLAN.md).

| Axis | Proposal to test | Why it is still open |
|------|------------------|----------------------|
| `first_at` | 75, sweep {60, 75, 90}, plus a 76 sensitivity against the closed `band_exit` | 75 is the top of an in-house band, not a published threshold |
| `interval` | 15, sweep {10, 15, 20} | A shorter interval raises the chance a long transcript is stopped by repeated noise |
| Snapshot | Hybrid v0 (stats + brief anchor + last 8 turns) | Tail-only, stats-only, and char-capped windows can win on the smoking guns |
| Question set | Five-question `session-checkout` v0 | The resolved two-question `session-progress` set may match gold as well |
| `confidence_min` | 3 on a 0–3 score, sweep {2, 3} | A lower bar cuts overshoot and raises false early stops |
| Gold aggregation | Earliest unanimous checkout | Majority and median rules move `gold_exit_turn` when judges disagree |
| Fixed vs rising bar | Fixed `confidence_min` at every checkpoint | A rising bar is a different policy and is outside the default grid |
| Judge bundle vs Jev state | Judges may see a larger structured prefix than the 12k Jev state | The gap between those views is itself a result to measure |

## Non-goals

- **Live Claude.** No `PostToolBatch` install, no hook timeout probe, no runner image change. Proof is replay of stored JSONL, Jev or schema dry-run on the snapshot, and comparison to gold.
- **Product wiring.** `install.sh`, default Claude settings, the driver, `assert_phase --deterministic`, and `classify.py` stay untouched. Classify stays a visualisation POC.
- **Feedback channel.** Once a signal is good, telling the parent versus injecting Claude hook `additionalContext` into the worker is a later product decision. This pack does not design or prove that channel.
- **Hard stops.** Replay `gate_exit` is a counterfactual turn. It does not block a worker, a merge, or a phase.
- **Rewriting the resolved paper.** Use cases 2–4 and the closed thresholds (`band_exit` 76, handoff 85 / 125k / 3MiB, escalate 100 / 130k / 5MiB, one optional `session-progress` call) remain the accepted recommendation until Cody accepts a change.
- **Per-turn Jev.** The schedule is sparse. `GOALS.md` still lists per-turn Jev inside the worker loop as out of remit.
- **Calling this pack high-confidence** before the proof stages in [`proofs/README.md`](../RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/README.md) have emitted agreement statistics and an overshoot table.

## What has to be true before a recommendation can lock

1. A corpus manifest of real JSONLs with at least 75 assistant turns, including the two smoking guns when their paths exist. Redacted copies are in `docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers/`. Raw Ubuntu JSONLs are not in this repo.
2. A multi-model gold table whose inter-rater reliability clears the pre-registered floor (Krippendorff’s alpha, with the Landis–Koch moderate band as the floor). Below that floor the rubric changes. Jev does not get tuned to noise.
3. An offline sweep of the grid against that gold: overshoot, false early, false late, and `max_allowed_turns`, stratified by transcript length so repeated testing of long workers is visible.
4. A written comparison of those numbers to the public results cited in [`LITERATURE.md`](../RESEARCH/2026-10-01-progressive-jev-session-gates/LITERATURE.md), including where those results do not transfer (SWE-bench step counts are not this band; LLM-judge agreement with humans is not agreement among our panel).

Until those four exist, the v0 question set and the hybrid snapshot are a protocol, not a finding.
