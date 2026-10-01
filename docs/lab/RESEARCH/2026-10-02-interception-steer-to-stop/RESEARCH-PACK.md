# Coding Harness Manager Interception / Steer-to-Stop
## Research Pack / Draft Thesis

**Date:** 2026-10-02  
**Scope:** Research pack / draft thesis; **Soft Standard HOLD**; docs only. No TypeSafe, hooks unlock, Pilot live Jev unlock, or shipping behavior.

**TL;DR:** Multiple competing framings and measurement designs are enumerated below. **No winner is chosen yet.** Interception might be understood as progressive reassessment, horizon control, detection of stalled progress, protection of completion boundaries, or minimization of counterfactual waste. These framings optimize different things and require different evidence. The research must distinguish the cost of stopping useful work too early from the cost of allowing excessive continuation. Cody’s progressive re-check hypothesis is **H1, one candidate among several**. LLMs can drive large lever-variation sweeps; model agreement is rejected as gold evidence of success.

## A. Problem Space: First Principles

### A.1. What decision is the system making?

A Coding Harness Manager observing an ongoing job faces several related questions:

- Is the agent still creating useful value?
- Is that value sufficient to justify further continuation?
- Is the requested deliverable complete, nearly complete, blocked, or still materially unfinished?
- Is excessive continuation becoming likely?
- Would steering now preserve useful work and improve the eventual outcome?
- If the system waits, will it retain a better opportunity to intervene?

These questions are not interchangeable. A session can be long and productive. It can appear nearly finished while repeatedly discovering consequential defects. It can show frequent activity while making no meaningful progress. It can also reach an acceptable deliverable and then continue indefinitely.

The decision surface therefore includes **continue, defer and reassess, or steer toward stopping**. Deferral is meaningful when it preserves productive work and a later interception opportunity. It becomes a failure when repeated deferrals let the useful interception window pass.

“Models agree on exit turn” is explicitly **not the problem statement**. Agreement concerns consistency among judgments. The problem concerns whether the system preserves valuable work, prevents avoidable continuation, and steers at a useful time.

### A.2. Interception success is a system outcome

An interception mechanism contains more than a classifier:

```text
Observed trajectory
    → checkpoint representation
    → assessment
    → intervention decision
    → steering instruction
    → agent response
    → resulting deliverable and continuation
```

Failures can occur at every step. A good assessment can feed a poor threshold. A sensible decision can produce an ineffective steer. An agent can acknowledge the steer and continue working. A stop can reduce turn count while leaving the requested work incomplete.

Research should distinguish:

| Layer | Question | Possible evidence |
|---|---|---|
| Assessment | Did the mechanism recognize the relevant condition? | Checkpoint inputs, ratings, uncertainty |
| Decision | Was continue, defer, or steer justified? | Decision criteria and opportunity sequence |
| Timing | Was this a useful intervention opportunity? | Acceptable windows, boundary evidence, subsequent events |
| Steer execution | Did the agent respond as intended? | Acknowledgment, closing actions, continued activity |
| Outcome | Did intervention improve the overall result? | Completion, quality, resource use, recovery work |

Offline replay can examine assessment and decision behavior. It cannot, by itself, establish what an intervention would have caused.

A timing detector and a successful steer-to-stop system are related research objects, but they require different evidence.

### A.3. Stopping too early versus runaway continuation

The central tension is between two kinds of harm.

**Stopping too early** can destroy valuable development, interrupt validation, displace a nearly finished deliverable, or create additional recovery work. Near-done false positives deserve separate attention: a small amount of remaining work may have disproportionate value because it makes the entire result usable.

**Runaway continuation** consumes turns, time, context, and attention after further work has become unjustified. It can involve repetition, low-value polishing, repeated reconsideration, or expansion beyond the requested scope.

Neither harm is fully described by turn count. A trajectory heading toward 360 turns is important when much of that continuation is avoidable. The number alone does not establish waste. Similarly, an early stop is not beneficial merely because it saves turns.

A useful research outcome vector is:

```text
Deliverable completion and quality
Productive work interrupted
Near-done closing work interrupted
Avoidable continuation
Interception timing
Steer adherence and post-steer continuation
Recovery burden
Monitoring cost
```

This vector makes tradeoffs visible without prematurely choosing a single weighting.

### A.4. “Ideal steer” may be conditional or absent

An ideal steering point should not be assumed to be a universally correct turn.

Depending on the framing and task, the reference may be:

- An acceptable interval during which steering preserves value.
- A boundary after which additional continuation becomes unjustified.
- A latest defensible intervention point before substantial waste accumulates.
- Several useful windows separated by productive work.
- No intervention, because the session completes naturally.

Different framings may disagree about the ideal window for legitimate reasons. A horizon policy may favor earlier closure than a boundary policy. A waste-minimization policy may tolerate a short stall if recovery remains valuable.

Reference judgments should record their criteria, supporting evidence, and uncertainty. They should not convert reviewer confidence or model consensus into ground truth.

### A.5. What remains unresolved

The pack does not assume that one signal is sufficient, that costs are already known, or that a hybrid is automatically superior. Combining detectors introduces its own questions: which signal takes precedence, how deferral works, and how repeated assessments affect the eventual decision.

All framings below are research propositions. Their measurement designs describe evidence to collect, not behavior authorized for deployment.

## B. Competing Framings and Measurement Designs

### H1. Progressive Re-check — Cody Hypothesis

**1. Name / one-line thesis**

Protect productive work at an early checkpoint, then reassess soon enough to catch emerging excessive continuation at a useful stopping opportunity.

**2. What it optimizes**

The timing of intervention across successive opportunities, balancing premature and near-done false positives against missed runaway interception.

Its prior favors preserving useful context and credible development. Catching a trajectory that would otherwise continue toward 360 turns is the motivating win; reducing every session’s length is not.

**3. Core measurement design**

Use the chain:

```text
(state, question, response-class)
    → rating
    → continue / defer / steer
    → fire-time versus ideal steer window
```

At approximately turn 75, hard development, active writing, and confidence supported by observable progress favor letting the agent run. Re-check roughly 15 turns later. The interval is a reassessment cadence, not an automatic stopping deadline.

Evaluate the entire checkpoint sequence. Record appropriate deferrals, early fires, fires within an acceptable window, late fires, and missed windows. Report productive-work interruption and near-done false-positive costs separately from runaway misses.

The acceptable window must come from explicit trajectory and deliverable criteria, with uncertainty retained.

**4. Failure modes**

- Confidence or visible writing masks unproductive activity.
- Repeated deferral becomes an indefinite escape route.
- A roughly 15-turn interval skips a brief intervention opportunity.
- Question wording drives ratings more than substantive state changes.
- Response classes flatten distinctions between productive continuation, closing work, and waste.
- Retrospective knowledge leaks into checkpoint inputs.

**5. Data needs**

Longitudinal sessions with checkpoint snapshots, progress evidence, question variants, response classes, ratings, and subsequent trajectory. Both natural completions and excessive continuations are needed, including productive development and closing work around the proposed checkpoints.

Claims about avoided continuation additionally require intervention-outcome evidence.

**6. How LLM volume / lever sweeps fit**

LLMs serve as **lever-variation drivers**, generating coherent variants across state, question, and response-class dimensions. They do not supply gold labels or establish correctness through agreement.

The target exploration volume is on the order of **hundreds to thousands of variants**. Thin pilots can check the evaluation plumbing but cannot adequately explore interactions and uncommon failure combinations. Flash/Luna batching is proposed for variation generation, subject to coverage and coherence checks.

Generated variant count must be reported separately from independent session count.

**7. Status**

**Hypothesis / candidate.** Cody’s prior motivates H1; it does not establish H1 as the thesis or winner.

---

### H2. Horizon Control — Budgeted Continuation

**1. Name / one-line thesis**

Bound continuation through a fixed or adaptive horizon, with a soft taper toward closure as the available budget diminishes.

**2. What it optimizes**

Predictability of resource use and exposure to extreme session lengths. This framing asks how much continuation to permit before task-specific evidence becomes decisive.

**3. Core measurement design**

Compare proposed fixed thresholds and adaptive horizons across matched task strata. Specify what a soft taper would mean in each offline candidate: a closure recommendation, reduced scope, or a stronger preference for finishing existing work.

Measure:

- Completion and quality at the proposed horizon.
- Budget exceedance and upper-tail continuation.
- Valuable work displaced by the threshold.
- Closure time after a hypothetical taper.
- Monitoring and resource costs.

Use sensitivity curves across thresholds. A threshold should not appear successful merely because it guarantees shorter sessions.

**4. Failure modes**

- Difficult tasks are penalized for requiring legitimate time.
- A turn is treated as a stable unit despite varying tool and work content.
- Adaptive extensions become effectively unlimited.
- Budget pressure encourages superficial closure.
- A session wastes substantial effort before reaching its cap.
- Aggregate completion rates hide harm to particular task classes.

**5. Data needs**

Task complexity and scope, turn/time/resource histories, deliverable quality, natural completion distributions, and evidence about unfinished work at candidate horizons. Adaptation requires features available before the extension decision.

**6. How LLM volume / lever sweeps fit**

Many threshold sweeps can use recorded trajectories without generated judgments. LLM variation is useful for stressing hypothetical budget-extension rules against ambiguous scope and remaining-work descriptions.

Large synthetic volume cannot replace representative completion and resource distributions.

**7. Status**

**Hypothesis / candidate.** A useful comparator, without assuming turn thresholds define success.

---

### H3. Progress Velocity — Sustained Plateau Detection

**1. Name / one-line thesis**

Steer when the rate of useful progress remains low despite continued activity.

**2. What it optimizes**

Detection of stalls, thrashing, repeated attempts, and low-yield continuation, potentially before a horizon limit becomes relevant.

**3. Core measurement design**

Define progress signals against the requested outcome: resolved requirements, validated fixes, completed sections, reduced uncertainty, or cleared blockers. Estimate changes over time rather than counting activity alone.

Evaluate candidate smoothing windows, plateau durations, and recovery allowances. Measure detection delay after a sustained plateau, interventions during temporary stalls, useful recovery interrupted, and cumulative waste before detection.

Use paired examples with similar activity levels but different substantive progress. This tests whether the detector responds to value rather than movement.

**4. Failure modes**

- Valuable reasoning produces little immediately visible output.
- Investigation temporarily increases uncertainty before resolving it.
- Repetitive-looking actions are necessary for validation.
- Large diffs or verbose output create an illusion of progress.
- Progress signals reward easy subtasks over the actual deliverable.
- A detector misses excessive continuation that keeps producing small artifacts.

**5. Data needs**

A time series of meaningful work signals, tool outcomes, requirement completion, blockers, failed and successful recovery episodes, and qualitative work value. Several task types are needed because progress has different forms in development, research, and writing.

**6. How LLM volume / lever sweeps fit**

LLMs can generate controlled cases where activity, substantive progress, and apparent confidence vary independently. Sweeps can expose dependence on superficial cues.

Observed histories remain necessary to determine whether plateau duration and recovery behavior are realistic.

**7. Status**

**Hypothesis / candidate.** Plausible for stalled trajectories; its ability to distinguish temporary difficulty from waste remains unproven.

---

### H4. Deliverable Boundary — Protect Completion, Detect Overrun

**1. Name / one-line thesis**

Preserve work until a defensible deliverable boundary is reached, then detect unjustified continuation beyond it.

**2. What it optimizes**

Protection of completion and closing stages, followed by reduction of post-completion overrun.

**3. Core measurement design**

Establish task-specific boundary criteria from the request: required content or functionality, relevant validation, resolution of necessary issues, and delivery.

Represent ambiguous boundaries as intervals or sets of defensible completion states. Measure pre-boundary interventions, necessary closing work interrupted, delay after the boundary, and post-boundary continuation without demonstrated value.

Include cases where apparent completion is invalidated by a real defect. Crossing a plausible boundary must not automatically make all subsequent work wasteful.

**4. Failure modes**

- Completion evidence is missing, misleading, or self-reported.
- The agent delivers superficially while requirements remain unmet.
- Necessary late fixes resemble unnecessary polishing.
- Open-ended tasks have no clear boundary.
- A session never reaches a boundary, leaving a pre-completion runaway undetected.
- Boundary detection rewards premature declarations of “done.”

**5. Data needs**

Original requirements, deliverable versions, validation evidence, unresolved issues, delivery events, and reasons for subsequent work. Review must separate required closure from optional expansion.

**6. How LLM volume / lever sweeps fit**

Variation drivers can alter completion claims, validation results, remaining requirements, and post-boundary actions independently. Large sweeps can test whether claims of completion overpower actual evidence.

They cannot establish that a real deliverable meets its requirements merely by agreeing that it looks finished.

**7. Status**

**Hypothesis / candidate.** Focused on near-done protection and post-completion overrun; potentially incomplete for sessions that stall before completion.

---

### H5. Counterfactual Waste — Value of Intervention

**1. Name / one-line thesis**

Steer when the expected waste avoided exceeds the useful value destroyed by intervention.

**2. What it optimizes**

The net outcome of intervention, including turns saved, completion preserved, recovery burden, and monitoring cost.

**3. Core measurement design**

For a checkpoint \(t\), compare possible outcomes:

```text
Net benefit of steering at t
    = avoidable continuation prevented
    − useful work lost
    − closing and recovery costs introduced
    − intervention overhead
```

The components require explicit units or weights. If those weights remain disputed, report component outcomes and sensitivity ranges instead of a single score.

Where feasible within future authorized research, compare continuation and intervention branches from equivalent checkpoints. Ordinary observational replay cannot directly reveal both futures.

Measure estimated intervention value, decision regret relative to defensible alternatives, and uncertainty. A policy should be able to abstain when available evidence does not identify the sign of the benefit.

**4. Failure modes**

- The unobserved alternative future is invented or estimated poorly.
- Retrospective review assumes every long continuation was preventable.
- Saved turns receive too much weight relative to completion.
- Small quality losses accumulate without being measured.
- Results depend strongly on an arbitrary cost conversion.
- A beneficial stop is credited to the detector when the steering instruction caused the improvement.

**5. Data needs**

Comparable trajectories or checkpoint branches, outcome quality, work remaining, resource use, recovery effort, intervention form, and explicit uncertainty about causal effects. This is the most demanding design when causal claims are required.

**6. How LLM volume / lever sweeps fit**

LLMs can generate scenario variations and proposed alternative explanations. Such alternatives are hypotheses to examine, not observed counterfactuals.

Hundreds or thousands of generated futures cannot substitute for evidence of what intervention actually changes.

**7. Status**

**Hypothesis / candidate.** Broadly aligned with system outcomes, with substantial identification and data challenges.

---

### H6. Monitor Agreement — Rejected as Gold

**1. Name / one-line thesis**

Investigate whether agreement among monitors adds diagnostic information, while rejecting agreement itself as proof of interception success.

**2. What it optimizes**

As a standalone proposal, monitor agreement would optimize consistency or confidence among judgments. Those quantities do not establish the desired system outcome.

Its limited research role is to reveal sensitivity, ambiguity, and shared blind spots.

**3. Core measurement design**

If monitor comparisons are retained, measure agreement separately from outcome quality. Examine unanimous mistakes, disagreements on productive and closing work, and whether adding monitors improves decisions against independent outcome evidence.

Include variants that preserve the substantive state while making agreement easier to obtain. This tests whether the metric can rise without any improvement in timing or outcomes.

**4. Failure modes**

- Monitors share correlated errors.
- Prompt wording makes all monitors repeat the same conclusion.
- Consensus confidently interrupts near-done work.
- Agreement improves while completion worsens.
- An exit turn chosen by consensus has no demonstrated causal benefit.
- The evaluation rewards agreement and thereby trains attention away from outcomes.

**5. Data needs**

Monitor inputs, judgments, disagreement patterns, and independent trajectory and deliverable evidence. Agreement-derived labels cannot be used as that independent evidence.

**6. How LLM volume / lever sweeps fit**

LLMs may drive perturbations that expose agreement-without-outcome and metric gaming. Increasing monitor count or comparison volume does not create gold truth.

Flash/Luna use under H1 remains variation generation, not a voting panel.

**7. Status**

**Rejected as a gold standard or standalone success criterion.** Diagnostic use is an open hypothesis. This rejection does not select a winner among H1–H5.

## C. Comparison Matrix

| Framing | Optimizes | Protects | Main FP | Main FN | Data burden | LLM role | Unlock risk if later operationalized | Open questions |
|---|---|---|---|---|---|---|---|---|
| **H1: Progressive re-check** | Timing across checkpoint sequences | Productive context and near-done work | Steer during valuable development or closing | Repeated deferral misses runaway window | Longitudinal snapshots, lever records, uncertain steering windows | Large variation sweeps; no gold judging | Cadence or ratings silently become live rules | How long can deferral remain justified? |
| **H2: Horizon control** | Bounded continuation and predictable cost | Resource envelope | Budget truncates legitimate work | Waste continues below the cap or through extensions | Completion distributions, costs, scope strata | Stress adaptive rules; many sweeps need no LLM | Research thresholds become enforced caps | Which budget unit and adaptation rule are defensible? |
| **H3: Progress velocity** | Detect sustained low-yield work | Sessions making substantive progress | Temporary stall mistaken for plateau | Activity masks lack of value | Detailed progress histories and recovery episodes | Separate activity from value in variants | Proxy signals become stop triggers | Which signals survive task changes and gaming? |
| **H4: Deliverable boundary** | Preserve completion; reduce overrun | Validation, final fixes, delivery | Apparent boundary precedes actual completion | Pre-completion runaway never reaches boundary | Requirements, artifacts, validation, delivery evidence | Vary claims and boundary evidence independently | Completion classifier gains stop authority | Can boundaries be identified before hindsight? |
| **H5: Counterfactual waste** | Net value of intervention | Work whose expected value exceeds its cost | Benefit overestimated; value destroyed | Benefit underestimated; avoidable waste continues | Comparable outcomes, causal evidence, explicit costs | Scenario variation; no invented causal truth | Estimated utility is treated as demonstrated benefit | How identifiable are alternative futures? |
| **H6: Monitor agreement** | Consistency; diagnostic sensitivity | Nothing inherently | Unanimous premature stop | Unanimous acceptance of runaway | Monitor records plus independent outcomes | Perturbation and error analysis | Consensus is mistaken for authorization or truth | Does agreement add information beyond shared inputs? |

**Explicit non-collapse:** This matrix does not choose a winner. It also does not prescribe a hybrid. H1–H5 may disagree because they prioritize different outcomes or use different evidence. H6 is rejected as gold, without settling the competition among the other framings.

Under this pack, **every operational unlock remains held**. The risk column identifies possible future category errors, not permissions.

## D. Open Threads

### D.1. Evidence that would discriminate the framings

The most informative cases are those where candidate policies make different decisions.

| Discriminating case | What it tests |
|---|---|
| Productive development at turn 75 and again around turn 90 | H1 deferral, H2 budget pressure, H3 progress evidence |
| A low-activity investigation that later resolves a major blocker | H3’s treatment of temporary stalls; H5’s lost recovery value |
| A deliverable is complete, but small edits continue indefinitely | H4 boundary detection versus H3’s continuing positive signals |
| A session stalls well before any plausible completion boundary | H3’s reach and H4’s pre-completion limitation |
| A long task remains productive and valuable throughout | Whether horizon control sacrifices warranted continuation |
| A short repetitive episode precedes useful recovery | Tolerance for ambiguity and the cost of early intervention |
| Monitors unanimously recommend stopping before a necessary final fix | Agreement-without-outcome under H6 |
| A good decision produces a steer that the agent ignores | Separation of detection from execution |

Evidence should distinguish **different judgments about value** from **different abilities to predict the same outcome**. If two framings use different cost weights, their disagreement cannot be resolved solely by classifier accuracy.

Potential hybrid policies belong in later hypothesis sets with explicit precedence rules. Combining signals does not remove the need to measure their conflicts.

### D.2. What Maps-style sessions must cover

Maps-style evaluation needs complete trajectories or linked segments that preserve the sequence of opportunities. Isolated checkpoints are useful for lever sensitivity but insufficient for repeated-deferral and timing claims.

Coverage should include:

- Productive hard development and writing around turn 75.
- Continued productivity through the next proposed re-check.
- Near-done validation, necessary final fixes, and delivery.
- Apparent completion followed by discovery of a consequential defect.
- Natural completion without any justified intervention.
- Thrashing, repeated failed attempts, and unresolved blockers.
- Temporary stalls followed by productive recovery.
- Post-completion polishing or scope expansion.
- Trajectories with substantial avoidable continuation, including would-go-to-360 cases.
- Ambiguous evidence where uncertainty and reassessment are warranted.

The set should vary task difficulty, work type, requested scope, evidence visibility, confidence, progress, and remaining work. Confidence and writing activity should vary independently from actual progress.

For each checkpoint, retain:

```text
Source session and checkpoint
Information available at that time
Task and deliverable criteria
Candidate framing and configuration
State, question, response-class, rating
Continue / defer / steer decision
Subsequent observed trajectory
Reference rationale and uncertainty
Whether outcome claims are observed, reviewed, or counterfactual
```

Future information may support retrospective review; it must not enter the checkpoint representation. Variants from one source session should remain grouped when separating development and evaluation material.

Synthetic cases should be identified separately from observed sessions. A thousand correlated variants from ten sessions do not provide the same outcome evidence as a thousand independent sessions.

### D.3. Establishing reference evidence without model gold

Reference evidence should combine observable task outcomes with explicit review criteria. Human review can resolve ambiguity, but human agreement is not automatically causal truth either.

Review should record:

- What work was still necessary.
- What additional work had demonstrated value.
- Why a proposed steering window was acceptable.
- Whether natural completion made intervention unnecessary.
- What remains unknown about the intervention’s effect.

Where evidence supports several windows or judgments, retain that ambiguity. Forcing every case into one exit turn can make the dataset easier to score while making the research less faithful to the problem.

### D.4. Pilot / wave-002 scoring: framing-agnostic

A framing-agnostic score would compare shared outcome dimensions without embedding H1’s measurement chain as the universal definition.

It could report:

- Completion and quality.
- Productive-work interruption.
- Near-done interruption.
- Avoidable continuation.
- Post-steer continuation and recovery burden.
- Monitoring cost.
- Uncertainty and evidence coverage.

This permits comparison across framings. Its limitation is that a single aggregate requires disputed weights, and “avoidable continuation” may remain unidentified in observational data.

A vector of results is therefore more defensible than an unexplained overall score. Timing should be reported only where an acceptable window has adequate support.

### D.5. Pilot / wave-002 scoring: framing-conditional

Conditional scoring tests whether each framing works on its own terms:

| Framing | Conditional scoring focus |
|---|---|
| H1 | Lever sensitivity, appropriate deferral, checkpoint sequence, fire-time versus window |
| H2 | Completion-cost curves, exceedance, extension behavior, tail control |
| H3 | Plateau detection delay, temporary-stall false positives, recovery interrupted |
| H4 | Boundary detection, pre-boundary harm, post-boundary overrun |
| H5 | Estimated benefit, observed outcome difference where available, uncertainty, regret |
| H6 | Agreement/outcome dissociation and diagnostic value; no consensus gold |

These scores are not automatically comparable. Good plateau detection does not prove low intervention harm. Accurate boundary detection does not prove runaway prevention before completion.

A useful research reporting arrangement is to show shared outcomes alongside conditional diagnostics. That is a scoring proposal, not a selected interception policy.

Pilot and wave-002 should also distinguish evidence levels:

| Evidence level | Supports |
|---|---|
| Synthetic variants | Sensitivity, coherence, coverage, failure discovery |
| Observational replay | Assessment and proposed decision behavior |
| Reviewed trajectories | Reference windows and outcome descriptions, with uncertainty |
| Comparable intervention outcomes | Stronger claims about the effects of steering |

A thin pilot can validate recording and scoring mechanics. It cannot settle the high-volume lever question, rare harms, or causal benefit.

### D.6. Soft Standard HOLD implications

Soft Standard HOLD allows this pack to specify hypotheses, data requirements, proposed scores, and discriminating experiments. It does not turn a candidate cadence, threshold, detector, or score into operating behavior.

Research results should state which claims remain unsupported and what evidence would be needed next. Evaluation readiness and policy selection are separate from authorization to change live behavior.

This pack does not propose that favorable offline scores automatically release any hold.

## E. Non-goals / Holds

- **Soft Standard HOLD remains in place.**
- **No TypeSafe.**
- **No hooks unlock.**
- **No Pilot live Jev unlock.**
- **Docs only:** no implementation, deployment, or shipping behavior is claimed or authorized.
- No multi-model agreement as gold labels, a gold exit turn, or proof of success.
- No premature winner among the substantive framings.
- No assumption that fewer turns always means a better outcome.
- No conversion of generated variants into independent outcome evidence.
- No claim that replay alone proves what steering would prevent.
- No automatic promotion of a research threshold, cadence, score, or hybrid into a live policy.

## F. Appendix: Cody-Hypothesis Detail

**This appendix preserves material under H1. It is not the thesis of the whole paper.**

### F.1. Progressive re-check window

At approximately turn 75, let the agent continue when it is doing hard development or writing and its confidence is supported by concrete progress. Preserve the useful context and continuity already established.

Re-check roughly 15 turns later—approximately turn 90 in this example. Assess what changed: useful progress, remaining work, blockers, repetition, closing-stage evidence, and the availability of a stopping boundary.

The interval is a hypothesis about observation cadence. It is neither a firing deadline nor permission to defer indefinitely. Evaluation should examine variation in the initial checkpoint, re-check interval, and conditions that justify another deferral.

### F.2. Measurement chain

```text
(state, question, response-class)
    → rating
    → continue / defer / steer
    → fire-time versus ideal steer window
```

**State** represents evidence available at the checkpoint. **Question** controls what judgment is elicited. **Response-class** preserves the kind of answer and its mapping to a rating. **Rating** informs the decision. **Fire-time** records where the resulting policy would intervene across the session.

The chain must preserve uncertainty and distinguish likely excessive continuation from whether stopping **now** is useful.

### F.3. False-positive and runaway costs

| Outcome | H1 concern |
|---|---|
| Productive-work false positive | Useful development interrupted; continuity or progress lost |
| Near-done false positive | Necessary validation, final fixes, or delivery displaced |
| Appropriate deferral | Valuable work preserved while retaining a later opportunity |
| Late or missed interception | Avoidable continuation accumulates after a useful window |
| Well-timed interception | Excessive continuation prevented while useful work is preserved |

Cody’s prior gives substantial weight to early-exit harm, especially near completion. Catching a trajectory that would otherwise continue toward 360 turns is the motivating success case.

That prior is an evaluation choice to test. It does not establish that every long session is runaway or that every early intervention is harmful. Report the components separately and examine sensitivity to their weights.

### F.4. Lever-grid volume

Explore the lever space at an order of magnitude of **hundreds to thousands of variants**, rather than treating a thin pilot as sufficient evidence.

Candidate axes include:

| Lever | Illustrative dimensions |
|---|---|
| State | Progress, remaining work, blockers, repetition, closing evidence, confidence support |
| Question | Expected continuation, value of current work, suitability of stopping, need to reassess |
| Response-class | Productive continuation, near completion, likely excessive continuation, uncertainty |
| Mapping and cadence | Class-to-rating mapping, decision threshold, re-check interval |

The purpose of volume is to expose interactions, sensitivity, uncommon combinations, and changes caused by wording or representation. Controlled contrasts should accompany broad variation so failures can be explained.

Flash/Luna batching is proposed as a way to drive large variation sets. Record coherence checks, coverage, source-session dependence, and rejected variants. Raw count alone is not evidence of adequacy.

### F.5. LLM as driver versus gold judge

**Accepted research role:** LLMs generate and vary cases, question formulations, and response-class examples. They help explore how levers affect answers, ratings, and proposed firing behavior.

**Rejected gold role:** LLMs do not establish ideal steering windows, causal benefit, or correct exit turns through their own judgments or agreement. Multi-model agreement remains secondary diagnostic information and is rejected as gold.

H1’s measurement remains:

**`(state, question, response-class) → rating → fire-time vs ideal steer`**

Its unresolved empirical question is whether progressive reassessment can preserve productive and near-done work while reliably catching excessive continuation. That question remains alongside the competing questions posed by H2–H5, under **Soft Standard HOLD**.

## G. First Offline Experiment Wave (parallel; Soft Standard HOLD ≠ pause)

**Status:** Offline trials may run in parallel (Soft Standard HOLD ≠ pause), but **Wave-0 is not score-ready until a leakage audit + T-independent checkpoint schedule + evidence-based (not length-only) outcome sheet** land — see Opus adversarial R1–R3. **Does not unlock Soft Standard, TypeSafe, hooks, or live Jev.** Do not wait for a framing winner; do not promote contaminated batches.

### G.1. Purpose

Burn Flash/Luna **as lever-variation drivers** against real session inventory to produce empirical traces under multiple framings — without collapsing the pack to H1 and without treating model agreement as gold.

### G.2. Corpus / shortlist inputs (reuse, don’t invent)

Preferred sources (read-only / offline):

- Progressive Jev session-gates inventory and ubuntu-raw dry-run thrash tables under `docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/validated/`.
- Shape-signal / full-Maps packs and shortlists already documented in `NEXT-EXPERIMENTS.md` and related validated gold summaries.
- Open-field / Pilot field-proof captures already on disk under session-analysis research trees.

Pre-register the worker ID set and checkpoint turns **before** labeling. Prefer T≥75 strata plus known near-done, productive-mid, and runaway-candidate shapes. Do not pad shortlists to force agreement.

### G.3. Wave-0 protocol (offline)

1. **Freeze a framing-agnostic outcome sheet** per session/checkpoint: closing-stage / thrash / requirement evidence from the transcript (not length alone), whether productive edits continued, natural completion vs runaway-like continuation, termination cause, human-steer count. Ideal windows may be `none`/`ambiguous`. **Length-derived windows are not reference evidence.** Prefer explicit review criteria + observables; record uncertainty. **No LLM gold panel.** Run a **leakage audit** listing every state/prompt field and flagging any dependence on post-checkpoint events (esp. `T_observed`, `approx_progress_frac=cp/T`). Use **T-independent checkpoint schedules**; score interventions conditional on survival to t.
2. **H1 lever sweeps (Flash/Luna volume):** generate large batches of `(state, question, response-class)` variants from frozen session snapshots; score fire/defer vs the outcome sheet’s ideal-steer window where available. Target order-of-magnitude: hundreds first, then push toward 1k+ where cells are sparse. Batch ~100–250 variants; coherence-check; no agreement-as-success.
3. **Parallel thin probes for H2–H5 (not winners — discriminators):**
   - H2: apply candidate horizon/budget rules offline; record truncation of productive vs runaway tails.
   - H3: plateau/velocity features on the same checkpoints; temporary-stall false positives.
   - H4: boundary/closing markers vs overrun after apparent completion.
   - H5: where paired counterfactual evidence exists (or bounded proxies), estimate intervention value; otherwise mark unidentified.
4. **H6 diagnostic only:** if multi-monitor outputs exist, measure agreement/outcome dissociation — never as unlock criterion.
5. **Emit per-framing scorecards + shared matrix rows**; update Section C/D with empirical cells as data lands. Do not declare a winner from Wave-0.

### G.4. Soft Standard HOLD while trials run

- Offline / dry / replay only unless a separate, explicit unlock is granted.
- Soft Standard HOLD remains; meeting volume targets does not authorize shipping behaviour, TypeSafe, hooks, or Pilot live Jev.
- Thin pilots remain insufficient for reasoned unlock; Wave-0 is evidence generation, not promotion.

## H. Evidence Fold-in (as Flash/Luna offline lever sweeps land)

**Do not wait for perfect theory.** As CHM’s Flash/Luna offline lever sweeps produce artifacts, fold them into this pack without collapsing framings.

### H.1. Intake slots (append-only)

Maintain a running evidence log (sibling or subsection under `.scratch/` / later `docs/lab/RESEARCH/…`) with rows:

| Landed artifact | Framing(s) touched | n variants / sessions | Near-done FP signal | Runaway miss signal | Notes / caveats | Date |
|---|---|---|---|---|---|---|
| `docs/lab/RESEARCH/2026-10-02-interception-trials/batch-001/` | H1-heavy (H2–H5 thin) | see batch PROTOCOL | **contaminated / not scored** | **contaminated / not scored** | Opus R1–R3: T leak into prompts/state; length-derived ideal window; T-dependent schedule. Log as **plumbing-only** until leakage audit. | 2026-10-02 |

### H.2. Fold-in rules

1. Map each sweep to one or more of H1–H5 measurement columns; never overwrite competing framings with H1-only narrative.
2. Prefer reporting **fire-time vs ideal** and cost components over preference/agreement rates.
3. If a sweep only exercises H1 levers, say so; spawn H2–H5 probes rather than claiming holistic coverage.
4. Reject any “models agreed → success” summaries; convert to diagnostic footnotes under H6 if useful.
5. Update open threads (Section D) when evidence discriminates or fails to discriminate; leave winner unset.

### H.3. Parallelism with theory

Research-pack revision and offline volume proceed **in parallel**. Soft Standard HOLD constrains shipping behaviour, not experiment throughput.

## I. Adversarial gate pointer (Opus, 2026-10-02)

Sibling adversarial review: `.scratch/2026-10-02-interception-research-pack-adversarial.md` (also `/tmp/2026-10-02-interception-research-pack-adversarial.md`).

Gate focus: premature collapse, missing framings, metric-gaming, Wave-0/evidence fold-in challenges. **Soft Standard HOLD unchanged.** No framing winner selected. Opus verdict: pack ready as research-pack draft **conditional on amending §G** for Wave-0 leakage/prereg concerns (T-leak / length-as-runaway / H1 cadence as universal sampling frame). Treat any concurrent Flash/Luna batch artifacts as **plumbing evidence until a leakage audit** — fold via §H intake slots; do not promote scores.

Recommended Composer land (path only; not opened by this harness): `docs/lab/RESEARCH/2026-10-02-interception-steer-to-stop/` with `RESEARCH-PACK.md`, `ADVERSARIAL-GATE-opus.md`, `EVIDENCE-LOG.md`, `WAVE-0-PREREG.md`.
