# Workflow Refinement and Close-Out

## Intent

User request, verbatim:

> Lets review and tune our workflow skills. A few things I've noticed:
>  - Plans are consistently being created with [NEW] prefix when they should not anymore.
>  - We should ensure plans are correctly closed off by consolidation - there should be guidance about this, but it perhaps needs to be clearer.
>  - There's a bunch of reference docs inside the skills, which either shouldn't exist, should be in the skill, or should be in the workflow-tuning skill, which is perhaps the right place to hold our workflow design principles
>  - Workflow plans are being created with not quite enough information for a comprehensive run. There's really a few stages to a plan. 1) the initial plan and scoping (what we are doing), which produces design and scope and light phasing. Then that has to be refined in to executable work - typically what I am doing is having another run take the initial plan and break it down into defined executable phases, with each agent having a predefined brief, written as a document containing the agents full input. This provides two optimisations - it means we've ensured we have strongly defined scope for each agent, and that the scope is not needing to be translated by the executing orchestrator - it just passes the briefs. Further it provides traceability for that execution, allowing it to be resumed or adjusted. After execution is complete, it should be collapsed down. We _should_ keep a plan document for traceability -it shows what we did, why (the actual), but not all of the interim docs.
>
> The remit here is to assess our workflow comprehensively and find ways to improve and optimise it. Use also your own judgement and come up with suggestions. Output a plan with what we'd change

## Why This Plan Exists

Four problems, and they are not the same kind of problem.

**The `[NEW]` prefix is not a prompt defect — it is version drift.** The repo removed the backlog
taxonomy in `02-pivot-consolidate-focus`. The *installed* plugin never got that change:
`~/.claude/plugins/installed_plugins.json` pins `workflow@workflow-plugin` to `gitCommitSha
8095d5a` (v1.1.0, last updated 2026-06-26), the commit immediately before the pivot. The live
cache at `~/.claude/plugins/cache/workflow-plugin/workflow/1.1.0/skills/plan/SKILL.md:70` still
instructs `[NEW]-<program>/` for open parent programs, and `~/.claude/plugins/marketplaces/workflow-plugin`
is a clone parked at the same commit. Corroborating evidence, all from the live session:
`workflow:execute` surfaces its pre-pivot description, the four `post-build-*` worker skills are
absent from the registry entirely, and `iterate`/`setup`/`workflow-tuning` still sit in the
`workflow:` namespace rather than `workflow-lab`. `docs/plans/[NEW]-conversation-indexer/` — parent
program, three child plans, a `ROADMAP.md` — is precisely what v1.1.0 mandates and what v2.2.0
forbids. No amount of prompt tuning fixes a prompt that is not loaded.

**Plans are never closed off because no skill owns closing them.** `plan`, `execute`,
`comprehensive-review`, and `post-build` each define what they *write*. Nothing defines what
survives. The result is accretion: `PLAN.md`, `DESIGN.md`, `PROVENANCE.md`, `briefs/`,
`IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`, `briefs/remediation-NN.md` — every one of them durable
by default, all of them still sitting in this repo's own plan folders. The one place consolidation
is described (`iterate` step 5, and `workflow-tuning`'s retro lifecycle) is scoped to those skills
and never generalized. `docs/plans/03-integrate-post-build-stage/` is the visible symptom: a
`PLAN.md` and an `IMPLEMENTATION.md`, no review, no ending.

**Design rationale is duplicated across four `reference.md` files.** The same handful of arguments —
cold-reader pressure, briefs-beat-paraphrase, bounded loops, the generation/acceptance split —
are re-argued in `skills/plan/reference.md`, `skills/execute/reference.md`,
`skills/post-build/reference.md`, and `plugins/workflow-lab/skills/iterate/reference.md`. They are
cross-cutting principles wearing per-skill costumes. Meanwhile the file that should hold them,
`workflow-tuning/reference.md`, has itself rotted: it cites dead `[NEW]-` paths as exemplars,
carries a lesson explicitly marked superseded, points at a "lesson 19" that does not exist, and
trails off into a stranded "Priority 2 / Priority 3" backlog.

**A plan is not yet executable work.** `plan` produces intent, scope, implications, light phasing,
and acceptance criteria. `execute` then derives each worker's brief at dispatch time, from hot
context. That fuses three separable jobs — decomposition, brief authorship, and orchestration —
into one context, and it costs on every axis: the decomposition is never reviewable before build
spend commits; the orchestrator pays to derive what it then routes; a killed run loses every brief
that had not yet been dispatched; and nothing ever tests whether the plan was decomposable at all
until a worker is already running against it. The user's observed practice — a separate run that
turns a plan into defined phases with a complete written brief per agent — is the missing stage,
and the repo already contains the proof it works: `docs/plans/02-pivot-consolidate-focus/briefs/`
holds four briefs of exactly that shape, and the run that consumed them is the cleanest execution
in this repo's history.

## Scope

Add the missing stage and the missing ending: a `refine` skill between `plan` and `execute` that
turns a plan into committed, complete, per-agent briefs and a definitive dispatch order; and a
`close-out` contract that collapses a finished plan folder to a single `PLAN.md` carrying an
appended Outcome section. Consolidate all per-skill design rationale into one principles corpus in
`workflow-tuning` and remove the four `reference.md` files. Fix the install drift that caused the
`[NEW]` regression, and migrate the artifacts it produced.

Out of scope: eval infrastructure (see Open Questions), any change to `post-build`'s SHA-binding,
QA, or checks-gate semantics, and the `conv-index` tool itself.

## Architectural Implications

- **A new core skill.** `refine` joins `plan`, `execute`, `comprehensive-review`, `post-build`, and
  the four dispatch-only workers. The canonical loop becomes plan → refine → execute → review →
  close-out. `docs/OVERVIEW.md`'s "eight skills" framing and `docs/ARCHITECTURE.md`'s component map,
  responsibilities, and data flows all change.
- **Brief authorship moves upstream.** `execute`'s Brief-Based Dispatch stops being an authoring
  responsibility and becomes a routing one whenever `refine` has run. The plugin-wide invariant
  ("context authors write once, in full, addressed to the consumer; orchestrators route verbatim")
  is unchanged — this strengthens it by moving authorship out of the orchestrator entirely.
- **The artifact taxonomy gains a terminal state.** Today every artifact is durable or run-scoped.
  After close-out there are three states: *durable* (`PLAN.md`, and any `DESIGN.md` promoted to
  `docs/design/`), *consumed* (everything else — deleted at close-out, recoverable from branch
  history and the PR), and *promoted* (follow-ups that became tracker issues or design-intent docs).
- **Close-out must land before the candidate SHA in pipeline posture.** `post-build`'s absolute rule
  is that no commit follows the tested commit. Close-out is a commit, so in pipeline posture it runs
  after remediation and QA planning and *before* the required-checks gate captures the candidate SHA.
  In terminal posture `execute` runs it after review settles.
- **Skill directories become runtime-only.** A skill directory holds what an agent loads while
  working: `SKILL.md`, `templates/`, `briefs/`, `scripts/`. Design rationale moves to
  `workflow-tuning`; operator guides move to `docs/`. `skills/post-build/automation.md` relocates
  under this rule.
- **No new metadata anywhere.** No version stamps in artifacts, no status fields, no scores. The
  existing invariant — nothing in the repo carries status — extends to close-out: a closed plan
  folder is not *marked* closed, it simply has an Outcome section and no interim files.

## Intent Validation

Four scope-shaping questions were asked and answered in the planning conversation:

- **What survives close-out?** A single `PLAN.md` with the outcome appended — not a `PLAN.md` +
  `OUTCOME.md` split, and not a light prune that keeps `IMPLEMENTATION.md`/`REVIEW.md`. One file per
  change is the cheapest cold read.
- **Where does refinement live?** A new `refine` skill, not a second phase of `plan` and not a gated
  phase of `execute`. The decomposition wants its own context, its own code recon, and its own gate.
- **What happens to the four `reference.md` files?** Consolidate into `workflow-tuning` as a
  cross-cutting principles corpus; delete the per-skill files.
- **Cleanup scope?** All four items in scope: update the pinned install, migrate
  `[NEW]-conversation-indexer`, trim `docs/ARCHITECTURE.md`, commit and harvest `docs/analysis/` —
  **but no version stamp in `PLAN.md`. "Lets avoid metadata."**

This session's Q&A is captured here rather than in a `PROVENANCE.md`, consistent with the direction
this plan sets: four decisions do not warrant a second file that close-out would delete anyway.

## Open Questions

- **Does `refine` need its own adversarial pass?** `plan` has Challenge. Briefs are where scope
  ambiguity actually bites, so a cold read of the brief set may pay for itself — but it adds a
  dispatch to a stage that must stay cheap. Recommendation: no dedicated pass in v1; `refine`'s
  executability verdict is its own cold read of the plan, and a bad brief surfaces as a worker
  contradiction report. Revisit if contradiction reports are frequent.
- **What to do about `evals/`.** `evals/scenarios/` and `evals/results/` contain only `.gitkeep`,
  and `workflow-tuning` carries ~30 lines of eval procedure that has never run. It is currently
  ceremony. Either land one real scenario or shrink the section to a pointer and let the
  observational harvest carry the load. Not resolved here; flagged for a decision.
- **Which install path is canonical for local use?** Two exist (marketplace plugin cache;
  `install.sh` → `~/.claude/skills/`) and they drift independently — that drift is the root cause of
  problem one. This plan documents both and updates the live one; picking a single canonical local
  path is a follow-on decision.

## Execution Phases

Light phasing — `refine` makes this definitive and authors the briefs.

1. **Unblock the install drift.** Update the pinned plugin from `8095d5a` to current master; verify
   no `[NEW]-` instruction survives in the live skill cache and that `post-build*` and the
   `workflow-lab` partition surface in the registry. Add a README section covering the two install
   paths, how they update, and how to tell which one is live. No version metadata in artifacts.

2. **The `refine` skill.** New core skill and `templates/brief.md`. Defines: the recon pass, the
   decomposition into ordered executable units, the brief anatomy, the dependency and parallelism
   declaration, the executability verdict (proceed, or bounce to `plan` with the contract gaps
   named), and the skip rule that keeps it off single-worker work.

3. **`execute` adapts to consume briefs.** Brief-Based Dispatch becomes routing-first: route
   `refine`'s briefs verbatim when they exist; author inline only for the single-worker case where
   `refine` was skipped. Add per-brief outcome recording and the resume-from-brief-ledger path, and
   the contradiction-amendment rule (a worker's reported contradiction amends the brief file, it is
   never resolved silently). Trim the now-duplicated recon and sizing prose that `refine` owns.

4. **The `close-out` contract.** New dispatch-only worker skill holding the rules once. Wire it into
   `execute` (terminal posture, after review settles) and `post-build` (pipeline posture, after
   remediation and QA planning, before the candidate SHA). Update `templates/PLAN.md` with the
   Outcome section shape.

5. **Reference-doc consolidation.** Author `workflow-tuning/principles.md` as the deduplicated
   cross-cutting corpus; delete the four per-skill `reference.md` files; fold `execute`'s model
   allocation into its skill body and drop its duplicated session-ID formulas (`transcript-parser`
   owns those); relocate `skills/post-build/automation.md` to `docs/automation/post-build.md`;
   repair `workflow-tuning/reference.md`'s rot.

6. **Docs, migration, and dogfooding.** Trim `docs/ARCHITECTURE.md` to seams, contracts, and
   invariants and update it for `refine`/close-out; update `docs/OVERVIEW.md` and `README.md`;
   commit `docs/analysis/` and harvest its lessons into the tuning corpus; migrate
   `[NEW]-conversation-indexer` to the current model; close out
   `docs/plans/03-integrate-post-build-stage/` as the first live application of the new contract.

## Design Notes

The load-bearing shapes, stated once so the briefs can cite rather than restate them.

### `refine`: what it produces

Into the existing plan folder:

- `briefs/NN-<slug>.md` — one per executable unit. `docs/plans/02-pivot-consolidate-focus/briefs/phase-1-plan-skill.md`
  is the reference exemplar; the template generalizes it. Each brief carries: its consumer and agent
  class; owned paths and explicit do-not-touch boundaries; required reading in order; the contract it
  must satisfy, cited from `PLAN.md`/`DESIGN.md` rather than paraphrased; the change spec; done
  evidence as runnable checks; the report-back shape; and the standing instruction to report
  contradictions rather than resolve them.
- `PLAN.md`'s Execution Phases, rewritten from light indicative phasing into the definitive ordered
  dispatch list, each phase naming its brief file and its dependencies. No new file, no dispatch
  table living somewhere a close-out would have to hunt for.

If the plan cannot support briefs — contracts too weak, boundaries undecidable, phases that cannot
be ordered — `refine` does not paper over it. It records the specific gaps in `PLAN.md`'s Open
Questions and returns to `plan`. That bounce is the point: it is a cold read of the plan by a
context that must actually decompose it, and it happens before build spend.

### `refine`: when it runs

It must not become ceremony on small work. Skip it when the change is one bounded slice one worker
can carry — `execute`'s existing ladder rung one — and let `execute` author inline as it does today.
Run it when there are two or more executable units, when workers will run in parallel, when the run
is expected to span sessions or be resumable, or when execution will be dispatched headlessly and no
one will be present to repair a thin brief.

### Close-out: the enabling principle

State it plainly in the skill, because it is what makes an agent willing to delete: **the branch
history and the PR are the archive; the plan folder is the record.** Nothing deleted at close-out is
lost — every brief, every review, every provenance turn remains in the commits that introduced them.
What close-out removes is the obligation on every future reader to sift them.

The steps: append `## Outcome` to `PLAN.md` (what was built, files and modules touched, deviations
from plan wording and why, review verdict and how findings resolved, QA result summary, residual
risks, and where each non-blocking follow-up went); promote `DESIGN.md` to `docs/design/` when it
holds contracts that outlive the change, delete it when it was scaffolding; delete `briefs/`,
`PROVENANCE.md`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`, remediation briefs, and any child plan
folders; commit as one close-out commit.

The guards matter as much as the steps. Never close out while a `blocker` or `high` finding stands.
Never close out unfinished work — `IMPLEMENTATION.md` is the resume path, and deleting it mid-run
destroys exactly the recoverability it exists for. Abandoned work is closed out too, with an Outcome
section that says it was abandoned and why, or by deleting the folder outright; what it must not do
is sit there looking like work in progress forever.

### Principles corpus: what moves

`workflow-tuning/principles.md` holds the arguments that recur across skills, each naming the skills
that instantiate it — cold-reader pressure; posture declared, never inferred; briefs beat paraphrase
and the static-direction/dynamic-context split; the generation/acceptance split (the divergence bar,
`plan`'s Challenge pass, reviewer-versus-verifier); bounded loops; right-sizing by classification;
nothing in the repo carries status; discovery never tie-breaks; the exact-SHA gate; an artifact's
first job is to be a forcing function; orienting-why in the skill, persuading-why out of it. Written
once, cross-referenced, not re-argued per skill.

`workflow-tuning/reference.md` stays the *observed lessons* corpus and gets repaired rather than
rewritten: dead `[NEW]-` exemplar paths corrected, the superseded parent-program lesson retired, the
mangled lesson 18 tail and its dangling lesson-19 reference fixed, the stranded Priority 2/3 backlog
dropped, and lessons already implemented in the skills marked as landed rather than left as open
recommendations.

## Acceptance Criteria

User-facing (entry point → action → observable result):

- Invoke `/workflow:plan` in any repo → the created folder is `docs/plans/<NN>-<slug>/` with no
  bracket prefix, and no `ROADMAP.md` is created.
- Invoke `/workflow:refine` against a plan folder with multi-phase work → `briefs/NN-<slug>.md`
  exists per executable unit, and `PLAN.md`'s Execution Phases names each brief and its dependencies.
- Invoke `/workflow:refine` against a plan whose contracts are too weak to decompose → it does not
  produce briefs; it names the specific gaps in `PLAN.md`'s Open Questions and returns to `plan`.
- Invoke `/workflow:execute` on a refined plan folder → the dispatched worker prompts contain the
  brief routed verbatim plus mechanical pointers only, with no orchestrator restatement of the plan.
- Complete a terminal-posture run through close-out → the plan folder contains `PLAN.md` alone, with
  an `## Outcome` section, and `git log` still reaches every deleted interim artifact.

Non-user-facing (observable statements):

- `grep -rn "\[NEW\]" ~/.claude/plugins/cache/workflow-plugin/` returns no instruction to use the
  prefix, and the live registry lists `post-build` and the four `post-build-*` worker skills.
- `skills/*/reference.md` and `plugins/workflow-lab/skills/iterate/reference.md` no longer exist;
  `plugins/workflow-lab/skills/workflow-tuning/principles.md` does, and no principle in it is
  re-argued inside any `SKILL.md`.
- No file under `skills/` or `plugins/*/skills/` is anything other than `SKILL.md`, a template, a
  brief, or a script; `docs/automation/post-build.md` exists and `skills/post-build/automation.md`
  does not.
- `workflow-tuning/reference.md` contains no `[NEW]-` exemplar paths, no reference to a lesson that
  does not exist, and no stranded priority backlog.
- `docs/plans/03-integrate-post-build-stage/` contains `PLAN.md` alone, with an Outcome section.
- No `[NEW]-` folder remains under `docs/plans/`; the conversation-indexer work is represented by a
  design-intent doc plus a plan folder for the slice actually being built.
- `docs/ARCHITECTURE.md` describes seams, contracts, and invariants without restating each skill's
  behavior, and covers `refine` and close-out.
- No artifact template gains a version, status, or score field.

## Provenance Notes

The `[NEW]` symptom is worth remembering as a class, not an incident: a skills plugin has no
runtime signal that the prompt an agent is executing is not the prompt in the repo. Every
observation about "the skill is doing X" is unreliable until the live copy is checked. The
instinctive fix — stamp a version into the artifacts — was explicitly rejected: metadata in
artifacts is the thing this workflow keeps removing, and the honest fix is to keep one install path
current, not to teach the artifacts to complain.

Moving brief authorship from `execute` to `refine` trades hot context for a reviewable gate. The
briefs get colder — `execute` authors them having just read the code, `refine` authors them having
just done its own recon. That is why `refine` does recon at all, and why the contradiction-amendment
rule matters: a worker that hits a brief-versus-reality mismatch amends the brief, and the amendment
is the traceable record of where the decomposition was wrong.
