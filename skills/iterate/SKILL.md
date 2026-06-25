---
name: iterate
description: Drive long-horizon work whose success criteria are not knowable up front, by building divergent candidate solutions on separate branches, judging them against criteria the builds reveal, consolidating a winner, then extrapolating the next step. Use when the user has a broad goal but no fixed spec, when a naive loop ("keep trying until X") is failing because X is not yet known, or when they ask to explore alternative implementations before committing.
---

# Iterate

## Purpose

Use this skill for long-horizon work where the success criteria cannot be written up front. You
know roughly what you need, but the criteria that actually matter are discovered by building,
looking, and assessing — not specified in advance.

The mechanism is a layered, **sequential** variant of best-of-n — not parallel sampling. Each
candidate is built *after* the previous one and uses the previous builds as its functional spec,
with a remit to find a materially different approach. Existing code is the cheapest, most precise
spec available, so a divergent rebuild against it beats blind refinement of a single line.

This skill prevents the failures that pure looping and naive best-of-n produce:

- Optimizing hard against a target X that turns out to be wrong, because the real criteria only
  became visible after something was built.
- Treating the first working build as the answer, when it was only the first reification of a
  still-forming model.
- Challengers that differ cosmetically rather than in approach — cost without information.
- Judging against a checklist invented up front instead of the criteria the builds surfaced.
- Looping forever, or discarding the losing branches that are the exercise's richest provenance.

**The orchestrator coordinates; it does not decide.** It delegates research, planning, execution,
challenger proposal, divergence gating, and synthesis to subagents. It never plans, implements,
gates, or synthesizes priorities in its own context. Its own actions are limited to: routing work
between subagents, collating their outputs into lean pointers, managing branches and loop control, and
surfacing decisions to the user at the gates. Each stage composes the existing skills in this
plugin — `plan`, `execute`, `comprehensive-review` — rather than reinventing them.

## Workflow

A **cycle** is steps 2–6; step 7 starts the next cycle. Actors: the *orchestrator* (coordinator,
above), *research subagents*, a *planning subagent* (via `plan`), an *approver subagent* (clean,
applies the divergence bar), a *builder* (via `execute`), and a *synthesis subagent* (clean, reads
every candidate and reconceives priorities). The orchestrator delegates every substantive step
below, and passes drift-sensitive briefs (`briefs/`) verbatim rather than paraphrasing them.

0. **Capture scope and base.** Record the user's broad goal verbatim — do not pressure them for a
   success checklist; its absence is the reason for this skill. Establish the parent program folder
   under `docs/plans/[NEW]-<goal>/` (see `plan` for the program/child-plan convention) and record
   the goal, the loop-control choice (gated vs. autonomous, depth), and the base commit.

1. **Initial research (delegated).** Dispatch 1–3 research subagents to map the problem space, the
   existing code surface, and the constraints. They report raw findings; the orchestrator forwards
   their output verbatim — no synthesis, filtering, or conclusions of its own. Research is not
   planning; step 2 runs a separate planning subagent.

2. **Plan and build candidate 1 (delegated).** A `plan` subagent receives the research output and
   produces the plan; then an `execute` subagent builds it on its own branch off the base. The
   planning and execution are separate subagents — the orchestrator dispatches each but does not
   absorb either role. The candidate is allowed to be naive; its job is to reify the model and
   become the spec for what follows. It carries the review `execute` already mandates.

3. **Propose and gate challengers (delegated).** For each challenger (up to 1–2), the divergence
   check sits **between `plan` and `execute`** — the plan *is* the proposal, and only a plan that
   clears the bar is built:
   - **Plan = proposal.** Run `plan` against the prior build(s) given as *real code, not a prose
     summary*, dispatched with `briefs/challenger-license.md` (the generative license, passed
     verbatim). The planner is not given the divergence tests — that license is generative; the
     tests are not (see Reasoning → The divergence bar).
   - **Evaluate divergence.** A clean approver subagent that did not author the plan applies the
     divergence bar and returns a verdict. Dispatch it with `briefs/divergence-approver.md`,
     passed verbatim.
   - **On pass:** run `execute` of that plan on a fresh branch off the base. A third challenger, if
     reached, sees both prior builds.
   - **On fail (safe union or no genuine fork):** do **not** build it. The same approver performs
     the **harvest analysis** — extracting the worthwhile ideas from the rejected plan into the
     consolidation queue for step 5 — and the cycle moves on. "No plan clears the bar" is a valid,
     expected stop; record it and go to synthesis.

4. **Synthesize across candidates (delegated).** A clean synthesis subagent that authored no
   candidate does a single deep cross-candidate read and, in this order (see Reasoning →
   Synthesis), dispatched with `briefs/synthesis.md` passed verbatim: first revises the
   long-horizon **outcome statement** the builds revealed — the yardstick that did not exist at
   step 0 — into `OUTCOMES.md`; then selects the approach that is the better *foundation to keep
   building on* toward those outcomes; then emits a **harvest list** of the best ideas from
   non-winning candidates, each with a code pointer. It does not plan or build — that is step 5.
   A null result (the naive build winning, or an equivalence resolved to the simplest) is valid.
   **Selection gate:** surface the revised outcomes and the selection rationale to the user (gated
   by default) — this is the moment to confirm or correct the reconceived priorities.

5. **Consolidate onto the winner (delegated).** A `plan` subagent receives a **defined scope** —
   the winner branch, the harvest list with its code pointers (plus any safe-union ideas harvested
   at step 3), and `OUTCOMES.md` as acceptance criteria — and produces a consolidation plan; it
   does not re-research across candidates. Then an `execute` subagent builds it, folding in what
   strengthens the winner. This is where detail and polish happen. Keep every challenger branch
   intact. The consolidated commit becomes the new base.

6. **Extrapolate next steps (delegated).** A subagent examines the **gap between the consolidated,
   built state and `OUTCOMES.md`** — not the original goal — and identifies the **top 3 next
   steps**: the most valuable things to build next given what now exists and where it is headed.
   These could not have been written at step 0 because they derive from current reality measured
   against the outcomes the cycle discovered.

7. **Loop control.** **Next-step gate:** surface the top 3 to the user. Select one step (user-gated,
   or auto-selected within the cap on an autonomous run) and re-enter at step 1 with that step as
   the new scope and the consolidated commit as the new base. The user owns depth and gating: default
   to **gated** at the selection and next-step decisions; on an autonomous run, **cap at 2 cycles**
   unless the user sets a larger depth or stop condition. Stop when the depth/stop condition is
   reached, the gates say stop, or extrapolation produces no step worth building.

## Reasoning

The whole skill mirrors how developers build things too big to hold in their heads: you put a first
version in code to reify your model, then challenge it *there*, against something concrete, not
against your imagination. Four ideas carry it.

- **Prior builds are the functional spec.** A challenger is never told to "do something different"
  in the abstract; it is handed the previous build(s) as a working contract and told to find a
  genuinely different approach using the lessons those builds made legible. This is why candidates
  are sequential, never parallel, and why they receive real code rather than a paraphrase — that
  sequencing is what makes this more than best-of-n.

- **The divergence bar** is the load-bearing gate, and it works against the grain of how agents
  behave: asked to "find a materially different approach," an agent will always return one and
  rationalize it. Two moves give the gate teeth. First, **invert the default** — the burden of
  proof is on building a challenger, not on stopping; "I cannot find a genuine fork" is the
  expected, valid, and frequently correct answer, and is itself the signal that this layer of
  exploration is exhausted. Second, **split generation from acceptance** across two agents: the
  planner gets wide license (criteria given to a generator become a target it games — reframing a
  fine problem just to clear a bar), while the clean approver holds the tests (criteria given to a
  filter stay a filter). Clearing the bar only earns the right to be built; the candidate must
  still win synthesis. The three tests and the approver's contract live in
  `briefs/divergence-approver.md`; the generative license in `briefs/challenger-license.md` — the
  split between those two files *is* the split between acceptance and generation.

- **The criteria are discovered, not declared.** Synthesis does not score candidates against a
  checklist written before anything existed. It reads the built candidates and surfaces the
  criteria *they* revealed to matter — refining the long-horizon `OUTCOMES.md` — then selects
  against those. This is the "get in the car and drive it before you can assess what counts" step,
  made concrete; the outcomes are a moving target the cycle sharpens, not a spec fixed at step 0.

- **Synthesis is design-altitude, not code review.** Each candidate already received code-level
  review inside its `execute` pass; re-running that misses the point. The question is which approach
  is the better *foundation to keep building on*, not which implementation is most polished — a
  rough build of a superior approach beats a polished build of a dead end, because consolidation
  fixes roughness but cannot fix a bad foundation. The synthesis agent's full remit and its
  load-bearing output ordering (yardstick before selection, so selection cannot be bent to fit a
  favorite) live in `briefs/synthesis.md`. A null result is valid and common — do not invent a
  winner's superiority because a selection was requested.

**Branch isolation and provenance.** Each candidate lives on its own branch off the shared base, so
the candidates are directly comparable; sequential builds mean separate branches suffice — no
worktrees. Never build a challenger by mutating a prior build in place — that destroys the spec.
Losing branches are never deleted: they are the reified alternatives and the richest provenance the
cycle produces, and the spec for any future divergence.

## Artifacts

An artifact's first job is to be a **forcing function**: requiring it guarantees the activity
happened. The handoff payload is secondary. So **specify the seam, not the substance** — require
only what the consumer must mechanically locate (a branch name, code pointers, N separable
options), mandate qualitative prose elsewhere, and **never** add status/score metadata, which
invites Goodhart gaming (the same reason `plan` warns against forcing a template mechanically).
Every artifact below names a consumer or a gate; one that has neither is ceremony. `briefs/` holds
the verbatim subagent context (see Workflow); it is the input counterpart to these outputs.

Per parent program:

- the goal, the loop-control policy, and the base-commit lineage across cycles.
- `OUTCOMES.md` — the **living** outcome statement: what success looks like for the long horizon,
  in qualitative prose, revised by the synthesis agent each cycle (step 4). Consumed by selection
  (step 4), extrapolation (step 6), and the next cycle's synthesis. No metrics tables.

Per cycle, under `docs/plans/[NEW]-<goal>/iteration-NN/`:

- `CANDIDATES.md` — the candidate registry: each candidate's branch, its divergence thesis (which
  test it cleared), and pointers to its plan and execution artifacts. Record the disposition the
  approver assigned to every proposed plan: built, or rejected and harvested (the ideas carried to
  step 5). Consumed by synthesis and as provenance. (A registry — structure *is* its content.)
- `JUDGEMENT.md` — consumed by the consolidation planner, whose two seams it must make findable:
  the **winner branch** and the **harvest list with code pointers**. Everything else — the emergent
  criteria, the per-candidate comparison at the level of approach, the design rationale (or the
  null result) — is prose, not a scoring matrix.
- `NEXT.md` — the top-3 extrapolated next steps (separable, so one can be chosen) and which was
  chosen (or why the loop stopped). Consumed by loop control and the next-step gate.

Each candidate keeps its own `plan`/`execute` artifacts (`PLAN.md`, `IMPLEMENTATION.md`,
`REVIEW.md`) on its branch, as those skills already require.

## Invariants

- Composes `plan`, `execute`, and `comprehensive-review`; does not reimplement them.
- The orchestrator decides nothing of substance — research, planning, execution, divergence gating,
  and synthesis are all delegated. Drift-sensitive subagent context is passed verbatim from
  `briefs/`, not paraphrased.
- Candidates are sequential, never parallel, and each sees the prior build(s) as real code.
- A challenger is built only when its plan clears the divergence bar, judged by a clean approver,
  not the planner. A rejected plan is harvested, not built.
- The synthesis agent reconceives priorities, selects, and harvests in one cross-candidate read,
  then stops — it does not plan or build. The consolidation planner gets a defined scope from it,
  not a remit to re-research the candidates.
- Each candidate is built on its own branch off a shared base; losing branches are never deleted.
- Stop when enough has been learned to commit. This skill exists to discover a spec by building,
  not to loop indefinitely.
