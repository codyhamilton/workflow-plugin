# Pivot, Consolidate, Focus

Align the workflow skills to one model shared by human and cloud processes: kill the repo-as-backlog, keep plan/execute as separate contracted skills, communicate through authored artifacts (briefs) instead of orchestrator paraphrase, and trim skills to orienting-why.

## Intent

User request, verbatim:

> So then, we strip out our backlog, retain more focused artifacts that rely less on orchestrator translation into subagent prompts, and we peel back some reasoning fluff in the existing skills

> The guide here would be not modal but pivot consolidate and focus.

> Ok do it now.
>
> Now. We are relying on a few hypotheses - some relatively well tested but not in this context. Let’s put our theory somewhere, maybe in the readme (concisely please). A very next step is going to be to run evals that test these very hypotheses, and so I think it’s critical to identify the assumptions that form our approach

Full conversation record: `PROVENANCE.md` in this folder.

## Why This Plan Exists

The plugin is being ported into a staged cloud pipeline: build agents (Claude Code, Codex, human workflows) produce changes and a PR; a cursor automation then reviews, runs computer-use QA, and babysits the PR to merge-ready. The plan artifact becomes the pipeline's backbone — it determines intent, anchors review outcomes, and derives the QA plan.

Working through that port exposed that much of the current structure is a shadow work-tracking system (`[NEW]-` prefixes, renumbering, ROADMAP sync, parent-program taxonomy) that exists for a backlog mental model the pipeline makes obsolete — PRs and the tracker already carry status. Meanwhile iterate's tested findings (briefs beat orchestrator paraphrase; a plan not built has value) point at what the skills should focus on instead.

This is deliberately **not** a modal human/cloud split. Both processes align to one model; the only irreducible difference is whether someone is standing at the plan→execute seam to hold the checkpoint.

## Scope

Revise the plan, execute, and comprehensive-review skills around the new model; define the PR artifact seam and artifact taxonomy as explicit contracts; partition the plugin into a cloud-safe core and a local lab; relocate persuading-why commentary to per-skill references; document the operating hypotheses in the README; build and run evals that test those hypotheses.

## The Model (decisions already made)

These were settled in the plan conversation and are not open for re-litigation during execution:

1. **Plan and execute stay separate skills.** A dedicated planning context has absolute focus on plan quality; joined workflows make the plan a stop on the way to the build, with an accuracy cost. Separation preserves gating, plan validation, adversarial planning, and iterate's plan-without-build. Cloud one-shots are *sequential composition* of the two skills within one run (the pattern iterate already uses), never fusion.
2. **The backlog dies.** A plan folder on a branch means "being built or was built" — nothing else. Status lives in the PR and the tracker. The `[NEW]-` prefix, numeric renumbering ceremony, parent-program taxonomy, and ROADMAP-as-canonical-schedule are removed. Deferred work persists as a design-intent doc or a tracker issue, not a stale plan folder. Exploratory/adversarial plans live with their exercise's provenance (iterate folders, branches).
3. **Artifact taxonomy.** Durable artifacts carry *intent and outcome* (PLAN.md, DESIGN.md when warranted, IMPLEMENTATION.md, REVIEW.md, QA.md). Run-scoped artifacts carry *coordination* (briefs). Nothing carries status.
4. **Briefs invariant, plugin-wide.** Context authors write once, in full, addressed to the consumer; orchestrators route verbatim, never paraphrase. Execute dispatches workers with briefs derived from plan contracts; review writes findings as remediation briefs the fixing agent consumes untranslated. (Empirical basis: iterate showed large gains in subagent prompt quality on long-context jobs and in review remediation accuracy.)
5. **Checkpoint at the seam.** The plan phase ends at a holdable checkpoint: held when a human is present and stakes warrant it, waved through in headless runs. One workflow shape; the gate is held or waived, not two processes.
6. **Orienting-why stays, persuading-why moves.** Keep rationale that changes agent behavior in unspecified situations (failure-mode lists, one-line invariant rationale, artifact consumers). Relocate rationale that argues the design's correctness to a per-skill `reference.md`. Test: if the agent already trusted the rule, would this sentence change what it does?
7. **Cold-reader pressure transfers to review.** With composition in one run, the downstream review stage is the cold reader that keeps plans honest — its remit includes judging whether the plan was sufficient to determine intent, place findings, and derive QA.

## Architectural Implications

- `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` of this repo describe the four-skill structure and the provenance model; both need updating after the skill revisions (component map, cross-skill contracts, invariants — e.g. invariant 3's ROADMAP references).
- The plan skill's folder-taxonomy rules (~40% of its Rules section) are removed; `docs/plans/01-workflow-improvements/` remains as historical provenance and is not migrated.
- The setup skill stops creating `docs/ROADMAP.md` as a canonical schedule.
- `marketplace.json` grows a second plugin entry: core (plan, execute, comprehensive-review) vs lab (setup, iterate, transcript-parser, workflow-tuning).
- iterate re-composes over the revised skills; its briefs pattern is promoted to the plugin-wide invariant rather than remaining iterate-internal.
- An external consumer appears: the cursor automation reads/writes the plan folder on PR branches. The seam contract in `DESIGN.md` is the interface it codes against.

## Intent Validation

- Modal vs unified: user rejected the modal split — "not modal but pivot consolidate and focus."
- Fusion vs separation: user retained separate plan/execute after weighing the focus-loss and gating arguments; composition happens at run level.
- Briefs: user adopted them explicitly as "an interesting approach to test" — hence evals, not just assertion.
- Why-trimming: user confirmed skills "still have too much commentary" but intent grounding stays because an agent that knows why "can fill the gaps you don't specify a little better."
- Hypotheses placement: user chose the README, concise.

## Assumptions (headless decisions, challengeable at review)

- Core plugin keeps the name `workflow`; the local set ships as a second plugin (working name `workflow-lab`). Naming is cosmetic and cheap to change.
- Briefs are committed to the plan folder (they are provenance and debugging truth, and cost nothing), not just review-remediation briefs.
- `comprehensive-review` remains the skill name despite its pipeline refocus.
- The QA.md artifact shape is defined by the seam contract but the computer-use QA skill itself is out of scope here (it lives with the cursor automation).

## Open Questions

- Which harness hosts the cursor automation's orchestrated workflow, and does it install this plugin's core skills directly or carry its own prompts that honor the seam contract? (Affects Phase 5 packaging detail, not the contract itself.)
- Eval harness capacity: full plan+execute runs per scenario are expensive; how many scenarios per hypothesis are enough for signal? (Resolve inside Phase 1; the existing evals/README variance guidance applies.)

## Execution Phases

Each phase is a separately executable slice producing its own PR.

1. **Hypothesis evals.** Build eval scenarios targeting the testable hypotheses (H2 briefed vs prose dispatch; H3 separate-plan vs fused plan-build; H5 orienting-why vs bare-rules vs full-commentary skill variants) using the existing `workflow-tuning` eval capability. Establish baselines with the current skills before any revision lands. Output: scenarios in `evals/scenarios/`, baseline + candidate results, a findings note per hypothesis.
2. **Plan skill revision.** Strip folder taxonomy and ROADMAP rules; restructure the accreted step numbering into named phases; add the headless posture (assumption ledger in place of blocking Q&A, presented at the checkpoint when a human is present); make acceptance criteria QA-drivable (entry point → action → observable result for user-facing criteria); fold provenance into PLAN.md for one-shot runs; move persuading-why to `reference.md`.
3. **Execute skill revision.** Brief-based worker dispatch (author-once, route-verbatim); progressive IMPLEMENTATION.md during execution (crash-resumable branches); review posture parameter (full independent review when terminal, pre-flight when a downstream review stage exists); delegation conditional on harness capability and context economics; session-ID capture and model tables moved out of the skill body into reference/config files.
4. **Comprehensive-review revision.** Explicit inputs (plan folder, diff, assumption ledger); outputs placed in the plan folder keyed to acceptance criteria (REVIEW.md + per-finding remediation briefs); an intent/assumptions lens; the plan-sufficiency judgment feeding workflow-tuning; the no-artifact fallback (reconstruct intent from PR, issue, commits into a recovered-intent note).
5. **Partition and re-composition.** Second plugin manifest (core vs lab); iterate re-composed over revised skills with its Reasoning section moved to `reference.md`; setup slimmed (no canonical ROADMAP); transcript-parser's inline script moved to a `scripts/` file; stable docs (`docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, README) updated to the new model.

Phase 1 precedes 2–4 because the revisions are bets on the hypotheses; where an eval needs a candidate variant (briefed dispatch), the variant is built as an eval candidate inside Phase 1, not merged first. Phases 2–4 may be re-scoped by Phase 1 findings — that is the point of running it first. Phase 5 depends on 2–4.

## Acceptance Criteria

- README carries a concise operating-hypotheses section; each hypothesis states its empirical status and is individually testable by an eval.
- `evals/scenarios/` contains at least one scenario per testable hypothesis, with baseline results recorded before skill revisions merge; each hypothesis has a written findings note.
- Grepping the revised plan and execute skills for `[NEW]-`, renumbering, and ROADMAP-sync rules returns nothing; the plan skill's Rules section no longer contains folder-status taxonomy.
- A headless plan run (no user available) produces a PLAN.md containing a populated assumption ledger instead of stalling on questions.
- Execute, run against a plan, dispatches workers with committed briefs and writes IMPLEMENTATION.md progressively (verifiable mid-run on the branch).
- Comprehensive-review, run against a PR branch with a plan folder, writes REVIEW.md and remediation briefs into that folder keyed to the plan's acceptance criteria; run against a PR with no plan folder, it produces a recovered-intent note and still completes.
- The marketplace exposes two plugins; installing the core plugin yields exactly plan, execute, comprehensive-review.
- Each revised skill's SKILL.md retains its failure-mode preamble; design-justification prose lives in `reference.md` files.

## Provenance Notes

See `PROVENANCE.md` for the verbatim conversation record.

- This folder deliberately uses the convention it defines: plain numbered folder, no `[NEW]-` prefix, no status in the name — the PR carries status. It doubles as the first dogfood of decision 2.
- The strongest-held constraint from the conversation: verbatim intent capture and the assumption ledger are the signal; the taxonomy was the noise. Everything downstream (review placement, QA derivation, merge-readiness) keys off intent fidelity.
