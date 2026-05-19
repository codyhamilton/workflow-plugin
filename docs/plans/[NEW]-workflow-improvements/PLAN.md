# [NEW] Workflow Improvements: Provenance, Setup, and Evals

## Intent

User request, verbatim:

> Consider our workflow skills. This is a simple starting point, but there's a few things we need to add.
> 1. A setup command for the workflow. Initial setup requires ensuring a docs folder is present, and we have our docs for "architecture plus intent". This could be called architecture.md/roadmap.md? consider. Regardless, the setup command has to orchestrate a comprehensive review, look for existing docs, consolidate. It should ask the user if it should do this. If gaps, it should take the user on a guided conversation, asking a series of high level then narrowing questions to come up with architecture and roadmap views, which it documents.
> 2. We need an evaluation system for the skills - running plan/execute commands in controlled environments. these should validate behaviours work as expected, output meets expectations and is reliable, and also be able to test different models and variations head to head (variant testing). It will be very difficult to manage reliable changes to the workflows without an eval system to do so. the workflow-tuning skill should be what does this.
> 3. We need to improve the way we record user intent. We should capture user inputs into a doc as provenance. Specific user inputs (sanitised). These could be pulled from chat transcripts, the harnesses we support all create these. provenance should be exact user inputs (initial/followups/questions responses) along with summary of agent relevant context, e.g. the questions agent asked or a brief of what the agent decided based on that

## Why This Plan Exists

The workflow-plugin works well for structured plan/execute cycles, but has three gaps that hinder reliability and repeatability:

1. **No bootstrap command.** Planning reads `docs/ARCHITECTURE.md` but nothing creates those docs when missing. New repos must muddle through or accept degraded planning.

2. **No eval system.** Improving skill prompts requires comparing variant outputs against known-good fixtures. Without it, workflow-tuning is observational only—no way to validate that prompt changes improve behavior.

3. **Weak provenance.** PLAN.md captures verbatim intent by agent convention, but followup responses, question turns, and decision rationale are not captured. Later intent reconstruction relies on agent memory rather than transcript evidence.

Implementing these three features together increases our ability to tune and improve the workflow itself, and makes the planning process more transparent and reproducible.

## Scope

Three linked child plans that improve the workflow-plugin by adding provenance capture (foundational), setup bootstrapping (enabling stable docs), and evaluation infrastructure (enabling variant testing and prompt improvement).

The implementation is phased: provenance first (smallest scope, foundational), then setup (new skill), then evals (depends on provenance + setup).

This is a parent program. Work is sequenced into three separately executable child plans with clear contracts and completion criteria.

## Architectural Implications

- **Stable docs expansion**: docs/OVERVIEW.md and docs/ARCHITECTURE.md are created for the workflow-plugin itself (not just target repos)
- **Provenance model change**: PLAN.md `## Intent` remains; PROVENANCE.md added alongside for transcript-based capture and conversation record
- **Setup skill addition**: New skill added to the plugin, expanding the four-skill set to five
- **Eval capability addition**: workflow-tuning gains eval modes (behavior validation, reliability, variant testing)
- **Directory structure**: New `evals/` directory at repo root; new `docs/plans/` directory for dogfooding the workflow

These changes do not affect the stable design of the core workflow loop (plan → execute → review). They are additive and enable the workflow to be improved iteratively.

## Intent Validation

The three features are interdependent:
- Provenance is foundational for evals (evals need faithful fixtures with captured intent)
- Setup creates the stable docs that planning reads
- Evals depend on both to produce meaningful comparative data for workflow tuning

**Questions to clarify before finalizing:**

- **Provenance storage**: Should PROVENANCE.md be a separate file alongside PLAN.md (recommended) or a section added to PLAN.md itself? A separate file keeps PLAN.md short and decision-oriented while making transcript evidence available separately.

- **Setup doc naming**: The recommendation is `docs/ARCHITECTURE.md` + `docs/ROADMAP.md`. These are the stable docs planning already reads. Are these the right names and structure, or should they be called something else?

- **Eval execution scope**: Should evals be a standalone mode in workflow-tuning (recommended, as a user-invoked sub-workflow), or a separate skill? workflow-tuning already has `disable-model-invocation: true` marking it as a meta-skill, so evals fit naturally there.

## Open Questions

None at this stage. Implementation details will be refined in child plan conversations.

## Execution Phases

1. **Provenance capture** (child plan 01-provenance-capture)
   - Add PROVENANCE.md template to skills/planning/templates/
   - Modify planning SKILL.md to extract transcript and write provenance
   - Modify PLAN.md template to reference PROVENANCE.md

2. **Setup skill** (child plan 02-setup-skill)
   - Create skills/setup/SKILL.md with full guided workflow
   - Add note to planning SKILL.md suggesting setup when stable docs are absent
   - Verify setup produces compliant ARCHITECTURE.md and ROADMAP.md

3. **Eval system** (child plan 03-eval-system)
   - Add Eval Capability section to workflow-tuning SKILL.md
   - Add Eval Patterns section to workflow-tuning reference.md
   - Create evals/ directory structure and README.md with fixture/results docs

## Acceptance Criteria

**Provenance**: After invoking `/workflow:planning` on any new work, PROVENANCE.md appears in the plan folder with verbatim initial request, conversation turns (if any), and agent decisions. No credentials or large file dumps appear.

**Setup**: On a repo with no `docs/` folder, `/workflow:setup` successfully bootstraps `docs/ARCHITECTURE.md` and `docs/ROADMAP.md` with the specified sections. Subsequent `/workflow:planning` invocation reads those docs without gaps.

**Evals**: With an existing plan folder (PLAN.md + IMPLEMENTATION.md + REVIEW.md), `/workflow:workflow-tuning` can run behavior validation, reliability, and variant testing evals. Results are written to `evals/results/` with comparison tables showing rubric application across variants.

**Overall**: This parent program is completed when all three child plans are executed and reviewed. Completion artifacts are written to the parent folder.

## Provenance Notes

This plan itself dogfoods the workflow. The workflow-plugin uses its own planning, execution, and review processes to improve itself. This serves two purposes:
1. Validates that the workflow can handle self-modification without architectural drift
2. Creates real examples of plan artifacts (PLAN.md, PROVENANCE.md, IMPLEMENTATION.md, REVIEW.md) that can be used as eval fixtures

The child plans are deliberately separated into independently executable slices so that phased execution is feasible across sessions.
