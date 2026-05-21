# 03 — Eval System: Behavior Validation and Variant Testing

## Intent

User request, verbatim (from parent):

> We need an evaluation system for the skills - running plan/execute commands in controlled environments. these should validate behaviours work as expected, output meets expectations and is reliable, and also be able to test different models and variations head to head (variant testing). It will be very difficult to manage reliable changes to the workflows without an eval system to do so. the workflow-tuning skill should be what does this.

## Why This Plan Exists

Without evals, improving skill prompts is guesswork. Changes that seem promising might actually degrade behavior on real scenarios. Evals enable systematic comparison of variants (different models, different prompt versions) against known-good fixtures. This is essential for reliable workflow improvement.

## Scope

Extend `workflow-tuning` with eval capability. An eval is a full end-to-end run of the workflow — plan then execute — on a fixture scenario, compared against a baseline (the current workflow's output on the same scenario) and a reference implementation (a known-good solution).

Evals are not unit tests. There is no absolute pass/fail. The question is: **does a proposed change to the workflow produce meaningfully better outcomes than the baseline, and are those outcomes in the same ballpark as the known reference?**

Two lenses:
1. **Cost** — objective metrics: agents spawned and their sizes, tool use turns per agent, estimated context, wall time. Used to detect regressions (a change that costs significantly more without quality gain) and improvements (same or better quality at lower cost).
2. **Quality** — relative comparison: how close are the candidate's artifacts to the reference implementation? Are there significant regressions or improvements versus baseline? No exact rubrics — judgment is "significant delta?" and "same ballpark as reference?"

Scenarios are real repos cloned at a specific tagged commit, paired with a task and a reference implementation. The reference is a known problem that has already been solved — the expected output shape is understood even if exact output varies. Scenarios are collected over time; the initial corpus can be empty. The pattern must be in place before fixtures are added.

This is user-invoked via `/workflow:workflow-tuning`, run when a workflow change is being proposed and needs validation.

## Architectural Implications

- **workflow-tuning expansion**: Gains eval mode as a sub-workflow
- **New directory**: `evals/` at repo root with `scenarios/` and `results/` subdirectories
- **Scenario format**: each scenario is a folder containing source definition (repo, tag, task) and reference artifacts
- **Results format**: per-run folders with candidate artifacts, cost comparison, and quality comparison against baseline and reference
- **No change to core workflow**: evals are meta-layer only; plan/execute/review loop unchanged
- **Evals are expensive by design**: a full plan+execute cycle per variant; not run continuously, run when validating a proposed change

## Intent Validation

**Key decisions confirmed:**
- Eval unit is plan+execute end-to-end, not planning output alone. Static analysis of plans is disconnected from what the workflow actually does when run.
- Evals measure relative outcomes (candidate vs baseline), not absolute quality against a rubric.
- Scenarios use real repos at tagged commits with known reference implementations, not synthetic fixtures.
- Cost is a first-class lens — agent count, model sizes, tool turns, and context are all captured.
- Quality comparison is intentionally loose: "significant improvement or regression?" and "in the same ballpark as the reference?" No finer-grained rubric needed to start.
- Fixture corpus is built up over time; the eval system ships with the pattern, not the fixtures.

## Open Questions

None.

## Execution Phases

1. Create `evals/` directory structure:
   - `evals/README.md` — scenario format, how to run an eval, how to interpret results
   - `evals/scenarios/` — initially empty; pattern documented in README
   - `evals/results/` — initially empty

2. Document scenario format in `evals/README.md`:
   - `scenarios/<name>/source.md` — repo URL, tagged commit, task description, notes on what the reference implementation achieves
   - `scenarios/<name>/reference/` — artifacts or description of the known-good solution (git diff, prose summary, or IMPLEMENTATION.md from the original solve)
   - `scenarios/<name>/baseline/` — populated on first eval run using the current workflow; becomes the comparison point for future candidate runs

3. Document result format in `evals/README.md`:
   - `results/<scenario>/<timestamp>/candidate/` — all artifacts produced by the candidate workflow run (PLAN.md, IMPLEMENTATION.md, file changes)
   - `results/<scenario>/<timestamp>/cost-comparison.md` — agents spawned + model sizes, tool use turns per agent, context estimates, wall time (baseline vs candidate)
   - `results/<scenario>/<timestamp>/quality-comparison.md` — narrative comparison: candidate vs baseline, candidate vs reference; notes on significant deltas

4. Modify `skills/workflow-tuning/SKILL.md`:
   - Add `## Eval Capability` section explaining the eval model (e2e, relative, two lenses)
   - Document how to set up a scenario (clone repo at tag, write source.md, capture or describe reference)
   - Document how to run an eval: run full plan+execute on the scenario using the candidate skills, capture cost metrics, compare artifacts
   - Document how to populate baseline on first run
   - Document how to interpret results: look for significant cost or quality delta; no fine-grained rubric

5. Modify `skills/workflow-tuning/reference.md`:
   - Add `## Eval Patterns` section for observed lessons from actual eval runs

## Acceptance Criteria

- **Scenario format documented**: source.md schema (repo, tag, task, reference notes), reference/ and baseline/ structure all defined in evals/README.md
- **Cost metrics specified**: agents + sizes, tool use turns, context estimate, wall time — all defined and consistently captured in cost-comparison.md
- **Quality comparison approach specified**: narrative, relative, no exact rubrics — "significant delta vs baseline?" and "same ballpark as reference?" documented as the evaluation frame
- **Eval mode in workflow-tuning**: SKILL.md describes how to set up a scenario, run an eval, populate baseline, and interpret results
- **Results structure**: a completed eval produces cost-comparison.md and quality-comparison.md under results/<scenario>/<timestamp>/
- **Pattern ships without fixtures**: evals/ directory and README are present and complete; scenarios/ and results/ are empty but documented

## Provenance Notes

Evals are the mechanism for safe workflow improvement. Without them, prompt changes are guesswork — even what an LLM predicts about a prompt is disconnected from what it would actually do with it. Running the full plan+execute cycle on known scenarios with reference implementations is the only way to get signal that a change is genuinely better.

The initial fixture corpus will be built from repos where the workflow has already been used and the outcomes are known. Scenarios are reusable: the same fixture can be run against future candidates as the workflow evolves.
