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
plugin — `workflow-plan`, `workflow-execute`, `comprehensive-review` — rather than reinventing them.

## Workflow

A **cycle** is steps 2–7; step 8 starts the next cycle. Actors: the *orchestrator* (coordinator,
above), *research subagents*, a *planning subagent* (via `workflow-plan`), an *approver subagent* (clean,
applies the divergence bar), a *builder* (via `workflow-execute`), a *synthesis subagent* (clean, reads
every candidate and reconceives priorities), and a *hardening reviewer relay* (clean, sequential
passes that verify the consolidated base end-to-end). The orchestrator delegates every substantive
step below, and passes drift-sensitive briefs (`briefs/`) verbatim rather than paraphrasing them.

**Steps 1–4 are divergent — they open options; steps 5–6 are convergent — they close them and bank
the gain into the base the next cycle forks from. The sprint sprints; the consolidation rests and
repairs.**

0. **Capture scope and base.** Record the user's broad goal verbatim — do not pressure them for a
   success checklist; its absence is the reason for this skill. Establish the parent program folder
   under `docs/plans/[NEW]-<goal>/` (see `workflow-plan` for the program/child-plan convention) and record
   the goal, the loop-control choice (gated vs. autonomous, depth), and the base commit.

1. **Initial research (delegated).** Dispatch 1–3 research subagents to map the problem space, the
   existing code surface, and the constraints. They report raw findings; the orchestrator forwards
   their output verbatim — no synthesis, filtering, or conclusions of its own. Research is not
   planning; step 2 runs a separate planning subagent.

2. **Plan and build candidate 1 (delegated).** A `workflow-plan` subagent receives the research output and
   produces the plan; then a `workflow-execute` subagent builds it on its own branch off the base. The
   planning and execution are separate subagents — the orchestrator dispatches each but does not
   absorb either role. The candidate is allowed to be naive; its job is to reify the model and
   become the spec for what follows. It carries the review `workflow-execute` already mandates.

3. **Propose and gate challengers (delegated).** For each challenger (up to 1–2), the divergence
   check sits **between `workflow-plan` and `workflow-execute`** — the plan *is* the proposal, and only a plan that
   clears the bar is built:
   - **Plan = proposal.** Run `workflow-plan` against the prior build(s) given as *real code, not a prose
     summary*, dispatched with `briefs/challenger-license.md` (the generative license, passed
     verbatim). The planner is not given the divergence tests — that license is generative; the
     tests are not (see Reasoning → The divergence bar).
   - **Evaluate divergence.** A clean approver subagent that did not author the plan applies the
     divergence bar and returns a verdict. Dispatch it with `briefs/divergence-approver.md`,
     passed verbatim.
   - **On pass:** run `workflow-execute` of that plan on a fresh branch off the base. A third challenger, if
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

5. **Consolidate onto the winner — capture (delegated).** A `workflow-plan` subagent receives a **defined
   scope** — the winner branch, the harvest list with its code pointers (plus any safe-union ideas
   harvested at step 3), and `OUTCOMES.md` as the design-altitude reference — and produces a
   consolidation plan; it does not re-research across candidates. Then a `workflow-execute` subagent builds
   it, grafting the harvested ideas onto the winner. This movement is **additive**: it captures the
   value the cycle discovered. It does **not** yet lock the base — making the integrated artifact
   actually work is step 6. Keep every challenger branch intact.

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
   not dot points (the reviewer holds the hottest context, so it authors the fix; a separate `workflow-execute`
   still builds it, preserving plan/execute separation). A pass **diagnoses, it does not redesign**,
   and does not relitigate the selection (step 4 owns that); it sorts findings into *must-fix* (blocks
   a sound base) and *next-worth* (valuable but non-blocking). The relay order follows the goal
   dependency:
   - **e2e validation** — actually exercise the built behaviour at the highest fidelity the harness
     supports (drive the app → automated e2e → manual walkthrough → static); record the rung reached.
   - **failure-mode analysis** — edges, resilience, where it breaks (only probeable once it runs).
   - **refine `workflow-execute`** — build the accumulated structural must-fix plan. Conditional: if no
     structural item accrued, there is nothing to build, which is a valid outcome.
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
  review inside its `workflow-execute` pass; re-running that misses the point. The question is which approach
  is the better *foundation to keep building on*, not which implementation is most polished — a
  rough build of a superior approach beats a polished build of a dead end, because consolidation
  fixes roughness but cannot fix a bad foundation. The synthesis agent's full remit and its
  load-bearing output ordering (yardstick before selection, so selection cannot be bent to fit a
  favorite) live in `briefs/synthesis.md`. A null result is valid and common — do not invent a
  winner's superiority because a selection was requested.

- **Consolidation is the only convergent phase, so it must verify, not just capture.** Everything
  before it opens options; this is where they close and the gain is banked into the base the next
  cycle forks from. Capture (step 5) is additive — it grafts the winner and the harvest — but the
  grafted whole is a new thing no per-candidate review ever saw, and the multi-branch seam is
  exactly where integration breakage and duplication live. So harden (step 6) is the skill's own
  build→clean-review→repair pattern promoted from the candidate level to the integration level: a
  clean reviewer applies a **deliverable** bar — does it work end-to-end, is it resilient, is it
  free of the graft's duplication — that `OUTCOMES.md`, deliberately design-altitude, does not. The
  bar self-limits: KISS/DRY can only collapse duplication *within* the chosen approach, never
  rearchitect, so the reviewer cannot relitigate selection. A soft base compounds — every later
  sprint builds on it — and the review's findings are also the empirical fuel for extrapolation,
  which is why harden precedes step 7.

- **Harden is a sequential relay, for the same reason candidates are.** Parallel reviewers with
  separate focuses are best-of-n sampling with no divergence pressure: they mode-collapse onto the
  same obvious subset and miss the long tail. Hand each pass the prior passes' findings and tell it
  to push past them, and the reviewers diverge by construction — the *building* thesis (prior as
  spec, find what's different) pointed at *verifying*. Sequential committed passes also buy what
  parallel cannot: no write contention, a refine plan that accumulates safely, and each pass
  reviewing the *corrected* state its predecessors left. The cost is reloading the artifact per pass
  (volume × N) — the same speed-for-coverage trade the skill already accepts for candidates, and
  worth it: N restatements of the obvious is the failure being bought out of. The relay is finite by
  design; "review until clean" is the looping this skill exists to prevent. (The one ordering subtlety:
  DRY runs *after* the structural refine build, because it targets the final shape.)

**Branch isolation and provenance.** Each candidate lives on its own branch off the shared base, so
the candidates are directly comparable; sequential builds mean separate branches suffice — no
worktrees. Never build a challenger by mutating a prior build in place — that destroys the spec.
Losing branches are never deleted: they are the reified alternatives and the richest provenance the
cycle produces, and the spec for any future divergence.

## Model allocation

The goal is **economy**: spend the quality premium only where cognition pays and starve it where the
work is rote. `cache_read` price dominates the bill, so the cheapest cache-read model that still
holds long context goes to the highest-volume role (the orchestrator), and the premium is spent at
the one taste seam (synthesis). The orchestrator sets each Task's `model` from the current harness
table in `protocol/models.yaml` (key `iterate`) — not from hard-coded IDs in this skill.
Resolve that file via `$WORKFLOW_PLUGIN_ROOT/protocol/`, `~/.cursor/plugins/local/workflow/protocol/`,
or `~/{.cursor|.claude|.codex}/skills/_workflow-protocol/`.

That file is the single source of truth for environment-specific model picks. This skill owns the
*roles* (orchestrator, research, synthesis, harden, …); `protocol/models.yaml` owns which model
fills each role in Cursor vs Claude Code vs Codex. Update models there when pricing or quality
shifts; do not edit artifact rules to chase model churn.

This is a **starting allocation, not a settled one.** Giving each class a distinct model is a
near-term convenience — the usage export reports cost per model, not per agent, so distinct models
let us *see* roughly where the cost is landing. Once that's visible we settle on the choices the
numbers actually justify, and classes can collapse onto the same model.

Principles (portable; not model-specific):

- Default each harness to its `defaults:` entry in `protocol/models.yaml` unless a role overrides it.
- Orchestrator wants cheap `cache_read` **with** strong long-context fidelity.
- Synthesis gets the highest-agency model available (taste at a one-way door).
- Extrapolate gets a high-reasoning model (it reads next steps off empirical behaviour).

## Artifacts

An artifact's first job is to be a **forcing function**: requiring it guarantees the activity
happened. The handoff payload is secondary. So **specify the seam, not the substance** — require
only what the consumer must mechanically locate (a branch name, code pointers, N separable
options), mandate qualitative prose elsewhere, and **never** add status/score metadata, which
invites Goodhart gaming (the same reason `workflow-plan` warns against forcing a template mechanically).
Shared plan/execute artifact layout is defined in `protocol/artifacts.md`. Every artifact below names
a consumer or a gate; one that has neither is ceremony. `briefs/` holds
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
- `HARDENING.md` — the **shared, accumulating** record of the harden relay (step 6): each pass
  appends to it and reads its predecessors' entries (the mechanism that stops the relay re-reporting
  the obvious). Three seams it must make findable: the **structural refine plan** (executable
  must-fix work for the refine `workflow-execute` to build — plan-shaped, not dot points), a note of the
  **trivial fixes already applied inline**, and the **next-worth list** (non-blocking — the primary
  input to extrapolation). Records which **fidelity rung** the e2e pass reached and one binary — does
  the end-to-end path run (re-confirmed by the smoke pass). Everything else (failure modes,
  simplifications) is prose; no score, no quality rating (the same Goodhart reason as everywhere else).
- `NEXT.md` — the top-3 extrapolated next steps (separable, so one can be chosen), drawn primarily
  from `HARDENING.md`'s next-worth findings, and which was chosen (or why the loop stopped).
  Consumed by loop control and the next-step gate.

Each candidate keeps its own `workflow-plan`/`workflow-execute` artifacts (`PLAN.md`, `IMPLEMENTATION.md`,
`REVIEW.md`) on its branch, as those skills already require.

## Invariants

- Composes `workflow-plan`, `workflow-execute`, and `comprehensive-review`; does not reimplement them.
- The orchestrator decides nothing of substance — research, planning, execution, divergence gating,
  and synthesis are all delegated. Drift-sensitive subagent context is passed verbatim from
  `briefs/`, not paraphrased.
- Candidates are sequential, never parallel, and each sees the prior build(s) as real code.
- A challenger is built only when its plan clears the divergence bar, judged by a clean approver,
  not the planner. A rejected plan is harvested, not built.
- The synthesis agent reconceives priorities, selects, and harvests in one cross-candidate read,
  then stops — it does not plan or build. The consolidation planner gets a defined scope from it,
  not a remit to re-research the candidates.
- Consolidation captures (step 5, additive: graft winner + harvest), then **harden** (step 6)
  verifies the integrated base and locks it. Harden is a **bounded, sequential reviewer relay** —
  never parallel, never "review until clean" — each pass clean (not the consolidation builder),
  handed the prior passes' findings, pushing past them; order follows the goal dependency (e2e →
  failure-mode → structural refine `workflow-execute` → KISS/DRY → smoke). A pass diagnoses then remediates:
  trivial inline, structural appended to the refine plan as executable work the separate refine
  `workflow-execute` builds. The refine build is conditional on structural findings; a pass diagnoses, it does
  not rearchitect or relitigate the selection.
- Each candidate is built on its own branch off a shared base; losing branches are never deleted.
- Stop when enough has been learned to commit. This skill exists to discover a spec by building,
  not to loop indefinitely.
