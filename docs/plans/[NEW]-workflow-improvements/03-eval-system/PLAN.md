# 03 — Eval System: Behavior Validation and Variant Testing

## Intent

User request, verbatim (from parent):

> We need an evaluation system for the skills - running plan/execute commands in controlled environments. these should validate behaviours work as expected, output meets expectations and is reliable, and also be able to test different models and variations head to head (variant testing). It will be very difficult to manage reliable changes to the workflows without an eval system to do so. the workflow-tuning skill should be what does this.

## Why This Plan Exists

Without evals, improving skill prompts is guesswork. Changes that seem promising might actually degrade behavior on real scenarios. Evals enable systematic comparison of variants (different models, different prompt versions) against known-good fixtures. This is essential for reliable workflow improvement.

## Scope

Extend `workflow-tuning` with eval capability. The skill will support three modes:
1. **Behavior validation** — Does the skill produce correct output against a known plan?
2. **Reliability testing** — Are results consistent across multiple runs?
3. **Variant testing** — Which model or prompt version performs better?

The eval system uses existing plan folders (PLAN.md + IMPLEMENTATION.md + REVIEW.md) as ground truth fixtures. Results are written to `evals/results/`.

This is user-invoked, not automatic. The user runs `/workflow:workflow-tuning` and asks for an eval.

## Architectural Implications

- **workflow-tuning expansion**: Gains eval modes (behavior validation, reliability, variant testing)
- **New directory**: `evals/` directory at repo root with `scenarios/` and `results/` subdirectories
- **Fixture format**: Existing plan folders serve as fixtures; documented in evals/README.md
- **No change to core workflow**: Evals are meta-layer only; planning/execution/review loop unchanged
- **Dependency on provenance**: Evals use PROVENANCE.md to get verbatim user request (from 01-provenance-capture)

## Intent Validation

**Key decisions:**
- Evals are part of workflow-tuning (not a separate skill) because workflow-tuning is already the meta-layer
- workflow-tuning retains `disable-model-invocation: true` (user-invoked, not auto-triggered)
- Eval fixtures are existing plan folders from target repos that used the workflow
- Eval scenarios can be bootstrapped from real completed plans (no synthetic fixtures needed initially)

## Open Questions

None.

## Execution Phases

1. Create `evals/` directory structure:
   - `evals/README.md` — documents scenario and result folder format
   - `evals/scenarios/` — fixture library (initially empty; populated from real plans)
   - `evals/results/` — eval run results

2. Modify `skills/workflow-tuning/SKILL.md`:
   - Add `## Eval Capability` section describing three eval modes
   - Document the rubric for behavior validation (intent verbatim, scope coverage, architectural implications, acceptance criteria observable, questions discipline, documentation economy)
   - Document reliability mode (run same scenario 3x, check consistency)
   - Document variant mode (side-by-side comparison table)
   - Explain how the agent injects skill prompts into subagents

3. Modify `skills/workflow-tuning/reference.md`:
   - Add `## Eval Patterns` section for recording observed lessons from actual eval runs

4. Test: Create an eval scenario from an existing plan, run behavior validation, verify rubric application and result output

## Acceptance Criteria

- **Eval modes documented**: Three modes (behavior validation, reliability, variant testing) are clearly described in workflow-tuning SKILL.md
- **Fixture format documented**: evals/README.md describes scenario structure (input.md, context.md, ground-truth/) and results structure
- **Rubric defined**: Behavior validation rubric covers intent capture, scope, architectural implications, acceptance criteria quality, questions discipline, documentation economy
- **Injection mechanism**: Skill documents how agents spawn subagents with skill prompts and scenario input
- **Results written**: Eval runs produce comparison tables in evals/results/<scenario>/<timestamp>-<variant>.md
- **Patterns recorded**: evals/reference.md grows with observed lessons from actual eval runs

## Provenance Notes

This is the most complex of the three child plans and depends on both 01 (provenance capture) and 02 (setup skill) being complete. It uses real plan folders from those completed child plans as eval fixtures, demonstrating the end-to-end workflow in action.

Evals are the gateway to reliable workflow improvement. Without them, tuning the workflow is unsafe. With them, every prompt change can be validated against known-good fixtures before deployment.

Initial eval corpus comes from real plan artifacts from the workflow-plugin's own child plans (this parent program), plus any existing plans in target repos using the workflow.
