# Workflow Plugin — Overview

## What It Is

A workflow plugin for Claude Code, opencode, and Cursor providing ten skills (plus four dispatch-only workers), split across two plugins, for structured plan/refine/execute/review workflows — usable identically by a human at the keyboard and by a staged cloud pipeline (build agent → automated review/QA → merge).

## Who Uses It

Teams and individual developers who want:
- Explicit, durable plans with verbatim intent capture and scope validation
- Work decomposed into per-agent briefs *before* execution, so scope is reviewable and a killed run is resumable
- Delegated implementation via authored briefs, not orchestrator paraphrase
- Independent review keyed to the plan's acceptance criteria, right-sized to whether a downstream pipeline stage exists
- Plans that end — a single durable record per change, not an accreting folder of interim artifacts
- A local lab for bootstrapping repo docs, running divergent-candidate exploration, and tuning the workflow itself from real outcomes

## The Skills

**Core plugin (`workflow`)** — cloud-safe, no interactive dead-ends, installable in build and pipeline environments:

1. **plan** — Produces `PLAN.md` (and `DESIGN.md` when contracts need reification). Captures verbatim user intent, validates scope, detects architectural drift, asks only decisions that matter. Runs interactive (checkpoint held) or headless (assumption ledger instead of questions), by explicit declaration.
2. **refine** — Turns a plan into executable work. Does its own code recon, decomposes the plan's light phasing into ordered units with disjoint ownership, writes one complete brief per unit, and rewrites the plan's Execution Phases into the definitive dispatch list. A plan too weak to decompose is bounced back to `plan` with the gaps named — before any build spend. Skipped for single-worker slices.
3. **execute** — Executes an existing plan. Routes `refine`'s briefs verbatim to rightsized workers (authoring inline only where refinement was skipped), writes `IMPLEMENTATION.md` progressively, runs review sized to the declared posture (terminal: mandatory independent review; pipeline: pre-flight self-verification only), lands a PR carrying the `Workflow-Plan:` marker.
4. **comprehensive-review** — Independent review keyed to `PLAN.md`'s acceptance criteria. Fixes straightforward findings in place (closing them without a downstream loop) and authors remediation briefs for structural ones; writes `REVIEW.md` (with a machine-actionable verdict reflecting the post-fix state) into the plan folder; includes an intent-and-assumptions lens and a plan-sufficiency judgment. Reconstructs intent when a PR arrives with no plan folder.
5. **close-out** — Ends a plan. Appends an `## Outcome` section to `PLAN.md` recording what was actually built, deviations and why, how review resolved, and where follow-ups went; promotes a `DESIGN.md` worth keeping to `docs/design/`; deletes the interim artifacts in one commit. The branch history and the PR are the archive; the plan folder is the record.
6. **post-build** — The pipeline stage that picks a PR up where the build leaves off: classifies the change and right-sizes the process, independent review via `comprehensive-review` when needed (delegated remediation and fresh verification only for briefed structural findings), conditional `QA.md` / exact-SHA deploy / browser QA for functional driveable need, a single end-of-work required-checks gate (failures fixed only for non-trivial functional changes), and an uncommitted merge-readiness report. Its delegated phases are dispatch-only worker skills (`post-build-fixer`, `post-build-verifier`, `post-build-qa-planner`, `post-build-qa-driver`) named in the dispatch and loaded only by the worker; repo mechanics come from a per-repo adapter skill.

**Lab plugin (`workflow-lab`)** — local and/or interactive; never required by the pipeline:

7. **setup** — Bootstraps `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` for repos that lack them, via a permission-gated, one-question-per-round conversation.
8. **iterate** — Long-horizon exploration for goals whose success criteria aren't knowable up front: sequential divergent candidates (built via `plan` + `execute`), a divergence gate, cross-candidate synthesis, additive consolidation, then a hardening review relay that locks the base.
9. **transcript-parser** — Extracts objective cost metrics (agents spawned, tool turns, context estimate, wall time) from a session transcript into eval cost-comparison format.
10. **workflow-tuning** — Holds the workflow's design principles and its real-world lessons corpus, and runs evals comparing candidate skill changes against a baseline and reference implementation; harvests both retros and merged PRs' pipeline outcomes (`REVIEW.md`, `QA.md`, remediation briefs).

## Core Intent

Optimize for outcome quality per token. Prevent common failures:
- Silent architectural pivots
- Lost user intent through paraphrasing — orchestrators route context verbatim, they do not translate it
- Implementation without explicit contracts
- Review that finds easy nits instead of underlying problems
- Documentation cascades that mostly restate the code
- A repo-as-backlog mental model — status lives in the PR and the tracker, never in a folder name or a canonical schedule doc

## Key Design Decisions

- Plan, refine, and execute stay separate skills, composed at the run level (never fused into one context). A dedicated planning context produces more accurate plans; a dedicated refinement context makes the decomposition reviewable before build spend commits to it; and both preserve gating, plan validation, and the option to plan without building.
- Nothing in the repo carries status. A plan folder existing on a branch means the work is being built or was built — nothing else. Deferred work becomes a design-intent doc or a tracker issue.
- Coordination between agents travels as authored briefs, routed verbatim — never as an orchestrator's paraphrase of the plan or the review.
- Posture (interactive/headless for plan; terminal/pipeline for execute's review and close-out's placement) is declared explicitly by the invoker, never inferred from environment or TTY.
- `DESIGN.md` is optional — only when it reifies target shape or cross-implementor contracts.
- Every plan ends. One durable record per change: `PLAN.md` with an appended Outcome. The branch history and the PR are the archive.
- Orienting-why (what changes agent behavior in an unspecified situation) stays in each skill body; persuading-why (design-justification prose) lives in one cross-cutting corpus, `workflow-tuning/principles.md`, not loaded during normal execution.

## Stability Boundaries

**Stable** (should not change casually):
- The core/lab partition and each skill's core purpose
- The plan → refine → execute → review → close-out loop, and the PR artifact seam that lets the pipeline locate a plan folder mechanically
- The artifact taxonomy: durable artifacts carry intent and outcome, run-scoped artifacts are consumed at close-out, nothing carries status
- Verbatim intent capture in `PLAN.md`'s Intent section
- The rule that no commit follows the tested commit — which is what fixes close-out's placement in pipeline posture

**Under improvement** (actively evolving):
- The operating hypotheses in `README.md` — falsifiable lenses awaiting a dedicated eval effort
- Eval infrastructure and workflow-tuning's harvest of pipeline outcomes
- Whether `refine`'s brief set needs its own adversarial pass, or whether its executability verdict is sufficient cold-reader pressure
- Per-harness model allocation, kept explicitly provisional because it rots faster than the skill bodies
