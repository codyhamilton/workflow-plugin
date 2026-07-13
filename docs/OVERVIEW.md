# Workflow Plugin — Overview

## What It Is

A workflow plugin for Claude Code, opencode, and Cursor providing eight skills, split across two plugins, for structured plan/execute/review workflows — usable identically by a human at the keyboard and by a staged cloud pipeline (build agent → automated review/QA → merge).

## Who Uses It

Teams and individual developers who want:
- Explicit, durable plans with verbatim intent capture and scope validation
- Delegated implementation via authored briefs, not orchestrator paraphrase
- Independent review keyed to the plan's acceptance criteria, right-sized to whether a downstream pipeline stage exists
- A local lab for bootstrapping repo docs, running divergent-candidate exploration, and tuning the workflow itself from real outcomes

## The Skills

**Core plugin (`workflow`)** — cloud-safe, no interactive dead-ends, installable in build and pipeline environments:

1. **plan** — Produces `PLAN.md` (and `DESIGN.md` when contracts need reification). Captures verbatim user intent, validates scope, detects architectural drift, asks only decisions that matter. Runs interactive (checkpoint held) or headless (assumption ledger instead of questions), by explicit declaration.
2. **execute** — Executes an existing plan. Dispatches rightsized workers with authored briefs, writes `IMPLEMENTATION.md` progressively, runs review sized to the declared posture (terminal: mandatory independent review; pipeline: pre-flight self-verification only), lands a PR carrying the `Workflow-Plan:` marker.
3. **comprehensive-review** — Independent review keyed to `PLAN.md`'s acceptance criteria. Fixes straightforward findings in place (closing them without a downstream loop) and authors remediation briefs for structural ones; writes `REVIEW.md` (with a machine-actionable verdict reflecting the post-fix state) into the plan folder; includes an intent-and-assumptions lens and a plan-sufficiency judgment. Reconstructs intent when a PR arrives with no plan folder.
4. **post-build** — The pipeline stage that picks a PR up where the build leaves off: classifies the change and right-sizes the process, independent review via `comprehensive-review` when needed (delegated remediation and fresh verification only for briefed structural findings), conditional `QA.md` / exact-SHA deploy / browser QA for functional driveable need, a single end-of-work required-checks gate (failures fixed only for non-trivial functional changes), and an uncommitted merge-readiness report. Its delegated phases are dispatch-only worker skills (`post-build-fixer`, `post-build-verifier`, `post-build-qa-planner`, `post-build-qa-driver`) named in the dispatch and loaded only by the worker; repo mechanics come from a per-repo adapter skill.

**Lab plugin (`workflow-lab`)** — local and/or interactive; never required by the pipeline:

5. **setup** — Bootstraps `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` for repos that lack them, via a permission-gated, one-question-per-round conversation.
6. **iterate** — Long-horizon exploration for goals whose success criteria aren't knowable up front: sequential divergent candidates (built via `plan` + `execute`), a divergence gate, cross-candidate synthesis, additive consolidation, then a hardening review relay that locks the base.
7. **transcript-parser** — Extracts objective cost metrics (agents spawned, tool turns, context estimate, wall time) from a session transcript into eval cost-comparison format.
8. **workflow-tuning** — Holds real-world lessons from plan/execute/review workflows and runs evals comparing candidate skill changes against a baseline and reference implementation; harvests both retros and merged PRs' pipeline outcomes (`REVIEW.md`, `QA.md`, remediation briefs).

## Core Intent

Optimize for outcome quality per token. Prevent common failures:
- Silent architectural pivots
- Lost user intent through paraphrasing — orchestrators route context verbatim, they do not translate it
- Implementation without explicit contracts
- Review that finds easy nits instead of underlying problems
- Documentation cascades that mostly restate the code
- A repo-as-backlog mental model — status lives in the PR and the tracker, never in a folder name or a canonical schedule doc

## Key Design Decisions

- Plan and execute stay separate skills, composed at the run level (never fused into one context), because a dedicated planning context produces more accurate plans and preserves gating, plan validation, and the option to plan without building.
- Nothing in the repo carries status. A plan folder existing on a branch means the work is being built or was built — nothing else. Deferred work becomes a design-intent doc or a tracker issue.
- Coordination between agents travels as authored briefs, routed verbatim — never as an orchestrator's paraphrase of the plan or the review.
- Posture (interactive/headless for plan; terminal/pipeline for execute's review) is declared explicitly by the invoker, never inferred from environment or TTY.
- `DESIGN.md` is optional — only when it reifies target shape or cross-implementor contracts.
- Orienting-why (what changes agent behavior in an unspecified situation) stays in each skill body; persuading-why (design-justification prose) lives in a per-skill `reference.md`, not loaded during normal execution.

## Stability Boundaries

**Stable** (should not change casually):
- The eight-skill structure across the core/lab partition, and each skill's core purpose
- The plan → execute → review workflow loop and the PR artifact seam that lets the pipeline locate a plan folder mechanically
- The artifact taxonomy: durable artifacts carry intent and outcome, briefs carry run-scoped coordination, nothing carries status
- Verbatim intent capture in `PLAN.md`'s Intent section

**Under improvement** (actively evolving):
- The operating hypotheses in `README.md` — falsifiable lenses awaiting a dedicated eval effort
- Eval infrastructure and workflow-tuning's harvest of pipeline outcomes
- Per-harness mechanics (model allocation, session-ID capture) kept in reference/config files precisely because they rot faster than the skill bodies
