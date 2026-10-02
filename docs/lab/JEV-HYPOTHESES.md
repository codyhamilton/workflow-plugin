# Jev research hypotheses — workflow decisions and session length

**Status:** hypotheses, not established outcomes. **Owner:** Cody + Workflow Optimiser. **Updated:** 2026-10-03.

**Human provenance:** [`PROVENANCE-jev-hypotheses-2026-10-02.md`](PROVENANCE-jev-hypotheses-2026-10-02.md) preserves Cody's wording verbatim and maps it to this agent-written synthesis. Where this file specifies a research procedure or metric beyond that wording, it is an agent interpretation to test.

**Evidence and method:** start with the [lab result register](JEV-RESULTS.md), then use the [active methodology](JEV-METHODOLOGY.md). The procedure sketched below is subordinate to that research loop and the results it produces.

This is the parent question for the Jev research packs and white papers. A working hook, a valid request schema, a simulated threshold, or agreement among model judges proves only that part of the method. It does not by itself show better work, fewer tokens, or a good decision.

## H1 — cheap judgement at structural workflow gates

Jev may help a workflow agent make a cheap, context-specific judgement at **exit from design, exit from refine, and exit from build**. At each gate, the decision is whether there is enough evidence to advance or whether the current stage needs more work. We hypothesise that using that judgement alongside the existing structural checks will improve the quality of the final work. In some cases it may also reduce rework, lower cost by giving agents better-sized remits, or avoid reviews that add little value. These are separate possible effects, not guaranteed consequences of a Jev score.

The phase-boundary problem appears simpler than session timing, but the corpus of completed plans is much smaller. The economic hypothesis is that an occasional avoided agent pass may repay many cheap Jev calls. That **does not** justify permissive decisions: a false confident advance or skipped review can cause misalignment and rework. Start conservatively. Act on a Jev answer only when its confidence is high and the relevant deterministic checks pass; otherwise use the current workflow. Low coverage or many missed opportunities is acceptable if the few actions taken are sound and their measured savings exceed call cost. Here “initial accuracy is less important” means **high recall is not required**; precision on actions taken, especially avoided work, is essential.

| Structural gate | Decision to test | Present coverage |
|---|---|---|
| Design exit | Do separate criteria hold: does the design address the problem, and are phase outcomes and brief success criteria measurable, well defined, and justified rather than arbitrary? Ask simple language yes/no questions with confidence for each answer; use a conservative combined bar to decide whether to advance. | **Gap:** the accepted four-signal paper has no design-exit Jev question or empirical result. The question set and bar are proposals to test. |
| Refine exit | Given the briefs, return a continuous size rating for each and the expected scope of files required. Use these to prioritise further refinement or review; confidently low-risk briefs may avoid that work. | The accepted `refine-brief-complexity` proposal ranks up to three briefs for attention. It does not establish the file scope, whether a brief is ready, or the safety of skipping its review. |
| Build exit | Does the built phase meet its stated outcome, or does it need correction before advancement? | The accepted `unit-needs-review` and `phase-alignment-sanity` proposals are advisory pieces of this gate. The existing deterministic phase assert remains authoritative for structural failures. |

At design exit, ask about brief success criteria only if the design actually specifies them. Otherwise judge the phase outcomes and any stated acceptance criteria there, then judge the concrete brief criteria after refine. A missing artifact cannot receive a confident pass.

The review choice at unit completion is a **possible consequence of the build assessment**, not a fourth structural phase boundary. A Jev recommendation to skip or request review has not yet been shown safe or cost-effective. At refine exit, the prospective benefit is chiefly the briefs **not** sent for further review; count those savings only after checking whether the skipped briefs later caused defects or rework. The existing in-session `PostToolBatch` signal belongs to H2 below.

**Evidence needed:** define each gate's input state and independently assessed outcome; compare the current workflow with the same workflow using Jev advice on comparable real tasks or replayable cases. Record advance versus rework decisions, missed defects or false advances, final outcome quality, review count and yield, agent remit size, rework, and total provider cost. Report the three gates separately before claiming a whole-workflow benefit. Count a reduced review as a gain only if downstream quality does not deteriorate. Keep deterministic checks as the authority where they already exist.

**Small-corpus study:** keep a case-level record of each answer, its confidence, whether it would have changed the workflow, and the eventual result. First evaluate the conservative subset of cases where the bar is met. Avoid tuning many question and threshold variants to the same few plans and then reporting that fit as general accuracy. For refine, compare predicted size and file scope with the files and work actually needed; also inspect a sample of briefs whose review Jev would have skipped. For design, separately report which criterion failed and whether that omission mattered downstream. Always show avoided agent work minus Jev call cost, alongside any quality loss.

## H2 — economical handling of long agent sessions

Sessions beyond roughly **75 assistant API turns** can become cost-inefficient as repeated context and cache reads accumulate. Cody's current ideal window is **about 50 turns or fewer**, so the first candidate observation is now **turn 60**, before the earlier 75-turn concern. Neither number is a proven universal optimum or a hard stop. The core hypothesis is that a set of observable signals can distinguish work likely to finish usefully soon from work likely to continue for a long time. Jev can cheaply judge whether each signal is present in the current prefix and return a confidence for that signal. An offline policy combines the individual signals into **confidence to let the agent continue**. If that confidence clears a bar, the agent continues and is checked again about 15 turns later. At each re-check, the policy modestly discounts continuation confidence so continuing indefinitely needs fresh supporting evidence. If confidence no longer clears the bar, the supervisor considers steering to a closing message, compaction, or handoff. The signal set, combination rule, discount, bar, and action choice are all research variables, not accepted runtime policy.

For example, a passed test suite **might** be a near-completion signal for some engineering tasks if it commonly occurs shortly before useful completion. It might instead occur early, recur many times, or precede a long fix cycle. The first question is whether the observed event predicts a defined outcome in the relevant task population. Only then is it useful to test whether Jev can recognise the event from a bounded state representation. No single generic question such as “will this session run long?” substitutes for that work.

**Scope of this white paper (human input 7):** it tests only whether Jev calls reliably predict when the steering message should fire, and that it avoids firing on sessions about to end anyway. Net benefit of steering is a later stage. See [methodology](JEV-METHODOLOGY.md) Stage A / Stage B.

### H2 economic premise (human-reported, 2026-10-03)

Cost accumulates nonlinearly with turn count times context, because cache reads repeat. Externally verified over many thousands of transcripts (per Cody; not yet reproduced on lab data): the top 15% of subagents account for about 70% of subagent cost, and a few breakaway agents running to several hundred turns can roughly double a session's cost. The claim is that stopping such an agent is beneficial **whether or not its work was productive**, even after paying for replacement agents. Break-even precision for an intervention is therefore expected to be low (probably under 5%), not the 30% once assumed in the cheap-judgement economics worksheet, which was an unsupported placeholder.

Consequences to test: the target is the **cost tail**, not a "runaway" quality label, so productive-versus-unproductive labels matter less than cost-per-turn growth and the replacement cost of a handoff. This weakens the low runaway base rate (2 of 20 labelled sessions) as an objection, but it moves the burden to measuring handoff and re-priming cost honestly. Replication on lab transcripts using usage data is the cheapest first check.

### H2 research sequence

Five stages: qualitative signal discovery, independent signal-outcome association, Jev matcher trials, combination and replay, then an intervention test. Stage A of the [methodology](JEV-METHODOLOGY.md) covers the first four on historical transcripts; the intervention test is Stage B. Procedure lives there, not here.

### H2 track B — hook-event state (added 2026-10-03, hypothesis)

An alternative to transcript-prefix snapshots: build Jev's state from hook events only, **`UserPromptSubmit`** (what the user said) and **`PostToolBatch`** (what the agent is doing). Candidate windows: last N tool batches (for example 5), all user prompts, both, plus cheap counters. Origin: [provenance input 5](PROVENANCE-jev-hypotheses-2026-10-02.md). Small uniform state is cheap per call, so Jev could run more often on a narrower question.

`PostToolBatch.tool_calls[]` carries `tool_response` (the [hook proof](RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/post-tool-batch-hooks.md)), and every hook receives `transcript_path`, so omitting outputs is a **design choice, not a constraint**. Variants to compare: no outputs, truncated outputs or exit status only, and full responses. Which signals survive without outputs is the open question, not a given.

Constraints to verify: the proof records no hooks on Cursor Cloud Agent or OpenCode; whether Cursor's **local** hooks provide equivalent events is not yet checked. Hook state must be reproducible from historical transcripts for replay. Frequent calls multiply correlated trials and add synchronous latency; meter total Jev cost per session.

## Research discipline and current status

- **Feasibility is not efficacy.** The [cheap-judgement paper](PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) resolved four advisory signal designs and validated hook mechanics, thresholds, and request shapes. It has not measured their decision quality, final quality, review savings, or net cost. H1 is therefore open, including the uncovered design-exit gate.
- **Session timing remains open.** The [progressive-session pack](RESEARCH/2026-10-01-progressive-jev-session-gates/INDEX.md) and [interception paper](PROPOSALS/2026-10-02-interception-steer-to-stop.md) provide offline observations and trial designs for H2. They have not established a safe, economical action policy. Behaviour ship remains held.
- **Independent outcomes are required.** Neither model agreement nor shorter sessions are the reference outcome. Label work and quality from deliverable and transcript evidence without exposing future session length or the Jev response to the judge input. Separate decision accuracy from whether the workflow acted on the advice and from the resulting quality/cost effect.
- **Claims stay local.** A useful signal on one gate, task type, harness, or worker shape does not validate the other gates or all long sessions. State each finding with its denominator, baseline, uncertainty, and failure cases.
