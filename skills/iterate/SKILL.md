---
name: iterate
description: Drive long-horizon work whose success criteria are not knowable up front, by building divergent candidate solutions on separate branches, judging them against criteria the builds reveal, reconciling a winner, then extrapolating the next step. Use when the user has a broad goal but no fixed spec, when a naive loop ("keep trying until X") is failing because X is not yet known, or when they ask to explore alternative implementations before committing.
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
challenger proposal, divergence gating, and judgement to subagents. It never plans, implements,
gates, or judges in its own context. Its own actions are limited to: routing work between
subagents, synthesizing their outputs into lean pointers, managing branches and loop control, and
surfacing decisions to the user at the gates. Each stage composes the existing skills in this
plugin — `plan`, `execute`, `comprehensive-review` — rather than reinventing them.

## Workflow

A **cycle** is steps 2–6; step 7 starts the next cycle. Actors: the *orchestrator* (coordinator,
above), *research subagents*, a *planning subagent* (via `plan`), an *approver subagent* (clean,
applies the divergence bar), a *builder* (via `execute`), and a *judge subagent*. The orchestrator
delegates every substantive step below.

0. **Capture scope and base.** Record the user's broad goal verbatim — do not pressure them for a
   success checklist; its absence is the reason for this skill. Establish the parent program folder
   under `docs/plans/[NEW]-<goal>/` (see `plan` for the program/child-plan convention) and record
   the goal, the loop-control choice (gated vs. autonomous, depth), and the base commit.

1. **Initial research (delegated).** Dispatch 1–3 research subagents to map the problem space, the
   existing code surface, and the constraints. They report findings; the orchestrator synthesizes
   pointers only and draws no conclusions of its own. This grounds candidate 1's plan.

2. **Build candidate 1 — the naive build (delegated).** Run a `plan` → `execute` pass for a
   straightforward, honest first solution on its own branch off the base. It is allowed to be
   naive; its job is to reify the model and become the spec for what follows. It carries the
   review `execute` already mandates.

3. **Propose and gate challengers (delegated).** For each challenger (up to 1–2), the divergence
   check sits **between `plan` and `execute`** — the plan *is* the proposal, and only a plan that
   clears the bar is built:
   - **Plan = proposal.** Run `plan` against the prior build(s) given as *real code, not a prose
     summary*, with deliberately wide license: *solve the same goal with a materially different
     approach; you may challenge the whole conception — structure, outward surface, even the
     problem statement.* Do not give the planning subagent the divergence tests — that license is
     generative; the tests are not (see Reasoning → The divergence bar).
   - **Evaluate divergence.** A clean approver subagent that did not author the plan applies the
     divergence bar and returns a verdict.
   - **On pass:** run `execute` of that plan on a fresh branch off the base. A third challenger, if
     reached, sees both prior builds.
   - **On fail (safe union or no genuine fork):** do **not** build it. The same approver performs
     the **harvest analysis** — extracting the worthwhile ideas from the rejected plan into the
     reconciliation queue for step 5 — and the cycle moves on. "No plan clears the bar" is a valid,
     expected stop; record it and go to judgement.

4. **Judge across candidates (delegated).** A clean judge subagent that authored no candidate reads
   every branch and runs design-altitude judgement (see Reasoning → Judgement): it surfaces the
   **emergent criteria** the builds revealed, selects the approach that is the better *foundation to
   keep building on*, and emits a **harvest list** of the best ideas from non-winning candidates.
   A null result (the naive build winning, or an equivalence resolved to the simplest) is valid.
   **Selection gate:** surface the selection and rationale to the user (gated by default).

5. **Reconcile the winner (delegated).** Run a `plan` → `execute` pass that folds the judge's
   harvest list — plus any safe-union ideas harvested at step 3 — onto the main line, pulling in
   what strengthens the winner. This is where detail and polish happen. Keep every challenger
   branch intact. The reconciled commit becomes the new base.

6. **Extrapolate next steps (delegated).** From the reconciled, built state — not the original goal
   — define the **top 3 next steps**: the most valuable things to build next given what now exists.
   These could not have been written at step 0 because they derive from current reality.

7. **Loop control.** **Next-step gate:** surface the top 3 to the user. Select one step (user-gated,
   or auto-selected within the cap on an autonomous run) and re-enter at step 1 with that step as
   the new scope and the reconciled commit as the new base. The user owns depth and gating: default
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
  filter stay a filter). The approver accepts a plan only if it clears at least one test, and none
  of these alone is sufficient — clearing the bar only earns the right to be built; the candidate
  must still win judgement:
  1. *It is not a safe union with the base* — not merely a subset or improvement that
     reconciliation could fold in. Changing the wheels is not a different car.
  2. *It changes the outer surface* — a different theory of how the thing is used, not just a
     different internal mechanism behind the same surface. A ute is a different vehicle from a car.
  3. *It reframes the problem* — challenges the problem statement itself. Deciding the user
     actually needed a boat is a legitimate, novel thesis (an illegitimate one — a boat no one
     needed — passes divergence but loses judgement; the two gates catch different failures).

- **The criteria are discovered, not declared.** Judgement does not score candidates against a
  checklist written before anything existed. It reads the built candidates and surfaces the
  criteria *they* revealed to matter, then selects against those — the "get in the car and drive it
  before you can assess what counts" step, made concrete.

- **Judgement is design-altitude, not code review.** Each candidate already received code-level
  review inside its `execute` pass; re-running that misses the point. The question is which approach
  is the better *foundation to keep building on*, not which implementation is most polished — a
  rough build of a superior approach beats a polished build of a dead end, because reconciliation
  fixes roughness but cannot fix a bad foundation. Compare the shape of the core abstractions, the
  one-way doors and lock-in, the long-term cost, and the headroom for the extrapolated next steps;
  ignore incidental defects unless one is intrinsic to the approach. A null result is valid and
  common — do not invent a winner's superiority because a selection was requested.

**Branch isolation and provenance.** Each candidate lives on its own branch off the shared base, so
the candidates are directly comparable; sequential builds mean separate branches suffice — no
worktrees. Never build a challenger by mutating a prior build in place — that destroys the spec.
Losing branches are never deleted: they are the reified alternatives and the richest provenance the
cycle produces, and the spec for any future divergence.

## Artifacts

Per parent program: the goal, the loop-control policy, and the base-commit lineage across cycles.

Per cycle, under `docs/plans/[NEW]-<goal>/iteration-NN/`:

- `CANDIDATES.md` — the candidate registry: each candidate's branch, its divergence thesis (which
  test it cleared), and pointers to its plan and execution artifacts. Record the disposition the
  approver assigned to every proposed plan: built, or rejected and harvested (the ideas carried to
  step 5).
- `JUDGEMENT.md` — the emergent criteria, the per-candidate comparison *at the level of approach*,
  the selection and its design rationale (or the null result), and the harvest list for step 5.
- `NEXT.md` — the top-3 extrapolated next steps and which was chosen (or why the loop stopped).

Each candidate keeps its own `plan`/`execute` artifacts (`PLAN.md`, `IMPLEMENTATION.md`,
`REVIEW.md`) on its branch, as those skills already require.

## Invariants

- Composes `plan`, `execute`, and `comprehensive-review`; does not reimplement them.
- The orchestrator decides nothing of substance — research, planning, execution, divergence gating,
  and judgement are all delegated.
- Candidates are sequential, never parallel, and each sees the prior build(s) as real code.
- A challenger is built only when its plan clears the divergence bar, judged by a clean approver,
  not the planner. A rejected plan is harvested, not built.
- Each candidate is built on its own branch off a shared base; losing branches are never deleted.
- Stop when enough has been learned to commit. This skill exists to discover a spec by building,
  not to loop indefinitely.
