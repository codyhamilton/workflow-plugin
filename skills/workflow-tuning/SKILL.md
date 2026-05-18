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

## Additional Resources

- [reference.md](reference.md)
