# Interception / Steer-to-Stop: What Success Means

**Date:** 2026-10-02  
**Scope:** Docs-only, first-principles design for the whole Coding Harness Manager / Jev interception system, including Maps-style evaluation and proposed Pilot / wave-002 scoring.

> **2026-10-02 — contrast, not the next primary.** For the theory → signal → subset loop, this rating → fire chain is the recorded contrast. The primary grammar is float closeness: [`../2026-10-01-progressive-jev-session-gates/DESIGN-signal-closeness-v0.md`](../2026-10-01-progressive-jev-session-gates/DESIGN-signal-closeness-v0.md) and [`SIGNAL-CLOSENESS-CONTRAST.md`](SIGNAL-CLOSENESS-CONTRAST.md). The success definition below is unchanged. It does not authorise behaviour.

**TL;DR:** Interception succeeds when it predicts that a job is likely to run long **and** identifies a good moment to steer the agent toward stopping. An agent doing productive development around turn 75, actively writing and showing credible confidence, should keep using its effective context; re-check roughly 15 turns later. Prematurely truncating useful work or a near-complete closing sequence is costly. Catching a trajectory that would otherwise run toward 360 turns is the win. Measure **`(state, question, response-class) → rating → fire-time vs ideal steer`**, balancing near-done false-positive cost against runaway-intercept misses. This requires **hundreds–thousands of lever variants, with a working target of 1,000–5,000**, supported by enough independent trajectory evidence to make reasoned decisions. Thin-n pilots are insufficient. Flash/Luna can drive variation generation and exploration; cross-model agreement is explicitly rejected as a gold standard or success criterion. **Soft Standard HOLD remains: docs only, no TypeSafe, no hooks unlock, and no unlock until the design lands.**

## 1. Success definition: steer-to-stop decision quality

The decision is: **Is this job likely to continue excessively, and is now a useful time to steer it toward stopping?**

Those are separate requirements. A long session may still be making valuable progress. A plausible future runaway does not automatically justify interrupting the current productive phase.

The measurement chain is:

```text
(Jev state, question, response-class)
    → predictive rating
    → fire / defer decision
    → fire-time relative to ideal steer
```

- **State** supplies evidence about the agent’s current work, progress, remaining work, blockers, repetition, and closing stage.
- **Question** determines what judgment the interception mechanism elicits.
- **Response-class** captures the kind of answer returned and how that answer maps into a rating.
- **Rating** predicts whether steering now would improve the trajectory.
- **Fire-time** is the point at which the interception policy actually recommends steering.

The **ideal steer** is the earliest useful opportunity to prevent excessive continuation without sacrificing worthwhile development or completion. It may be a window rather than a single turn. Some sessions have no appropriate intervention window because they finish naturally.

Success requires both predictive quality and good timing. Correctly predicting a long trajectory but firing during valuable development is not a successful interception. Agreement between models does not establish either requirement.

Success also requires sufficient evaluation volume and coverage to support the decision. A favorable result from a thin pilot does not establish that a policy separates near-done false positives from runaway misses or fires at the right time.

## 2. False-positive / near-done cost versus runaway miss

The evaluation must make the asymmetric costs visible.

| Outcome | Meaning | Cost to measure |
|---|---|---|
| Premature productive-work interception | Steering interrupts useful development | Lost progress, broken continuity, recovery work |
| Near-done false positive | Steering interrupts validation, final fixes, or delivery | Completion displaced, work left unfinished, unnecessary restart |
| Runaway-intercept miss | No useful steering occurs before excessive continuation | Avoidable turns, repetition, resource use, delayed delivery |
| Well-timed interception | Steering catches excessive continuation at a useful stopping boundary | Waste avoided while preserving useful work |

A near-done session is not a runaway simply because its turn count is high. Closing work can still have substantial value.

The prior should therefore resist early exits that truncate productive or closing stages, while still detecting trajectories that would otherwise continue toward 360 turns. “Fewer turns” alone is not the objective.

Use a cost-weighted score that penalizes premature and near-done interventions and missed runaway windows. Report those components separately so a policy cannot appear successful merely by firing rarely or by stopping everything early. The cost weights are explicit evaluation choices, not established facts.

Report sample support and uncertainty for each component. A low aggregate cost from sparse near-done or runaway coverage is insufficient evidence. Check whether conclusions remain stable across additional batches and reasonable cost-weight choices.

## 3. Progressive re-check window

Interception should support **defer and re-check**, not force every checkpoint into an immediate stop decision.

At approximately turn 75:

- If the agent is doing hard development, actively writing, and showing confidence supported by progress, let it keep running.
- Preserve the value of the context it already has.
- Re-check roughly 15 turns later and ask whether **now** is the right time to steer.

At the next checkpoint, assess what changed: concrete progress, remaining scope, unresolved blockers, repeated attempts, and whether a usable stopping boundary has emerged.

Steer when evidence supports both excessive future continuation and a useful current intervention point. Continue when meaningful work is progressing or completion is close.

The approximately 15-turn interval is a re-check cadence, not an automatic firing deadline. Evaluation must score the checkpoint sequence: an appropriate deferral followed by a timely interception can be better than an early fire.

## 4. What to measure on Maps-style sessions

All testing can be done without LLM comparison. The test surface is **variants of Jev state, question, and response-class**, evaluated against steering timing and trajectory evidence.

Include sessions or session segments representing:

- Productive development around turn 75.
- Productive work continuing through the next re-check.
- Near-done validation, final fixes, and delivery.
- Repetition or scope expansion leading toward excessive continuation.
- Ambiguous checkpoints where deferral preserves a later decision opportunity.

Vary each lever independently, then test combinations:

| Lever | Example variation | Evaluation question |
|---|---|---|
| Jev state | Progress history, remaining work, repetition, closing-stage evidence | Does the rating respond to evidence relevant to steering? |
| Question | Ask about expected continuation, value of current work, or suitability of stopping now | Does the question distinguish likely runaway from current timing? |
| Response-class | Productive continuation, near completion, likely runaway, uncertainty | Does class-to-rating mapping preserve useful distinctions? |

For each checkpoint, record the inputs, rating, decision, and subsequent trajectory. Establish an ideal steering window from explicit review criteria and observable continuation evidence, with uncertainty recorded where necessary. Later evidence belongs in evaluation; it must not leak into the checkpoint input.

Measure near-done false positives, productive-work interruptions, runaway misses, and timing relative to the ideal window. Natural-completion sessions must be included to expose unnecessary interventions.

A replay can test ratings and firing decisions. Claims about what steering actually prevents require evidence from the resulting trajectory; an observed long session alone does not prove every earlier intervention would have helped.

## 4b. Lever-grid volume targets

The design needs **many variations**, large enough to make reasoned decisions about the state / question / response-class levers. Dozens of cases or a thin pilot are insufficient.

Use these order-of-magnitude planning targets:

| Evaluation stage | Volume target | Purpose |
|---|---|---|
| Initial grid exploration | Several hundred distinct, coherent lever variants | Find missing cells, ambiguous wording, and mappings that collapse useful distinctions |
| Main lever sweep | **1,000–5,000 distinct lever variants** | Compare configurations across phases, timing boundaries, and outcome classes |
| Boundary and uncertainty expansion | Additional hundreds–thousands where evidence remains weak | Resolve near-done false positives, runaway misses, and unstable cost estimates |

A concrete starting grid could use **24 state scenarios × 12 question variants × 8 response-class formulations or mappings = 2,304 combinations**. These are exploration targets, not measured results or proof of statistical sufficiency. Check combinations for coherence and replace invalid cases; paraphrases and duplicates must not inflate the count.

Cross work phase with timing: productive development, closing work, repetition or scope expansion, ambiguity, and natural completion; around turn 75, the next re-check, and before, within, or after an ideal steering window where one exists. Include sequences that change phase between checkpoints. Give near-done cases and runaway boundaries explicit coverage so common productive states cannot dominate the score.

The reason for this volume is to:

- Separate costly near-done false positives from missed runaway opportunities.
- Cover phase / timing cells and interactions among the three levers.
- Test whether small wording or mapping changes shift fire-time.
- Obtain cost estimates that remain stable as evidence accumulates.

**Lever count and independent evidence count are different.** Thousands of variants derived from a few sessions remain thin trajectory evidence. Track variants, source sessions, checkpoint sequences, and support per phase / timing cell separately. Keep variants from the same source session together when separating exploration from evaluation, and account for their dependence when estimating uncertainty.

Use Flash/Luna as **variation drivers** in batches of roughly **100–250 candidate variants**, using explicit cell quotas, seed scenarios, and controlled changes to individual levers before combination sweeps. Review each batch for coherence, duplicates, coverage, and accidental inclusion of future trajectory evidence. Feed gaps and unstable decisions into the next generation batch. Their role is generation and exploration; neither model supplies gold judgments or participates in an agreement panel.

Do not conclude that the grid is sufficient merely because it reaches a numeric target. Expand coverage and independent trajectory evidence until the separate false-positive, miss, timing, and cost estimates have decision-useful uncertainty and remain stable across further batches. Thin pilots can expose design defects; they cannot justify policy selection or an unlock.

**Soft Standard HOLD remains. This is docs-only design work. No unlock until the design lands; meeting a volume target does not itself authorize TypeSafe, hooks, or live Jev changes.**

## 5. Proposed Pilot / wave-002 scoring

Pilot / wave-002 scoring should evaluate the **whole interception decision chain**, rather than a dual-label versus Flash bakeoff.

The proposed evaluation unit is a session trajectory with successive interception opportunities. Score:

1. Whether ratings distinguish productive continuation, near completion, and likely excessive continuation.
2. Whether the policy defers appropriately during valuable work.
3. Whether firing occurs inside a useful steering window.
4. Whether missed or late interventions allow avoidable runaway continuation.
5. Whether early interventions sacrifice progress or completion.

Compare lever configurations by their cost-weighted decision quality and timing. Agreement rates between models are neither a primary metric nor a substitute for trajectory evidence.

Report the lever-grid volume, independent session support, phase / timing coverage, and uncertainty alongside the score. Evaluate promising configurations on held-out source sessions so selecting among thousands of variants does not turn exploration results into claimed success.

A thin-n Pilot / wave-002 result is insufficient for reasoned policy decisions, even if its aggregate score looks favorable. It can inform the next sweep, but cannot establish success or justify an unlock.

This is a scoring design proposal only. It does not report a scoring implementation, deployment, or live Jev unlock.

## 6. Explicit non-goals / holds

- **Soft Standard HOLD remains in place.**
- **No TypeSafe.**
- **No hooks unlock.**
- **No Pilot live Jev unlock in this note.**
- **Markdown design note only:** no shipping behavior or code changes are claimed as completed work.
- **No unlock until the design lands:** thin pilots, favorable scores, or reaching a volume target do not lift the hold.
- No thin-n pilot treated as sufficient evidence for reasoned policy decisions.
- No dual-label versus Flash comparison as the organizing objective.
- No model consensus, comparison panel, or agreement-derived gold labels.
- No fixed turn count treated as sufficient reason to stop.

## 7. LLM as lever-variation driver versus LLM as gold judge

**Accept: LLM as lever-variation driver.** LLMs can generate large numbers of variations across Jev state, question wording, and response-class examples. Their role is to explore the lever space and expose how tweaks change answers, ratings, and firing decisions. Generated cases should be checked for coherence and coverage.

Flash/Luna can drive the hundreds–thousands of variants described in section 4b through bounded batches, targeted cell coverage, and further exploration of unstable boundaries. Using both expands the candidate space; their agreement is not an evaluation signal. Generated cases can expose sensitivity, but do not create independent observed trajectories or establish an ideal steering window.

**Reject: LLM as gold judge.** LLMs must not supply gold labels, form comparison panels, or turn multi-model agreement into evidence of success. Agreement does not establish that stopping would preserve useful work or prevent a runaway.

For both generated cases and observed sessions, measurement remains:

**`(state, question, response-class) → rating → fire-time vs ideal steer`**

The score remains the cost of near-done and premature false positives versus missed runaway interception. Reasoned decisions require broad lever coverage and sufficient independent trajectory evidence; thin-n pilots are insufficient.
