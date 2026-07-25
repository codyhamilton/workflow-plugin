---
name: iterate
description: Drive long-horizon work whose success criteria are not knowable up front, by building divergent candidate solutions, synthesising, consolidating and hardening, then extrapolating next steps.
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

A **cycle** is steps 2–7; step 8 starts the next cycle. Actors: the *orchestrator* (coordinator,
above), *research subagents*, a *planning subagent* (via `plan`), an *approver subagent* (clean,
applies the divergence bar), a *builder* (via `execute`), a *synthesis subagent* (clean, reads
every candidate and reconceives priorities), and a *hardening reviewer relay* (clean, sequential
passes that verify the consolidated base end-to-end). The orchestrator delegates every substantive
step below, and passes drift-sensitive briefs (`briefs/`) verbatim rather than paraphrasing them.

**Steps 1–4 are divergent — they open options; steps 5–6 are convergent — they close them and bank
the gain into the base the next cycle forks from. The sprint sprints; the consolidation rests and
repairs.**

0. **Capture scope and base.** Record the user's broad goal verbatim — do not pressure them for a
   success checklist; its absence is the reason for this skill. Establish iterate's own plan folder
   at `docs/plans/<NN>-<slug>/` — the same plain convention `plan` and `execute` use elsewhere (no
   `[NEW]-` prefix; the slug is the unique key, `NN` is best-effort ordering only) — and record the
   goal, the loop-control choice (gated vs. autonomous, depth), and the base commit. This folder
   holds iterate's own cross-cycle artifacts (`OUTCOMES.md`, `iteration-NN/`, below); each
   candidate's own `plan`/`execute` artifacts live on its own branch, not here.

1. **Initial research (delegated).** Dispatch 1–3 research subagents to map the problem space, the
   existing code surface, and the constraints. They report raw findings; the orchestrator forwards
   their output verbatim — no synthesis, filtering, or conclusions of its own. Research is not
   planning; step 2 runs a separate planning subagent.

2. **Plan and build candidate 1 (delegated).** A `plan` subagent — dispatched with headless posture
   declared explicitly in its brief, since iterate's own gates (not plan's checkpoint) own user
   interaction — receives the research output and produces the plan; then an `execute` subagent —
   dispatched with terminal review posture declared explicitly — builds it on its own branch off
   the base. The planning and execution are separate subagents — the orchestrator dispatches each
   but does not absorb either role. The candidate is allowed to be naive; its job is to reify the
   model and become the spec for what follows. It carries the independent review terminal posture
   mandates.

3. **Propose and gate challengers (delegated).** For each challenger (up to 1–2), the divergence
   check sits **between `plan` and `execute`** — the plan *is* the proposal, and only a plan that
   clears the bar is built:
   - **Plan = proposal.** Run `plan`, headless posture declared explicitly, against the prior
     build(s) given as *real code, not a prose summary*, dispatched with
     `briefs/challenger-license.md` (the generative license, passed verbatim). The planner is not
     given the divergence tests — criteria given to a generator become a gaming target; criteria
     given to a filter stay a filter.
   - **Evaluate divergence.** A clean approver subagent that did not author the plan applies the
     divergence bar and returns a verdict. Dispatch it with `briefs/divergence-approver.md`,
     passed verbatim.
   - **On pass:** run `execute`, terminal review posture declared explicitly, on that plan on a
     fresh branch off the base. Clearing the bar only earns a build; synthesis still decides. A
     third challenger, if reached, sees both prior builds.
   - **On fail (safe union or no genuine fork):** do **not** build it. The same approver performs
     the **harvest analysis** — extracting the worthwhile ideas from the rejected plan into the
     consolidation queue for step 5 — and the cycle moves on. "No plan clears the bar" is a valid,
     expected stop; record it and go to synthesis.

4. **Synthesize across candidates (delegated).** A clean synthesis subagent that authored no
   candidate does a single deep cross-candidate read and, in this order — yardstick before
   selection, so selection cannot bend the yardstick — dispatched with `briefs/synthesis.md`
   passed verbatim: first revises the
   long-horizon **outcome statement** the builds revealed — the yardstick that did not exist at
   step 0 — into `OUTCOMES.md`; then selects the approach that is the better *foundation to keep
   building on* toward those outcomes; then emits a **harvest list** of the best ideas from
   non-winning candidates, each with a code pointer. It does not plan or build — that is step 5.
   A null result (the naive build winning, or an equivalence resolved to the simplest) is valid.
   **Selection gate:** surface the revised outcomes and the selection rationale to the user (gated
   by default) — this is the moment to confirm or correct the reconceived priorities.

5. **Consolidate onto the winner — capture (delegated).** A `plan` subagent, headless posture
   declared explicitly, receives a **defined scope** — the winner branch, the harvest list with its
   code pointers (plus any safe-union ideas harvested at step 3), and `OUTCOMES.md` as the
   design-altitude reference — and produces a consolidation plan; it does not re-research across
   candidates. Then an `execute` subagent, dispatched with **pipeline** review posture declared
   explicitly (step 6, harden, is the downstream review stage for the consolidated artifact — the
   capture build does not get its own terminal review), builds it, grafting the harvested ideas
   onto the winner. This movement is **additive**: it captures the value the cycle discovered. It
   does **not** yet lock the base — making the integrated artifact actually work is step 6. Keep
   every challenger branch intact.

6. **Harden — verify and lock the base (delegated).** The consolidated artifact is a new thing no
   one has reviewed end-to-end: the multi-branch graft seam is where integration breakage and
   duplication concentrate, and the per-candidate reviews never saw it. Harden is a **bounded relay
   of sequential reviewer passes**, not one review and not parallel reviews — each pass is a clean
   agent that did not build the consolidation, handed the prior passes' findings and the accumulating
   refine plan, and told to push *past* what is already covered. Sequential-with-prior-as-spec is the
   same mechanism that makes candidates more than best-of-n: parallel reviewers mode-collapse onto the
   same obvious subset; a relay diverges by construction. Each pass is dispatched with
   `briefs/hardening-review.md` passed verbatim (parameterised by its focus), running
   `comprehensive-review` against a **deliverable bar**. Within a pass: diagnose its focus to
   completion, then remediate — **denoise trivial fixes inline** (committed, so the next pass reviews
   corrected state) and **append structural items to the shared refine plan** as executable plan work,
   not dot points (the reviewer holds the hottest context, so it authors the fix; a separate `execute`
   still builds it, preserving plan/execute separation). A pass **diagnoses, it does not redesign**,
   and does not relitigate the selection (step 4 owns that); it sorts findings into *must-fix* (blocks
   a sound base) and *next-worth* (valuable but non-blocking). The relay order follows the goal
   dependency:
   - **e2e validation** — actually exercise the built behaviour at the highest fidelity the harness
     supports (drive the app → automated e2e → manual walkthrough → static); record the rung reached.
   - **failure-mode analysis** — edges, resilience, where it breaks (only probeable once it runs).
   - **refine `execute`** — dispatched with **pipeline** review posture declared explicitly (the
     remaining relay passes are the downstream review) — build the accumulated structural must-fix
     plan. Conditional: if no structural item accrued, there is nothing to build, which is a valid
     outcome.
   - **simplify & consolidate (KISS/DRY)** — collapse the duplication the graft introduced, within
     the chosen approach, without over-abstracting. Runs *after* the structural build, because DRY
     targets the final shape and a structural fix often dissolves the duplication it would hand-collapse.
   - **smoke re-check** — confirm the e2e path still runs after all changes.

   The relay is **finite by design** — a fixed focus-differentiated sequence, never "review until
   clean" (that reintroduces the looping this skill exists to prevent). The hardened commit becomes
   the new base.

7. **Extrapolate next steps (delegated).** A subagent examines the **gap between the hardened,
   locked base and `OUTCOMES.md`** — not the original goal — and identifies the **top 3 next
   steps**. Its primary input is the **next-worth findings from step 6**: because the harden review
   actually used the thing, the next steps are read off empirical behaviour, not guessed from a
   design doc. These could not have been written at step 0 because they derive from current reality
   measured against the outcomes the cycle discovered.

8. **Loop control.** **Next-step gate:** surface the top 3 to the user. Select one step (user-gated,
   or auto-selected within the cap on an autonomous run) and re-enter at step 1 with that step as
   the new scope and the hardened commit as the new base. The user owns depth and gating: default
   to **gated** at the selection and next-step decisions; on an autonomous run, **cap at 2 cycles**
   unless the user sets a larger depth or stop condition. Stop when the depth/stop condition is
   reached, the gates say stop, or extrapolation produces no step worth building.

## Model allocation

The goal is **economy**: spend the quality premium only where cognition pays and starve it where the
work is rote. `cache_read` price dominates the bill, so the cheapest cache-read model that still
holds long context goes to the highest-volume role (the orchestrator), and the premium is spent at
the one taste seam (synthesis). The orchestrator sets each Task's `model` from the table below.

This is a **starting allocation, not a settled one.** Giving each class a distinct model is a
near-term convenience — the usage export reports cost per model, not per agent, so distinct models
let us *see* roughly where the cost is landing. Once that's visible we settle on the choices the
numbers actually justify, and classes can collapse onto the same model. The two harnesses differ in
granularity: Cursor has enough model families to give nearly every class its own; Claude Code has
three tiers, so it puts **haiku** at the cheap end (research), **opus** at the taste seam
(synthesis), and everything else on **sonnet**.

| Agent class (step) | Cursor | Claude Code |
| --- | --- | --- |
| Orchestrator | Kimi | sonnet |
| Research (1) | composer-2.5 | haiku |
| Candidate plan/execute (2–3, 5) | composer-2.5 | sonnet |
| Synthesis (4) | sonnet | opus |
| Harden review relay (6) | GLM 5.2 | sonnet |
| Refine `execute` (6) | composer-2.5 | sonnet |
| Extrapolate (7) | GPT5.4 xhigh | sonnet |

`composer-2.5` is the Cursor default and `sonnet` the Claude Code default — any class not named runs
on it. The orchestrator pick is deliberately *not* the absolute cheapest: it wants cheap `cache_read`
**with** strong long-context fidelity (Kimi, not the floor; sonnet, not haiku), because orchestrator
long-context accuracy makes or breaks the run. Synthesis gets the highest-agency model (taste at a
one-way door); extrapolate gets a high-reasoning model (it reads next steps off empirical behaviour).

## Artifacts

An artifact's first job is to be a **forcing function**: requiring it guarantees the activity
happened. The handoff payload is secondary. So **specify the seam, not the substance** — require
only what the consumer must mechanically locate (a branch name, code pointers, N separable
options), mandate qualitative prose elsewhere, and **never** add status/score metadata, which
invites Goodhart gaming (the same reason `plan` warns against forcing a template mechanically).
Every artifact below names a consumer or a gate; one that has neither is ceremony. `briefs/` holds
the verbatim subagent context (see Workflow); it is the input counterpart to these outputs.

Per iterate plan folder (`docs/plans/<NN>-<slug>/`):

- the goal, the loop-control policy, and the base-commit lineage across cycles.
- `OUTCOMES.md` — the **living** outcome statement: what success looks like for the long horizon,
  in qualitative prose, revised by the synthesis agent each cycle (step 4). Consumed by selection
  (step 4), extrapolation (step 6), and the next cycle's synthesis. No metrics tables.

Per cycle, under `docs/plans/<NN>-<slug>/iteration-NN/`:

- `CANDIDATES.md` — the candidate registry: each candidate's branch, its divergence thesis (which
  test it cleared), and pointers to its plan and execution artifacts. Record the disposition the
  approver assigned to every proposed plan: built, or rejected and harvested (the ideas carried to
  step 5). Consumed by synthesis and as provenance. (A registry — structure *is* its content.)
- `JUDGEMENT.md` — consumed by the consolidation planner, whose two seams it must make findable:
  the **winner branch** and the **harvest list with code pointers**. Everything else — the emergent
  criteria, the per-candidate comparison at the level of approach, the design rationale (or the
  null result) — is prose, not a scoring matrix.
- `HARDENING.md` — the **shared, accumulating** record of the harden relay (step 6): each pass
  appends to it and reads its predecessors' entries (the mechanism that stops the relay re-reporting
  the obvious). Three seams it must make findable: the **structural refine plan** (executable
  must-fix work for the refine `execute` to build — plan-shaped, not dot points), a note of the
  **trivial fixes already applied inline**, and the **next-worth list** (non-blocking — the primary
  input to extrapolation). Records which **fidelity rung** the e2e pass reached and one binary — does
  the end-to-end path run (re-confirmed by the smoke pass). Everything else (failure modes,
  simplifications) is prose; no score, no quality rating (the same Goodhart reason as everywhere else).
- `NEXT.md` — the top-3 extrapolated next steps (separable, so one can be chosen), drawn primarily
  from `HARDENING.md`'s next-worth findings, and which was chosen (or why the loop stopped).
  Consumed by loop control and the next-step gate.

Each candidate keeps its own `plan`/`execute` artifacts (`PLAN.md`, `IMPLEMENTATION.md`,
`REVIEW.md`) on its branch, as those skills already require.

## Invariants

- Composes `plan`, `execute`, and `comprehensive-review`; does not reimplement them.
- The orchestrator decides nothing of substance — research, planning, execution, divergence gating,
  and synthesis are all delegated. Drift-sensitive subagent context is passed verbatim from
  `briefs/`, not paraphrased.
- Candidates are sequential, never parallel, and each sees the prior build(s) as real code.
- A challenger is built only when its plan clears the divergence bar, judged by a clean approver,
  not the planner (the burden of proof is on building a challenger, not on stopping — "no genuine
  fork" is a valid, expected answer). A rejected plan is harvested, not built.
- Posture is always declared explicitly when dispatching `plan` or `execute`, never left to default
  inference: `plan` subagents run headless (iterate's gates, not plan's checkpoint, own user
  interaction); `execute` subagents run terminal review posture for candidate builds (steps 2–3) and
  pipeline review posture for the consolidation capture and refine builds (steps 5–6), where harden
  is the downstream review stage.
- The synthesis agent reconceives priorities, selects, and harvests in one cross-candidate read,
  then stops — it does not plan or build. The consolidation planner gets a defined scope from it,
  not a remit to re-research the candidates.
- Consolidation captures (step 5, additive: graft winner + harvest), then **harden** (step 6)
  verifies the integrated base and locks it. Harden is a **bounded, sequential reviewer relay** —
  never parallel (parallel reviewers mode-collapse onto the same obvious subset; sequential passes
  diverge by construction), never "review until clean" — each pass clean (not the consolidation builder),
  handed the prior passes' findings, pushing past them; order follows the goal dependency (e2e →
  failure-mode → structural refine `execute` → KISS/DRY → smoke). A pass diagnoses then remediates:
  trivial inline, structural appended to the refine plan as executable work the separate refine
  `execute` builds. The refine build is conditional on structural findings; a pass diagnoses, it does
  not rearchitect or relitigate the selection.
- Each candidate is built on its own branch off a shared base; losing branches are never deleted.
- Stop when enough has been learned to commit. This skill exists to discover a spec by building,
  not to loop indefinitely.
