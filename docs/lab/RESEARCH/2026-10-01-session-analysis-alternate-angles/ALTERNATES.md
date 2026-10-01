# Alternate angles — session analysis

**Date:** 2026-10-01 (Brisbane)  
**Status:** draft contrarian note, lab only. **Soft until Cody.**  
**Scope:** no behaviour ship, no live Jev, no hook/plugin/skill changes.  
**Posture:** challenges the progressive-Jev-gate + shape-qual line of research. Argues from in-repo evidence that the main design has structural blind spots worth hedging before WSM commits to a single plan.

---

## Motivation: the current line is stuck, and the stuck-ness may be informative

The progressive Jev session gates pack has run experiments (a) through (f) plus `shape-signal-panel-v1` and produced:

- **One** non-null unanimous gold exit (`ca977b9ca0dd@90`) across **all** labeled workers ([`PANEL-FINDINGS`](../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/PANEL-FINDINGS-20261001.md)).
- **H5 fail** on P0 (α = 0.1189) — the panel does not agree enough to tune against ([`HYPOTHESIS.md`](../2026-10-01-progressive-jev-session-gates/HYPOTHESIS.md)).
- Exhaustion of the maps corpus for ca977 twins: strict shape screen on the remaining 26 T≥75 workers returned **zero** ([`NEXT-EXPERIMENTS`](../2026-10-01-progressive-jev-session-gates/NEXT-EXPERIMENTS.md) §(e)).
- Cross-project screen: **zero** T≥75 candidates in non-maps Ubuntu dirs (§(f)).

The shape-signal pivot shifted measurement from exact-exit unanimity to early-signal/shape agreement. That was the right move — but it is still an LLM-judge-asks-LLM-judge loop, with all the self-referential limits that entails (Zheng et al. position bias; R-Judge models near chance on trajectory judgement; [`LITERATURE.md`](../2026-10-01-progressive-jev-session-gates/LITERATURE.md)).

The `shape-qual-full-maps-v1` expansion to n=34 is inventory work, not a new measurement paradigm. If the underlying problem is that LLM judges **cannot reliably distinguish "long but productive" from "long and stuck"** on hybrid_v0 snapshots alone, running the same judges on more workers will not fix it — it will produce more `unclear` majority votes (5 of 7 workers in the signal panel were majority `unclear`; [`shape-signal-agreement-SUMMARY`](../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md)).

**The question this note asks:** what if the entire approach of "LLM judge on a truncated snapshot at fixed intervals" is not the right primitive? What approaches could WSM hedge with, and what would kill each one?

---

## Alternate A — Purely programmatic predictors of T (no LLM in the loop)

### Thesis

The maps evidence already contains a strong programmatic signal. Worker `92a48e004519` has 6 paths re-read ≥3×, ~60 compaction events, and a sleep/poll pattern — all countable from the JSONL without any model call. Worker `ca977b9ca0dd` has zero Edit/Write, max reread 14, 16 compactions ([`NEXT-EXPERIMENTS`](../2026-10-01-progressive-jev-session-gates/NEXT-EXPERIMENTS.md) §(d)). The thrash-screen's strict shape (no Edit/Write ∧ max reread ≥ 8 ∧ compaction ≥ 8) is already a rule — it just hasn't been evaluated as a **classifier**.

Hypothesis: a logistic regression (or survival model) on a small feature set extracted from `prefix(c)` — compaction rate, re-read density, Edit/Write ratio, tool histogram entropy, assistant-text-chars growth rate, and bash-only streak length — predicts the **binary outcome** "should this worker have been checked out by now?" at least as well as the LLM judge panel on the workers where both are available.

### Feature set (extractable from JSONL with no model call)

| Feature | Source | Why it should matter |
|---------|--------|---------------------|
| `compaction_rate_per_turn` | Count of detectable compaction markers in `prefix(c)` / `c` | High compaction = context churn. `92a48e` has ~60; `bb6165` has 0 |
| `edit_write_ratio` | (Edit + Write tool calls) / (all tool calls) in `prefix(c)` | Zero Edit/Write is the ca977 signature. Productive workers write things |
| `reread_density` | (sum of re-reads ≥ 3) / `distinct_read_paths` | High = circling the same files. Low = exploring new ground |
| `tool_entropy` | Shannon entropy of tool-call histogram in `prefix(c)` | Monotonic Bash/Read = stuck. Diverse tools = building |
| `text_growth_rate` | Δ(assistant_text_chars) / Δ(turns) in a trailing window of 15 turns | Frozen text output (~167 chars) was the ca977 signal |
| `bash_only_streak` | Longest consecutive run of turns whose only tool is Bash | Sleep/poll/wait loops manifest as bash streaks |
| `monitor_wait_density` | Turns matching `sleep|wait|poll|monitor` in bash args / total turns in `prefix(c)` | The sleep/poll class that (d) found unproductive but not runaway |

### Why this might beat the LLM judge

1. **No snapshot truncation loss.** The features integrate over the entire prefix, not a 12k-char window. The hybrid_v0 shrink order can delete the tail, delta, and reread paths before the judge even sees them (TERMS §5 shrink steps 1–4). The programmatic features never lose data.
2. **No model disagreement.** Features are deterministic. There is no Sonnet-stays-`not_yet` problem. The panel's α = 0.1189 is zero-cost to avoid when the classifier is a function.
3. **The thrash-screen already is this.** Experiment (d)'s screen (no Edit/Write ∧ max reread ≥ 8 ∧ compaction ≥ 8) is a hand-crafted feature conjunction. It found the only A0 in the study. The step from "hand-crafted filter" to "fit a model on the same features" is small.
4. **Interpretable.** Every feature maps to a rubric concept (runaway, low progress, drift). A checkout decision can cite "compaction rate 0.20/turn, zero Edit/Write, 167-char plateau" — which is exactly what the shape-signal seats cited for ca977, but without the $2 model call.

### Kill criteria

- **K-A1:** On the n=34 `shape-qual-full-maps-v1` inventory, programmatic features (extracted from hybrid_v0 pack stats, no raw JSONL needed) fail to separate the ca977-class workers from the `unclear`-class at any threshold. Specifically: AUC < 0.70 on the binary task "would ≥2 of 3 shape-signal seats say `early_thrash`?" using leave-one-out cross-validation. If the features can't match the seats, they're not a substitute.
- **K-A2:** Feature extraction on `prefix(75)` — the first checkpoint — requires >5 seconds per worker on the redacted fixtures. If it's expensive to compute, it trades one cost for another.
- **K-A3:** The feature set has no variance on the maps corpus outside the ca977-class (all workers look the same programmatically). This would mean the programmatic signal only works for the one shape the study already found, not for the late-pivot or productive-then-stuck arcs that dominate the corpus.

### Relationship to the main design

Complementary, not competitive. If programmatic predictors identify the "obvious runaways" cheaply, the LLM judge budget can be reserved for the ambiguous cases (the `unclear` majority). This is the economics argument from [`economics-jev-prefilter.md`](../2026-09-30-jev-cheap-judgement-signals/economics-jev-prefilter.md) applied one layer earlier: if deterministic features avoid ~50% of Jev calls while catching the ca977 class, the expensive model call is reserved for the cases where a model actually adds value.

---

## Alternate B — Hierarchical summary tree (local LLM at leaves, frontier at root)

### Thesis

The current design puts a single model (Jev `jev-1.13.0`, or the panel seats) against a truncated snapshot. TERMS §5 acknowledges `recursive_summary` as a future mode but dismisses it as "another model inside the state" that "makes the gold and the instrument depend on a third model" ([`TERMS.md`](../2026-10-01-progressive-jev-session-gates/TERMS.md) §5).

That caution is correct for a **single** recursive summary. But it underweights a **hierarchical** structure: turn-level → segment-level → session-level, where:

- **Leaves:** A small, cheap, local model (Haiku-class or even a fine-tuned small model) summarizes each 15-turn segment into a fixed-schema JSON: tools used, paths touched, progress claim, stall indicators. Cost: negligible. Latency: in-process.
- **Branches:** Consecutive segment summaries are grouped into "arcs" by a simple change-detection heuristic (tool-mix shift, new file surface). Each arc gets a one-line label: "productive build on X," "stalled re-reading Y," "sleep/wait for Z."
- **Root:** The frontier model (Flash, Sonnet, or Jev) sees the arc labels plus the leaf summary of the current segment, plus `brief_anchor`. Total input is bounded by `(number_of_arcs × ~200 chars) + current_leaf + anchor` — well under the 12k guard, with no shrink-order truncation.

### Why this might beat flat hybrid_v0

The hybrid_v0 snapshot is a **recency-biased sample**: it has the tail (last N turns) and cumulative stats, but the middle of the transcript is invisible. Liu et al.'s "lost in the middle" finding is the *motivation* for hybrid_v0, but hybrid_v0's response is to *throw away* the middle rather than *compress* it. The hierarchical approach compresses the middle into arc labels, preserving the session's narrative shape.

The shape-signal seats were asked for "phases contained" and "inflection points" (TERMS §11, §14). Those questions are *about* the arc structure. When the panel majority says `unclear`, it may be because the hybrid_v0 snapshot doesn't carry enough middle-of-session information to identify the inflection. A hierarchical summary that explicitly names arcs and transitions gives the judge the information it needs to answer the question it's being asked.

### Kill criteria

- **K-B1:** On the 7-worker `shape-signal-panel-v1` shortlist, a hierarchical summary (built from hybrid_v0 pack stats as a proxy for real turn-level data) does not improve shape-vote agreement across seats. Specifically: the number of workers with majority `unclear` does not decrease when seats receive arc labels vs. hybrid_v0 stats. If more information doesn't help, the judge is the bottleneck, not the snapshot.
- **K-B2:** The leaf summarizer (Haiku-class) hallucinates arc boundaries or progress claims at a rate >20% on spot-check against raw transcript. If the leaves are unreliable, the tree is worse than no tree.
- **K-B3:** The total cost of the hierarchical pipeline (leaf summaries + arc detection + root call) exceeds 3× the cost of a single hybrid_v0 Jev call per checkpoint. The economics argument from the cheap-Jev paper requires the pre-filter to be cheap; a hierarchical pipeline that costs as much as three flat calls isn't worth the complexity.

---

## Alternate C — Adversarial framing search (find what breaks, then harden)

### Thesis

The current research line optimizes for **agreement** — can multiple models agree on when to checkout? But agreement on the wrong answer is not progress. The shape-signal panel achieved unanimous `early_thrash` on ca977 and `split` / `unclear` on everything else. What if the unanimous answer on ca977 is **easy** (any approach would catch it) and the `unclear` answers reflect **genuine ambiguity** that no framing will resolve?

Instead of searching for a framing that produces agreement, search for framings that **fail** on the known cases. Specifically:

1. **Generate adversarial prompts** that cause ≥2 of 3 seats to say `continue` on `ca977b9ca0dd@90` (the unanimous A0 exit) or `checkout` on `bb6165018de0@150` (the unanimous `not_yet`). These are attacks on the rubric.
2. **Catalogue the failure modes.** Which prompt modifications flip the verdict? Candidates: removing `brief_anchor`, shuffling field order (Wang et al. position bias), replacing structured stats with prose, inflating the tail excerpt length, inserting a plausible-but-false progress claim.
3. **Score brittleness:** what fraction of reasonable prompt perturbations flip the verdict on each worker? If ca977 is robust (hard to flip) and 92a48e is brittle (easy to flip), that gap is a property of the worker, not the framing.

### Why this matters for WSM

The progressive-gate design assumes that **if we find the right framing, the judge will reliably identify runaways**. But the experiments so far show the *opposite*: the framing that works on ca977 (zero Edit/Write, frozen output, compaction-dominated) does not generalize to 92a48e (which has real productive stretches mixed with thrash). If the problem is not "wrong framing" but "genuinely ambiguous trajectory," then no amount of framing search will fix it, and the correct response is to **accept a higher uncertainty** and design the system around it (e.g., ask the user, or use a softer intervention than checkout).

The adversarial search also directly stress-tests the `hybrid_v0` snapshot format. If swapping field order flips verdicts, the snapshot is encoding position bias. If removing `brief_anchor` has no effect on the checkout decision, the brief isn't earning its keep. These are measurements the current pack explicitly deferred (LITERATURE.md: "we have not measured our own conflict rate under order swap") but that should come before scaling to n=34 seats.

### Kill criteria

- **K-C1:** Generating adversarial prompts that flip ≥2 seats on ca977@90 to `continue` requires changes that also flip >50% of the `not_yet` verdicts to `checkout` across other workers. If you can't attack the known positive without also attacking the negatives, the framing is **robust** and this alternate is unnecessary.
- **K-C2:** Fewer than 3 prompt perturbation dimensions (of order-swap, field-removal, prose-rewrite, false-injection, excerpt-length) produce any verdict flip on any worker. If the judge is insensitive to perturbation, brittleness is not the problem.
- **K-C3:** The adversarial search requires >20 model calls per worker per perturbation dimension. If it's too expensive to search the fragility space, the information isn't actionable.

---

## Alternate D — MCP-first TypeSafe from Cursor/Claude (not OpenCode tools)

### Thesis

The current Jev integration path runs through OpenCode hooks (`PostToolBatch`, Claude Code `tool.execute.after`) and the workflow-plugin's own driver ([`assert_phase.py`](../../../tools/driver/assert_phase.py), [`phase_assert.py`](../../../tools/driver/phase_assert.py)). The research pack explored and recommended this path ([`RESEARCH/2026-09-30-opencode-hooks-plugin/`](../2026-09-30-opencode-hooks-plugin/INDEX.md)).

But the dominant harness for this repo's actual users is **Cursor Cloud Agents** (this very environment), and Cloud Agents have a different integration surface: **MCP servers**. The bootstrap script just installed skills via `.cursor/skills/`. The `cursor-cloud` MCP namespace already has `run-info`, `environment-info`, `get-events`. A Jev-as-MCP-tool would:

- Be callable from any Cursor Cloud Agent session, not only from OpenCode/Claude Code.
- Use Cursor's native MCP authentication and secret injection (`TYPESAFE_API_KEY` as a repo-scoped secret).
- Return structured JSON that the agent can act on within its own context, rather than writing to a side-channel JSONL.
- Enable the **agent itself** to request a checkout assessment (pull model, not push from a hook). This inverts the control: instead of a hook that fires at a fixed schedule and the agent doesn't know about, the agent (or WSM) calls `jev-session-checkout` when *it* thinks it might be stuck, or when an orchestrator asks.

### Why this might be better than the hook path

1. **Pull > push for advisory signals.** The progressive-gate design (TERMS §2) fires at a fixed schedule regardless of what the agent is doing. A pull model lets the WSM orchestrator call Jev when it observes a signal (e.g., the programmatic features from Alternate A cross a threshold), rather than on every 15th turn. This naturally implements the "accumulate" path from §12 without a fixed decay schedule.
2. **Cursor is the shipped product.** The OpenCode hooks plugin is a separate npm package that "is not installed in cloud agent environments" (bootstrap output). The workflow-plugin's own lab bootstrap installs core skills, not hooks. An MCP tool is immediately available.
3. **Composability.** An MCP `jev-session-checkout` tool can be composed with other MCP tools (`cursor-cloud-get-events`, `cursor-cloud-run-info`) to build richer context than the hybrid_v0 snapshot alone. The agent can read its own event stream, count its own tool calls, and include that in the Jev state — eliminating the need for a separate snapshot builder.

### Kill criteria

- **K-D1:** Cursor Cloud Agents do not have access to the running agent's own transcript or tool-call history via MCP or any other mechanism. If the agent can't observe itself, the pull model can't work. (Check: does `cursor-cloud-get-events` return tool-call-level data, or only lifecycle events?)
- **K-D2:** TypeSafe's API does not support being wrapped as an MCP tool (e.g., requires a long-lived session, streaming responses, or state that doesn't fit the MCP request/response model). If the API shape is incompatible, this is engineering, not research.
- **K-D3:** The pull model produces strictly fewer checkout assessments than the push model on the known runaway (`92a48e004519`), because no orchestrator or programmatic trigger fires before the fixed schedule would have. If pull is slower to detect, it trades responsiveness for elegance.

---

## Alternate E — Survival analysis with right-censoring (the workers that *didn't* run away)

### Thesis

The entire research line frames the problem as **classification** at each checkpoint: checkout or continue. But the natural statistical framework for "time until an event, where some subjects never experience the event" is **survival analysis** with right-censoring.

Every worker in the maps corpus has:
- A known `T` (total turns).
- A possible event: "the trajectory became unproductive" (the gold exit, if it exists).
- Right-censoring: workers that finished productively have `T` observed but no event.

The current gold-labeling protocol (TERMS §7) treats `gold_exit = null` as an absence of information. But in survival analysis, a censored observation *is* information: it tells you the worker survived to `T` without the event occurring. The Kaplan-Meier estimator, Cox proportional hazards, and accelerated failure time models are designed for exactly this mixture.

### What the survival framing buys

1. **Uses the "boring" workers.** Experiments (c) and (e) produced all-`not_yet` panels. Under the current framing, those workers are useless (they contribute no A0 and no positive-class mass). Under the survival framing, they are *informative right-censored observations*: they tell us that workers with their feature profile survive past their T without deteriorating. A Cox model on the features from Alternate A, fit to the entire maps corpus (not just the ca977-class), estimates the **hazard function**: the instantaneous risk of trajectory deterioration at any turn, conditional on having survived to that turn.
2. **Answers the real question directly.** The design asks "should we checkout at turn c?" The survival model answers "what is the probability of needing checkout in the next `interval` turns, given the features at turn c?" That probability is the natural input to the decision rule — and it naturally incorporates the "accumulate" concept from §12, because the hazard can rise or fall with time and covariates.
3. **Solves the prevalence paradox.** Krippendorff's α = 0.0000 on the expansion panel is the prevalence paradox: when almost all labels are `not_yet`, agreement metrics collapse. Survival models don't have this problem because censored observations contribute to the likelihood through the survival function, not through a binary classification table.
4. **The gold label is simpler.** Instead of asking each judge "should this worker be checked out?" at each prefix (21+ calls per worker per judge), ask: "at what turn, if any, did this worker's trajectory become unproductive?" One call per worker per judge. The event time is the gold label. Censoring is `T` with no event. The survival model is fit once on the corpus, not re-evaluated at every checkpoint.

### Sketch of a Cox model

Covariates (time-varying, extracted at each turn):
- `compaction_rate(t)`, `edit_write_ratio(t)`, `reread_density(t)`, `tool_entropy(t)`, `text_growth_rate(t)`, `bash_only_streak(t)` — the Alternate A features, now as time-varying covariates.

Event: `gold_exit_turn` from the simplified gold protocol (one call per worker per judge: "at what turn did this become unproductive, or null?").

Censoring: `T` for workers with no gold exit.

Baseline hazard: non-parametric (Cox model doesn't assume a distribution).

Output: `h(t | x(t))` — the hazard at turn `t` given the feature vector `x(t)`. Integrate over an interval to get the probability of needing checkout in the next 15 turns. Compare to a threshold for the decision rule.

### Kill criteria

- **K-E1:** The maps corpus (n=34 T≥75 workers) is too small for a time-varying Cox model with 6 covariates. Standard guidance is ~10 events per covariate; with possibly 2–5 gold exits, the model is not identified. **Mitigation:** reduce to 2–3 covariates (compaction rate + edit/write ratio + tool entropy), or use a simpler parametric model (exponential, Weibull). **Hard kill:** if even with 2 covariates and a simplified gold protocol, the concordance index is < 0.60 on leave-one-out CV.
- **K-E2:** The simplified gold protocol ("at what turn did this become unproductive?") produces even worse inter-rater agreement than the current prefix-causal protocol. If judges can't agree on a single event time per worker, the survival labels are noise.
- **K-E3:** The survival model's predicted hazard at `ca977@75` is not in the top quartile of the corpus. If the model can't identify the one known runaway as high-hazard at the first checkpoint, the features don't carry the signal.

---

## What's wrong with claim-counter decay + steer-at-50/60/75

TERMS §12 proposes a **decaying `confidence_min`** across revalidation rounds, with two exit paths: "leap" (high-confidence checkout) and "accumulate" (stacked stop-signals lower the bar). §13 proposes **progressive validation checks** at ~50, 60, and 75 turns, asking whether the agent is "already in validation."

### Problem 1: The decay schedule is ungrounded and unfalsifiable as specified

The decay of `confidence_min` from 3 → 2 (or lower) across rounds is presented as a design intent, not a hypothesis. There is no proposed decay function, no pre-registered schedule, and no measurement that could distinguish "decay was too fast" from "decay was too slow." The §12 text says "harness work; pre-register before any live run" — but there's nothing to pre-register *against*, because the offline sweep uses **fixed** `confidence_min = 3` (TERMS §6, §9).

This is a theory-free parameter: there is no mechanism model that says *why* the bar should decay, *at what rate*, or *in response to what*. The phrase "accumulate stop-signals" implies that repeated low-confidence checkouts should eventually trigger, but the current question set (§6) has no memory across checkpoints — each call is independent. A "stop-signal counter" would need to be built into the snapshot state, which means adding a new field to `hybrid_v0`, which means the gold labels collected so far are not valid for the new snapshot.

**Falsifiable alternative:** instead of decaying the bar, raise the **information** at each checkpoint. The hybrid_v0 snapshot at turn 150 contains more data than at turn 75 (more cumulative stats, more tail). If that additional data doesn't change the verdict, the problem is the snapshot, not the bar. Test: is `checkout_confidence` at turn `c+15` ever higher than at turn `c` on the same worker under the same framing? If not, the "accumulate" concept is fiction — the model is not accumulating evidence, it's repeating itself.

### Problem 2: Steer-at-50/60/75 conflates two different problems

§13 asks "is the agent already in validation?" at turns 50, 60, and 75, and steers differently based on the answer. But:

- **At turn 50, hybrid_v0 cannot fire.** The default schedule starts at `first_at = 75`. Turn 50 is outside the checkpoint grid. §13 proposes these as "progressive validation checks" separate from the §2 schedule, but the pack has no snapshot design, no question set, and no gold protocol for turns before 75. It's a design intent attached to no measurement apparatus.
- **"Already in validation" is not the right question.** Validation (test/fix loops) can be **productive** — the agent fixing real bugs found by real tests. Steering away from validation at turn 50 because "build context decays once the loop is reactive" assumes that all validation is unproductive context decay. But the maps evidence includes workers like `bb6165018de0` (T=154, unanimous `not_yet`, census/monitor wait) where the wait *is* the work. The steer would interrupt legitimate waiting.
- **The steer mechanism doesn't exist.** §13 says "prefer Claude/Cursor hook `additionalContext` (or equivalent parent steer)." But `additionalContext` injection is deferred landing (TERMS §10: "The bytes of a Claude hook response, including `additionalContext`" is out of scope). The steer is a design that depends on a mechanism that is not in the plan to build.

### Problem 3: The 50/60/75 anchors are neither field-validated nor internally validated

The field review ([`docs/analysis/2026-09-08-workflow-vs-field.md`](../../../analysis/2026-09-08-workflow-vs-field.md)) already established that "no published source names these numbers" and "the sweet-spot claim is partial." SWE-agent successes cluster at median 12 steps ([`LITERATURE.md`](../2026-10-01-progressive-jev-session-gates/LITERATURE.md)). The 50–75 band is a cost crossover on cache reads for this repo's model mix, not a quality threshold.

Internally, the maps data has 150 subagents with 24 (16%) over ideal and 8 over 100 turns ([`evidence-maps-claude-5h.md`](../2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md)). The 126 workers under 75 turns are never examined. If a survival model (Alternate E) showed that the hazard function is flat until turn 100 and then rises sharply, the steer-at-50/60/75 checkpoints would be wasted effort. If the hazard rises at turn 30, they're too late.

### Problem 4: Decay + steer assumes the Jev judge works; the evidence says it doesn't yet

The decay schedule (§12) and validation-handoff steer (§13) are designs that sit on top of the progressive-gate primitive. But the progressive-gate primitive has not cleared its own reliability floor: H5 failed, A0 is null on 9 of 10 labeled workers, and the shape-signal agreement is majority `unclear` on 5 of 7 workers. Building a decay schedule on top of a judge that cannot agree with itself is premature optimization of a system that doesn't work.

The honest next step is not "how should we tune the judge?" but "should we keep using this kind of judge at all?" — which is what Alternates A and E propose.

---

## Summary: strongest two alternates for WSM

### Tier 1 — seriously consider

**Alternate A (programmatic predictors)** and **Alternate E (survival analysis)** form a natural pair:

- **A** provides the features. **E** provides the statistical framework.
- Together they answer: "given the programmatic trajectory features at turn `c`, what is the probability this worker needs checkout in the next 15 turns?" — without any LLM judge call.
- The gold label for E can be collected with **one** model call per worker per judge (event time or censored), not 6–16 prefix calls per worker per judge as in the current protocol. This is 5–10× cheaper gold.
- The n=34 corpus *might* be adequate for a 2-covariate survival model, while it is clearly inadequate for the current approach (which needs multiple non-null A0 exits and can't find them).
- Programmatic features are deterministic, so the "agreement" problem vanishes — the only agreement needed is on the gold labels, and the survival framing uses censored observations that the current framing discards.

The programmatic-predictor + survival pair does not replace Jev. It replaces the **cheap layer** that the current design allocates to Jev. The expensive Jev call (or a human review) is reserved for cases where the survival model's predicted hazard is in an ambiguous range — the same economics argument the cheap-Jev paper makes, but with the cheap layer being even cheaper (a function call, not a model call).

### Tier 2 — hedge with

**Alternate C (adversarial framing search):** before scaling shape-qual to n=34 seats (which is expensive), invest 20–30 model calls in perturbation testing the existing verdicts. If the verdicts are brittle to field-order swap or brief-anchor removal, the n=34 expansion will produce noise. If they're robust, proceed with more confidence. This is a small, cheap experiment that de-risks the larger one.

**Alternate B (hierarchical summaries):** worth prototyping if the shape-qual seats continue to produce majority `unclear`. The current snapshot may be the bottleneck, and a richer middle-of-session representation is the obvious thing to try before concluding that LLM judges can't do this task.

**Alternate D (MCP-first):** more of an engineering bet than a research one. Worth pursuing in parallel if the pull model aligns with how WSM actually dispatches work, but it doesn't change the underlying measurement problem.

---

## Amended research-ops advice

1. **Before running shape-qual n=34 seats:** run the adversarial framing search (Alternate C) on the existing 7-worker shortlist. 20–30 calls. If the framings are brittle, fix the snapshot before scaling.
2. **In parallel with shape-qual seats:** extract the Alternate A feature set from hybrid_v0 pack stats (no raw JSONL needed — `cumulative` fields in the packs already carry `tool_histogram`, `reread_paths`, `compaction_event_count`, `assistant_text_chars`). Fit a logistic regression on the 7 shape-signal workers with `early_thrash` vs. `not-early_thrash` as the target. If AUC > 0.80, the feature set is sufficient and the survival model (E) is worth building on the full n=34 corpus.
3. **Change the gold protocol for the survival model:** one call per worker per judge ("at what turn, if any, did the trajectory become unproductive?") instead of 6–16 prefix-causal calls. Collect this alongside the shape-qual seats on the same n=34 workers. Cost: 34 × 3 seats = 102 calls total, vs. 104 pack rows × 3 seats = 312 calls for prefix-causal. Net saving: ~200 calls.
4. **Do not ship decay (§12) or steer (§13) until the survival model has been tried and killed.** If a 2-covariate survival model with concordance > 0.70 provides a probability of needing checkout that is calibrated on the maps corpus, the decay schedule becomes a derived quantity (the hazard function provides it), not a hand-tuned parameter.
