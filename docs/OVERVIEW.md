# Workflow Plugin — Overview

## What It Is

A workflow plugin for Claude Code, opencode, and Cursor providing ten skills, split across two plugins, for a design → phased refine/execute → review → close-out workflow — usable identically by a human at the keyboard and by a staged cloud pipeline (build agent → automated review/QA → merge).

## Who Uses It

Teams and individual developers who want:
- A bounding design with verbatim intent, domain contracts, and phases each closed by a provable outcome
- Work refined one phase at a time, against the code the previous phase actually left, so late discoveries land in refinement rather than in the build
- Delegated implementation via authored briefs, not orchestrator paraphrase
- Independent review keyed to the design's phase outcomes, right-sized to whether a downstream pipeline stage exists
- Plans that end — a single durable record per change, not an accreting folder of interim artifacts
- A local lab for bootstrapping repo docs, running divergent-candidate exploration, and tuning the workflow itself from real outcomes

## The Skills

**Core plugin (`workflow`)** — cloud-safe, no interactive dead-ends, installable in build and pipeline environments:

1. **design** — Produces `DESIGN.md`: verbatim intent, problem, solution shape as domain boundaries and contracts, and phases each with a provable outcome, its surfaces, and an approach flag (known or open). Ground is delegated to cheap recon agents. Interactive (checkpoint held) or headless (assumption ledger), by explicit declaration. Phase count is fixed at sign-off.
2. **refine** — Refines the next phase only: reads the design, `IMPLEMENTATION.md`, and the previous phase's carried items, decomposes the phase into units with disjoint ownership and budgets, writes one complete brief per unit, and adds the phase's Units list to `DESIGN.md`. The first refinement also coarse-checks every phase. Bounces to `design` when a contract, boundary, or outcome is missing. Skipped for a one-unit phase.
3. **execute** — Builds one phase per orchestrator: dispatches `refine` when the phase has no units, routes briefs by path to rightsized workers, records each unit in `IMPLEMENTATION.md` as it lands, verifies the phase outcome with a cheap-tier check, and closes the phase record with the git trailer `Workflow-Phase: <slug>:<n>` — then always stops and reports, never dispatching a successor itself. After the last phase: terminal review and close-out, or pipeline pre-flight; lands the PR carrying the `Workflow-Plan:` marker.
4. **comprehensive-review** — Independent review keyed to the design's phase outcomes. Fixes mechanical findings in place, briefs structural ones for remediation, writes `REVIEW.md` with a machine-actionable post-fix verdict, includes the intent-and-assumptions lens and a plan-sufficiency judgment. Reconstructs intent for a PR with no design.
5. **close-out** — Collapses the plan folder into one record file, `docs/plans/<NN>-<slug>.md` (what was built per phase, deviations, review, QA, risks, follow-ups), promotes contracts that outlive the change to `docs/design/`, deletes the folder in one commit.
6. **post-build** — The pipeline stage against a PR: classify and right-size, `comprehensive-review`, bounded remediation and fresh verification for briefed findings, conditional `QA.md` and exact-SHA deploy proof and browser QA, one end-of-work required-checks gate, an uncommitted merge-readiness report. Workers run from standing briefs in the skill's `briefs/`; repo mechanics come from a per-repo adapter skill.

**Lab plugin (`workflow-lab`)** — local and/or interactive; never required by the pipeline:

7. **setup** — Bootstraps `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` for repos that lack them.
8. **iterate** — Long-horizon exploration for goals whose criteria are not knowable up front: sequential divergent candidates, a divergence gate, synthesis, consolidation, a hardening relay. Also the method for a design phase flagged approach-open, with that phase's outcome as the fixed yardstick.
9. **transcript-parser** — Extracts cost metrics from a session transcript into eval cost-comparison format.
10. **workflow-tuning** — Holds the design principles and the lessons corpus; runs evals; harvests retros and merged PRs' pipeline outcomes.

**Driver tool** (`tools/driver/`) — a third, optional way to run the refine/execute loop across phases, beside the two plugins above. Not an agent context: a process, provider-abstracted over the Claude Agent SDK and Cursor's headless agent, chosen by whichever key is present in the environment, run by a person or by an agent holding that key. Agent-orchestrated is the default and works without it — either a human dispatching each phase, or, where the harness has two levels of subagent nesting, a naive coordinator dispatching `execute` per phase in series. The driver exists to test and validate that economics and to reach harnesses agent-orchestration can't: a single-level-nesting harness can run one `execute` invocation but can't also wrap a coordinator around it, and routes to the driver instead (`docs/plans/06-phase-driver/DESIGN.md`).

## Core Intent

Optimize for outcome quality per token. Prevent:
- Silent architectural pivots
- Lost intent through paraphrase — orchestrators route context verbatim
- Implementation without explicit contracts
- Drift absorbed by the build orchestrator instead of by the next refinement
- Review that finds easy nits instead of underlying problems
- Documentation cascades that restate the code
- A repo-as-backlog model — status lives in the PR and the tracker

## Key Design Decisions

- Design, refine, and execute are separate contexts composed at the run level, never fused. Each stage reads the committed artifacts cold.
- A phase is defined by a provable outcome, not by a surface. Outcomes close phases; surfaces define units inside them. The phase count is fixed at design sign-off, so the refine/execute loop is bounded by construction.
- Refinement is per phase, against real code. Carried items live in the closed phase's record in `IMPLEMENTATION.md`, consumed by the next refinement — never in a backlog file.
- Verification per phase is cheap-tier; premium independent review runs once, against the whole design.
- Coordination travels as authored briefs routed verbatim. Briefs carry a budget, verification-first done evidence, and a bounded report.
- Posture is declared by the invoker, never inferred: interactive/headless for design; terminal/pipeline review for execute; close-out's placement follows. Whether another phase runs after one closes is deliberately not this kind of posture — `execute` always stops and reports; it is a property of the invocation instead (a bare call, a coordinator, or the driver).
- Nothing in the repo carries status. Every plan ends in one record file.
- Skills state outcomes and the constraints an agent could not infer; they do not narrate steps an agent can derive. Design rationale lives in `workflow-tuning/principles.md`.

## Stability Boundaries

**Stable**:
- The core/lab partition and each skill's purpose
- The design → phased refine/execute → review → close-out loop, and the PR artifact seam (`Workflow-Plan:` marker, `docs/plans/<NN>-<slug>/`)
- The artifact taxonomy: durable carries intent and outcome, run-scoped is consumed at close-out, nothing carries status
- Verbatim intent in `DESIGN.md`'s Intent section
- No commit follows the tested commit

**Under improvement**:
- The operating hypotheses in `README.md`
- Eval infrastructure and the pipeline-outcomes harvest
- Whether a phase's brief set needs its own adversarial pass beyond `refine`'s verdict
- Per-harness model allocation, provisional by design
