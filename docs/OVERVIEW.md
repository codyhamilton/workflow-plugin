# Workflow Plugin — Overview

## What It Is

A workflow plugin for Cursor / Claude Code / Codex that provides interdependent skills for structured plan/execute/review workflows across repositories. The machine-readable contract is `workflow-protocol.json` (`workflow-protocol: 1`).

## Who Uses It

Teams and individual developers who want:
- Explicit, durable plan with intent capture and scope validation
- Delegated implementation with orchestration and cost discipline
- Mandatory independent review after implementation
- Observable lessons from real plan artifacts to improve the workflow itself
- Non-interactive install into Cursor Cloud agent environments without Team Marketplace

## The Skills

1. **workflow-plan** — Create PLAN.md and DESIGN.md artifacts. Capture verbatim user intent, validate scope, detect architectural implications, ask only decisions that matter.

2. **workflow-execute** — Execute existing plans. Rightsize subagents, maintain orchestration clarity, run mandatory review, write completion artifacts (IMPLEMENTATION.md, REVIEW.md).

3. **comprehensive-review** — Independent review of completed work. Four lenses: contracts/correctness, failure modes, real usefulness, domain-specific concerns. Capped at one external loop before self-review.

4. **workflow-setup** — Bootstrap missing stable docs (`docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`).

5. **iterate** — Long-horizon work without a fixed spec: divergent candidates, synthesis, harden, extrapolate.

6. **workflow-tuning** — Meta-skill for improving the workflow itself. Holds real-world lessons from executed plans. Includes eval capability for validating skill prompt changes against fixtures.

7. **transcript-parser** — Extract cost metrics from session transcripts for evals.

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
- Generic skill names are namespaced (`workflow-plan`, `workflow-execute`, `workflow-setup`) to avoid collisions in shared skill directories
- Portable artifact rules (`protocol/artifacts.md`) are separate from harness model recommendations (`protocol/models.yaml`)

## Stability Boundaries

**Stable** (should not change lightly):
- The skill structure and their core purposes
- The plan/execute/review workflow loop
- The provenance capture model (verbatim user intent in PLAN.md)
- `workflow-protocol` major version semantics

**Under improvement** (actively evolving):
- Provenance capture — moving from agent convention to transcript extraction
- Setup process — bootstrapping missing stable docs
- Eval infrastructure — testing skill prompt variations against fixtures
- Model recommendations in `protocol/models.yaml`
