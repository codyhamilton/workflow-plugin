---
name: workflow-tuning
description: Captures observed lessons about plan/execute/review workflows, documentation economy, execution cost, phasing, and review posture. Use when refining planning, plan-execution, or review skills; designing workflow evals; or comparing real plan artifacts to decide what workflow improvements are worth making.
---

# Workflow Tuning

## Purpose

Use this skill as a holding place for real-world lessons from plan/execute/review workflows across repos.

It is for improving the workflow itself, not for executing a single implementation task.

## Core Positions

- Optimize for outcome quality per token, not maximal autonomy, context length, or parallelism.
- Prefer the minimum durable documentation set that helps agents reason beyond what the code already shows.
- Keep plans concise and decision-oriented. Plans should explain intent, scope, implications, sequence, and observable success. They should not freeze speculative implementation detail.
- Stable docs earn their keep when they act as concept maps and intent anchors. Free-text paraphrases of code usually do not.
- Plan-scoped `DESIGN.md` is not mandatory. It is most valuable when it reifies target shape or cross-implementor contracts inside the scope of the change.
- Phased execution is the default. End-to-end execution is an explicit cost/quality trade.
- Review should be focused, right-sized, and usually capped at one external review loop before self-review and residual-risk reporting.

## Working Model

1. Read the plan artifacts and the nearest stable architecture and design-intent docs.
2. Ask whether the proposed workflow change improves one of:
   - clarity of target shape
   - cross-implementor coordination
   - recovery across sessions
   - verification quality
   - cost or latency
3. If it mainly adds structure without improving one of those, avoid it.
4. Prefer lightweight implementation plans over strict handoff contracts unless the work is clearly parallel, high-risk, or long-running.
5. Prefer cheap, obedient workers for bounded local tasks. Use frontier models for planning, synthesis, ambiguous design judgment, and high-value review.
6. If a worker result is required, the orchestrator should wait rather than absorb the implementation and bloat its own context.

## Documentation Economy

Default stack:

- Stable architecture docs: concept map, ownership map, key invariants, cross-system relationships.
- Stable design-intent docs: why the system or surface exists, what experience or outcome matters.
- Plan docs: change-scoped intent, scope, implications, sequence, and acceptance criteria.

Only add plan-scoped `DESIGN.md` when at least one of these is true:

- the target shape is not obvious from stable docs and code
- multiple implementors need a shared contract
- architecture needs a scoped "to-be" shape inside the change boundary
- acceptance depends on explicit ownership, interface, or behavior contracts

## Improvement Priorities

- Keep planning lean and accurate.
- Treat executed plan folders as an eval corpus for workflow quality.

## Eval Capability

Use evals to validate that a proposed workflow change produces meaningfully better outcomes before committing to it. An eval is a full end-to-end run — plan then execute — on a fixture scenario, compared against a baseline (the current workflow's output on the same scenario) and a known reference implementation.

See `evals/README.md` for scenario format, results format, and full instructions.

### When to Run an Eval

- Before merging a change to a skill prompt that affects planning, execution, or review behavior
- When a qualitative observation suggests a workflow change might help, but you want signal before committing
- When comparing two candidate approaches (variant testing)

### Running an Eval

1. Choose or create a scenario in `evals/scenarios/` — a real repo at a tagged commit with a known task and reference implementation.
2. Clone the scenario repo at the specified commit into a temporary working directory.
3. Run the full workflow on the task (plan + execute) using the candidate skill changes.
4. Capture cost metrics: agents spawned and model sizes, tool use turns per agent (and total), context estimate (or note if unavailable), wall time.
5. Write results to `evals/results/<scenario>/<YYYYMMDD-HHMMSS>/` following the format in evals/README.md.
6. If `evals/scenarios/<name>/baseline/` is empty, copy the candidate artifacts there — this establishes the baseline. Do not overwrite an existing baseline; it is fixed once set.

### Interpreting Results

Two questions:

1. **Significant cost regression?** — If the change costs meaningfully more (more agents, more turns, more context) without quality gain, it is not worth it.
2. **Quality in the same ballpark as the reference?** — If the candidate is clearly worse than the reference, the change needs work. If clearly better, that is strong signal.

Do not chase small differences within normal run variance. Baseline outputs themselves vary — only clear, significant deltas should drive decisions.

### Variant Testing

To compare two candidate approaches, run each against the same scenario and compare both to the baseline and reference. Record each candidate's cost data in its own `cost-comparison.md` and quality data in its own `quality-comparison.md` under separate timestamped result folders.

## Additional Resources

- [reference.md](reference.md) — numbered lessons from real execution traces
- [retros/](retros/) — staging area for per-execution retros; consumed and removed after consolidation

## Retro Lifecycle

After a plan execution, write a retro in `retros/<plan-name>.md` capturing: execution stats, what worked, what didn't, and any candidate lessons not yet in `reference.md`.

Retros are a holding area, not an archive. When consolidating:

1. Read all files in `retros/`.
2. For each retro, extract lessons or observations not yet reflected in `reference.md` or the relevant skill files.
3. Update `reference.md` and any skills that need changing.
4. Delete the consumed retro files.

A retro that has been fully absorbed into `reference.md` updates has no further value and should be removed. The lessons are the record; the retro is the raw input.
