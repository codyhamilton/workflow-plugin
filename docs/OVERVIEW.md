# Workflow Plugin — Overview

## What It Is

A Claude Code plugin that provides four interdependent skills for structured plan/execute/review workflows across repositories.

## Who Uses It

Teams and individual developers who want:
- Explicit, durable planning with intent capture and scope validation
- Delegated implementation with orchestration and cost discipline
- Mandatory independent review after implementation
- Observable lessons from real plan artifacts to improve the workflow itself

## The Skills

1. **planning** — Create PLAN.md and DESIGN.md artifacts. Capture verbatim user intent, validate scope, detect architectural implications, ask only decisions that matter.

2. **plan-execution** — Execute existing plans. Rightsize subagents, maintain orchestration clarity, run mandatory review, write completion artifacts (IMPLEMENTATION.md, REVIEW.md).

3. **comprehensive-review** — Independent review of completed work. Four lenses: contracts/correctness, failure modes, real usefulness, domain-specific concerns. Capped at one external loop before self-review.

4. **workflow-tuning** — Meta-skill for improving the workflow itself. Holds real-world lessons from executed plans. Includes eval capability for validating skill prompt changes against fixtures.

## Core Intent

Optimize for outcome quality per token. Prevent common failures:
- Silent architectural pivots
- Lost user intent through paraphrasing
- Implementation without contracts
- Review that finds easy nits instead of underlying problems
- Documentation cascades that mostly restate the code

## Key Design Decisions

- Plans are concise and decision-oriented, not implementation specs
- Stable docs are concept maps and intent anchors, not code paraphrases
- DESIGN.md is optional — only when it reifies target shape or cross-implementor contracts
- Phased execution is the default, with explicit cost/quality tradeoffs
- Review is focused and capped; one external loop + self-review model, not repeated loops

## Stability Boundaries

**Stable** (should not change):
- The four-skill structure and their core purposes
- The plan/execute/review workflow loop
- The provenance capture model (verbatim user intent in PLAN.md)

**Under improvement** (actively evolving):
- Provenance capture — moving from agent convention to transcript extraction
- Setup process — bootstrapping missing stable docs
- Eval infrastructure — testing skill prompt variations against fixtures
