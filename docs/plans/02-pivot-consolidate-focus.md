# Pivot, Consolidate, Focus

The pivot that gave the plugin its current shape. The repo-as-backlog convention was removed, `plan`
and `execute` stayed separate skills composed at run level, agent-to-agent coordination became
authored briefs routed verbatim instead of orchestrator paraphrase, design-justification prose moved
out of the skill bodies, and the plugin split into a cloud-safe `workflow` core and a local
`workflow-lab`. Four phases, all landed. It did what it set out to do; the model it defined is what
`docs/ARCHITECTURE.md` describes today.

## Intent

User request, verbatim:

> So then, we strip out our backlog, retain more focused artifacts that rely less on orchestrator translation into subagent prompts, and we peel back some reasoning fluff in the existing skills

> The guide here would be not modal but pivot consolidate and focus.

> Ok do it now.
>
> Now. We are relying on a few hypotheses - some relatively well tested but not in this context. Let's put our theory somewhere, maybe in the readme (concisely please). A very next step is going to be to run evals that test these very hypotheses, and so I think it's critical to identify the assumptions that form our approach

## Why This Existed

The plugin was being ported into a staged cloud pipeline: build agents produce a change and a PR, an
automation then reviews it, runs computer-use QA, and babysits it to merge-ready. That made the plan
folder the pipeline's backbone — it determines intent, anchors review outcomes, and derives the QA
plan. Working the port through exposed that much of the existing structure was a shadow work tracker
(`[NEW]-` prefixes, renumbering ceremony, ROADMAP sync, parent-program taxonomy) serving a backlog
mental model the pipeline makes obsolete, since PRs and the issue tracker already carry status.
Deliberately not a modal human/cloud split: both processes align to one model, and the only
irreducible difference is whether someone is standing at the plan→execute seam to hold the
checkpoint.

## What Was Built

Seven decisions settled in the plan conversation became the model, and the four phases implemented
it: the backlog dies and a plan folder on a branch means only "being built or was built"; durable
artifacts carry intent and outcome while run-scoped artifacts carry coordination and nothing carries
status; briefs are a plugin-wide invariant (authored once, in full, addressed to the consumer, routed
verbatim); the seam checkpoint is held or waived, not forked into two processes; orienting-why stays
in skill bodies and persuading-why relocates; and with plan and execute composable in one run, the
downstream review stage becomes the cold reader that keeps plans honest.

**Changed:** `skills/plan/`, `skills/execute/`, `skills/comprehensive-review/` (bodies plus new
`reference.md` files and revised templates), `plugins/workflow-lab/` (new home for setup, iterate,
transcript-parser, workflow-tuning), both plugin manifests and `marketplace.json`, `install.sh`,
`docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `README.md`.

### Phase 1 — plan skill

Restructured from a numbered checklist with accreted insertions into six named phases — Capture,
Ground, Resolve, Write, Challenge, Checkpoint — where only Resolve and Checkpoint branch by posture.
The backlog taxonomy came out entirely. Added: postures (interactive default, headless declared,
never inferred), the plan-folder convention (slug is the unique key, `NN` best-effort only, the
`Workflow-Plan:` marker as the sole mechanical location mechanism), and QA-drivable acceptance
criteria (entry point → action → observable result for user-facing ones). The `PLAN.md` template
gained the Assumption Ledger; `PROVENANCE.md` became interactive-posture-only.

### Phase 2 — execute skill

Gained brief-based dispatch (the invariant stated once, plus mechanics and a ceremony guard),
delegation framed as a judgment call over harness capability and context economics rather than a
mandate, an explicit review-posture section (terminal vs pipeline, declared not inferred), and a
progressively-written `IMPLEMENTATION.md` carrying run identity. Removed: ROADMAP sync, `[NEW]-`
checks, the parent-renaming ceremony, the mandatory-subagent rule, and `STATUS.md` — a status
artifact violates the taxonomy, and progressive `IMPLEMENTATION.md` is the recovery mechanism
instead. Per-harness model tables and session-ID formulas moved to `reference.md`.

### Phase 3 — comprehensive-review skill

Became the pipeline's review stage: explicit inputs (marker-located plan folder, diff, verbatim
intent and assumption ledger), outputs placed in the plan folder keyed to acceptance criteria
(`REVIEW.md`, with structural findings written as self-contained remediation briefs and trivial ones
kept inline), a new intent-and-assumptions lens, a plan-sufficiency judgment flowing one-way to
`workflow-tuning`, and a `RECOVERED-INTENT.md` fallback for PRs with no plan folder.

### Phase 4 — partition and re-composition

Core skills stayed at repo root `skills/`; lab skills moved under `plugins/workflow-lab/` with their
own manifests, and `marketplace.json` began listing both (`workflow` 2.0.0 as a breaking bump,
`workflow-lab` 1.0.0). `iterate` was re-composed over the revised skills with posture declared on
every dispatch; `setup` stopped creating `docs/ROADMAP.md`; `transcript-parser`'s inline Python moved
to `scripts/parse_session.py` (and a pre-existing `OPENCODE` → `OPENCODE_RUN_ID` bug was fixed along
the way); `workflow-tuning` gained the pipeline-outcomes harvest. The stable docs were rewritten for
the two-plugin model, and the README gained the breaking-change callout: repos that adopted the old
folder-status convention get no automated migration.

## Deviations

- **One PR, not one per phase.** The plan specified a PR per phase; the user directed a single
  execution pass, so the phases landed as sequential commits on one branch.
- **Independent review was deliberately skipped at execution time.** The user declared the session
  execution-only and left deep review to the downstream stage. See Review below — this is the
  honest gap in this plan's record.
- **Pipeline posture does not write `REVIEW.md`.** The Phase 2 brief hadn't said where pre-flight
  self-verification results land; the worker resolved it by the seam's ownership contract — the
  pipeline stage owns `REVIEW.md`, so pre-flight results go in `IMPLEMENTATION.md`.
- **The durable contract moved to `docs/ARCHITECTURE.md`.** Since a plan-scoped `DESIGN.md` becomes
  historical after merge, the seam, taxonomy, and posture contracts were written into the stable doc
  instead, and `workflow-tuning`'s citation points there. `DESIGN.md` was therefore not promoted at
  close-out; `docs/ARCHITECTURE.md` supersedes it and the original text remains in history.
- **Hypothesis evals re-scoped out mid-plan.** They became a later, separate effort; the README's
  operating-hypotheses and candidate-variants sections are what this plan leaves behind for it.

## Review

An adversarial **plan-stage** review by a clean subagent judged the plan executable slice-by-slice
and returned twelve findings — one high internal contradiction (the model claimed its decisions were
closed to re-litigation while a phase existed to test them; rewritten so decisions are user-settled
bets and a falsifying result halts and returns to a plan conversation), one high on `NN` collision
under concurrent build agents (resolved by making the slug the unique key and the PR marker the only
location mechanism), and ten medium/low contract and consistency gaps. All twelve were applied
before execution.

No independent review of the **implementation** ran under this plan, by the user's direction. The
code review that did happen came afterwards and out-of-band, in the merge-review PR that followed
(`2439c91`, cleaning up change-relative commentary and inlining load-bearing rationale). This is the
gap that `close-out` and the post-build stage were subsequently built to prevent.

## QA

None. The change is skill and doc prose with no runtime surface, and the pipeline stage that would
have driven QA is the thing this plan was building toward.

## Residual Risks

- The hypotheses this model rests on — briefs beating orchestrator paraphrase, cold-read pressure
  keeping plans honest, orienting-why changing agent behavior — remain untested in this context.
  They are documented in the README as falsifiable lenses precisely because they are bets.
- Two of those hypotheses have no fast feedback loop at all; observational validation only arrives
  once the pipeline has run at volume.
- The breaking-change callout is the only migration path for repos that adopted the old convention
  through this plugin.

## Follow-ups

- The hypothesis eval effort: standing input is the README's operating-hypotheses and
  candidate-variants sections. Never run.
- One open question at plan time — which harness hosts the pipeline automation, and whether it
  installs the core skills or carries its own prompts honoring the seam — was answered by later
  work, in the `post-build` stage and its per-repo adapter model.

## Decisions Worth Keeping

- **Plan and execute stay separate skills.** A dedicated planning context has absolute focus on plan
  quality; a joined workflow makes the plan a stop on the way to the build and pays for it in
  accuracy. Composition happens at run level — sequential dispatch, never fusion, because inlining
  destroys the cold-read pressure the model depends on.
- **Not modal.** The user rejected a human/cloud split outright. One model, one workflow shape; the
  seam checkpoint is held or waived.
- **The taxonomy was the noise; intent fidelity is the signal.** Verbatim capture and the assumption
  ledger are what everything downstream — review placement, QA derivation, merge-readiness — keys
  off.
- **Briefs are committed, not ephemeral.** They cost nothing and they are the provenance and
  debugging truth for what a worker was actually told.
- **The orienting-why test:** if the agent already trusted the rule, would this sentence change what
  it does? If not, it is persuading-why and belongs outside the skill body.
