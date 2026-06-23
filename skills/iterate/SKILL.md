---
name: iterate
description: Drive long-horizon work whose success criteria are not knowable up front, by building divergent candidate solutions on separate branches, judging them against criteria the builds reveal, reconciling a winner, then extrapolating the next step. Use when the user has a broad goal but no fixed spec, when a naive loop ("keep trying until X") is failing because X is not yet known, or when they ask to explore alternative implementations before committing.
---

# Iterate

Use this skill for long-horizon work where you do not have perfect future knowledge: you know roughly what you need, but you cannot write the success checklist ahead of time. The criteria that matter are discovered by building, looking, and assessing — not specified in advance.

This is a layered, sequential variant of best-of-n. It is not parallel sampling. Each candidate is built *after* the previous one and uses the previous builds as a functional spec, with a remit to find a materially different solution. It exploits a property of LLMs that pure looping ignores: existing code is the cheapest, most precise technical spec available, and a divergent rebuild against that spec is easier and better than blind incremental refinement of a single line.

## Why This Exists

The default approach to open-ended work is a loop: keep trying until you meet a measurable outcome X. This fails precisely when the spec is not known ahead of time. The analogy: you know you need a car, but you do not know all the criteria up front. You only have a broad sense of what matters. You have to get in a car and drive it before you can assess the things that actually count.

This skill exists to prevent the failures that pure looping and naive best-of-n produce:

- Optimizing hard against a measurable target X that turns out to be the wrong target, because the real criteria only became visible after something was built.
- Treating the first working implementation as the answer, when it was really just the first reification of a still-forming cognitive model.
- Incrementally refining a single implementation — which is hard — instead of using it as a spec to shape a cleaner alternative — which is easier.
- Best-of-n parallelism producing N near-identical samples that explore no real design space, because none of them could see the others.
- Building challengers that differ cosmetically rather than in approach, adding cost without adding information.
- Judging candidates against a checklist invented up front, missing the criteria the builds themselves surfaced.
- Throwing away the losing branches, destroying the reified alternatives that are the most valuable provenance of the whole exercise.
- Running the loop forever instead of stopping when enough has been learned to commit.

## Working Model

This mirrors how developers actually build large things. For any work too big to hold in your head, you do not design it perfectly in your head and then type it. You put a first version on paper — or in code — to reify your cognitive model, and then you challenge it *there*, against something concrete, not against your imagination. The initial build is not the deliverable; it is the instrument that makes the real requirements visible.

So the unit of work here is not "an implementation." It is a **cycle**: build a naive solution, build one or two challengers that diverge from it on purpose, judge the set against the criteria that emerged, reconcile a winner while keeping the challengers, then extrapolate what to build next. Each stage composes the existing skills in this plugin — `plan`, `execute`, `comprehensive-review` — rather than reinventing them.

Two ideas carry the whole skill:

- **Prior builds are the functional spec.** A challenger is not told "do something different" in the abstract. It is given the previous build(s) as a working contract and told to find a genuinely different approach to the same goal, using the lessons those builds made legible. If it cannot articulate a distinct design thesis, it is not built — a cosmetic variant adds cost and no information.
- **The criteria are discovered, not declared.** Judgement does not score candidates against a checklist written before anything existed. It reads the built candidates and surfaces the criteria *they* revealed to matter, then selects against those. This is the "get in the car and assess" step made concrete.

### The divergence bar

This is the load-bearing gate of the whole skill, and it works against the grain of how agents behave. Asked to "find a materially different approach," an agent will *always* return one and rationalize it, because it treats the request as a thing to satisfy rather than a hypothesis to test. A gate phrased as "build a challenger unless you can't think of one" therefore never stops. Two moves give it teeth: invert the default, and split generation from acceptance.

- **The default is no further candidate.** The burden of proof is on building a challenger, not on stopping.

- **The proposer gets breadth; the gate holds the tests.** These two needs are in tension, and that is exactly why they go to different agents. The proposer needs wide license — otherwise challenge collapses into local tweaks — so tell it plainly that it may challenge the entire conception: the structure, the outward surface, even the problem statement itself. But do **not** hand the proposer the acceptance tests below as a target. If the generator holds the tests, it games them — reframing a problem that was fine just to clear a bar. Criteria given to a generator become a target; criteria given to a filter stay a filter. Breadth to the proposer; the tests live with the approver (the orchestrator or a clean, separate check), never the agent that wants to build.

- **What counts as real divergence.** The gate accepts a thesis only if it clears at least one of these — not all need hold:
  1. *It is not a safe union with the base.* If the thesis is merely a subset or improvement that could be folded into the base by reconciliation, it is not a fork. Do not build it — queue the idea for the reconcile step and move on. Changing the wheels is not a different car.
  2. *It changes the outer surface.* It presents a different solution outward — a different theory of how the thing is used — not just a different internal mechanism behind the same surface. A ute is a meaningfully different vehicle from a car.
  3. *It reframes the problem.* It challenges the problem statement itself, not only the solution. Deciding the user actually needed a boat is a legitimate and novel thesis.

  These tests are necessary, not sufficient: clearing the bar only earns a candidate the right to be *built*. It still has to win judgement. An illegitimate wide swing — a boat no one needed — passes divergence but loses at step 4, so the two gates catch two different failures.

- **Convergence is success, not failure.** "I cannot find a thesis that clears the bar" is the expected, valid, and frequently correct answer — and is itself the signal that this layer of exploration is exhausted. You have iterated successfully *when you can no longer produce a genuine fork*. Never manufacture one to satisfy the request.

### What judgement is — and is not

Judgement is not code review. Each candidate already received code-level review inside its `execute` pass (correctness, contracts, failure modes). Re-running that misses the point. Cross-candidate judgement is a higher-altitude, different activity:

- **The question is which approach is the better foundation to keep building on** — not which implementation is most polished. A rough implementation of a superior approach should beat a polished implementation of a dead-end one, because the reconcile step fixes roughness but cannot fix a bad foundation.
- **Operate at design altitude.** Compare the shape of the core abstractions, the boundaries, the one-way doors and lock-in, the long-term cost, and the headroom each approach leaves for the extrapolated next steps. Ignore incidental defects — they belong to `execute`, not here — *unless* a defect is intrinsic to the approach and reveals it cannot work.
- **Judge against the emergent criteria**, the spec the builds revealed, not a checklist invented up front.
- **The null result is valid and common.** The naive candidate winning, or the candidates being effectively equivalent (then pick the simplest), are legitimate outcomes. Do not invent a winner's superiority because a selection was requested.
- **Emit a harvest list.** Judgement's output is not just a winner. It names the best ideas from the *non-winning* candidates that are worth pulling into the reconciliation. That list is the direct input to the reconcile step.

### Branch isolation

Each candidate is built on its own git branch off a shared base commit, so the candidates are directly comparable. Builds are sequential, so separate branches are sufficient — no worktrees are needed; just check out the base commit and branch for each candidate. Do not build challengers by mutating the previous build in place — that destroys the spec. Keep every candidate branch intact through judgement and reconciliation. Losing branches are not deleted; they are the reified alternatives and the most valuable provenance the cycle produces.

## Loop Control

The user defines depth and gating when they invoke the skill. Honor what they ask for. In the absence of explicit instruction:

- **Default to gated.** Pause for the user at the two judgement points — the selection gate (which candidate wins) and the next-step gate (which extrapolated step to pursue). These are exactly the points where human judgement supplies what the missing spec cannot.
- **If asked to run autonomously, cap at 2 cycles by default** — the current scope, plus one round of its extrapolated next step. Do not run open-ended autonomous loops unless the user explicitly sets a larger depth or a stop condition. Surface the state and stop.

## Workflow

A cycle is steps 2–6. Step 7 starts the next cycle.

1. **Capture scope and broad goal.** Take the user's broad goal verbatim. Do not pressure them for a success checklist — the absence of one is the reason this skill exists. Establish a parent program folder under `docs/plans/[NEW]-<goal>/` (see the `plan` skill for the program/child-plan convention) and record the goal and the loop-control choice (gated vs autonomous, depth) there. Capture the base commit the cycle branches from.

2. **Build the naive implementation (candidate 1).** Run a normal `plan` → `execute` pass for a straightforward, honest first solution to the goal. This is candidate 1. It is allowed to be naive; its job is to reify the cognitive model and become the spec for what follows. It carries the internal review that `execute` already mandates.

3. **Build 1–2 divergent challengers, sequentially.** For each challenger:
   - Check out the same base commit and create a fresh branch off it.
   - Give the challenger the prior candidate(s) as a functional spec — the actual code, not a prose summary — and a remit with deliberately wide license: *solve the same goal with a materially different approach, and you may challenge the whole conception — structure, outward surface, even the problem statement.* Do not give the proposer the divergence tests; that license is generative, the tests are not (see "The divergence bar").
   - Apply the **divergence bar** as the approver — the orchestrator, not the proposer. Accept the thesis only if it clears at least one test (changes outer surface, or reframes the problem) and is not a safe union with the base. If it is a safe union, do not build — queue the idea for reconciliation (step 5) and move on. "No thesis clears the bar" is a valid, expected stop: record it and move to judgement.
   - If the thesis clears the bar, build it via `plan` → `execute` on its branch. Candidate 3, if built, sees both candidate 1 and candidate 2.

4. **Judge across candidates.** Run a cross-candidate judgement with a clean agent that authored none of the candidates, reading every branch. This is design-altitude judgement, not code review (see "What judgement is — and is not"): surface the **emergent criteria** the builds revealed, then select the approach that is the better *foundation to keep building on*, not the most polished implementation. The null result — the naive build winning, or an equivalence resolved to the simplest — is valid; do not invent superiority. Record the selection, its design rationale, and the **harvest list** of best ideas from the non-winning candidates for step 5.

5. **Reconcile the winner, keep the challengers.** Run a `plan` → `execute` pass that reconciles the selected candidate onto the main line — working through judgement's harvest list, plus any safe-union ideas queued at step 3 that were never built, pulling in what strengthens the winner. This is where detail and polish happen; judgement picked the direction, reconciliation does the engineering. Do **not** delete or overwrite the challenger branches; they remain as provenance and as the spec for any future divergence. The reconciled state on the main line is the new base.

6. **Extrapolate the next steps.** From the reconciled, built state — not from the original goal — define the **top 3 next steps**: the most valuable things to build next given what now exists. These are derived from current reality, which is why they could not have been written at step 1.

7. **Loop, under the loop-control policy.** At the next-step gate, select one step (user-gated, or auto-selected under an autonomous run within the cap) and re-enter at step 2 with that step as the new scope and the reconciled commit as the new base. Stop when the user's depth or stop condition is reached, when the gates say stop, or when extrapolation produces no step worth building.

## Required Artifacts

Per parent program: the goal, the loop-control policy, and the base commit lineage across cycles.

Per cycle (under `docs/plans/[NEW]-<goal>/iteration-NN/`):

- `CANDIDATES.md` — the candidate registry: each candidate's branch, its divergence thesis (which test it cleared), and a pointer to its plan and execution artifacts. Record the disposition of every pitched thesis: built, rejected for lack of divergence, or queued for reconciliation as a safe union (not built but carried to step 5).
- `JUDGEMENT.md` — the emergent criteria the builds revealed, the per-candidate comparison *at the level of approach*, the selection and its design rationale (or the null result), and the harvest list of ideas from non-winning candidates to carry into reconciliation.
- `NEXT.md` — the top-3 extrapolated next steps and which was chosen (or why the loop stopped).

Each candidate keeps its own `plan` and `execute` artifacts (`PLAN.md`, `IMPLEMENTATION.md`, `REVIEW.md`) on its branch, as those skills already require.

## Rules

- The skill composes `plan`, `execute`, and `comprehensive-review`. Do not reimplement planning, delegation, or review inside it.
- Candidates are sequential, never parallel. Each challenger must see the prior build(s) as a functional spec. That sequencing is the point; it is what makes this more than best-of-n.
- Give challengers real code as the spec, not a paraphrase. Existing code is the most precise technical spec available — that is the property this skill exploits.
- The default is not to build a challenger. Build only when a thesis clears the divergence bar — it changes the outer surface, or reframes the problem, and is not a safe union with the base — and have the approver, not the proposer, decide that. Give the proposer wide license to challenge the whole conception, but never the tests themselves, or it games them. A safe-union idea is queued for reconciliation, not built. "No thesis clears the bar" is a successful, expected outcome and the signal the exploration is exhausted; never manufacture one to comply.
- Build each candidate on its own branch off a shared base commit. Never produce a challenger by mutating a prior candidate in place.
- Never delete losing branches. Reconcile the winner but keep the challengers as provenance and as future spec.
- Judgement is design-altitude comparison of approaches, not code review — pick the better foundation to build on, not the most polished build. A clean agent that authored no candidate runs it. Naming the emergent criteria and emitting the harvest list are required outputs. A null result (naive wins, or a tie to the simplest) is valid.
- Extrapolate next steps from the built state, not from the original goal. The whole reason to loop is that current reality teaches you what the goal could not.
- The user owns loop depth and gating. Default to gated at the selection and next-step decisions. Cap autonomous runs at 2 cycles unless the user sets otherwise.
- Stop when enough has been learned to commit. This skill exists to discover a spec by building, not to loop indefinitely.
