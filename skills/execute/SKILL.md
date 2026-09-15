---
name: execute
description: Build one phase of a signed-off design from `docs/plans/` — refine it if needed, route briefs to rightsized workers, verify the phase outcome, record it, then hold at the boundary or continue. Runs terminal review and close-out after the last phase. Use when the user wants designed work built.
---

# Execute

One phase per orchestrator. The orchestrator holds control state and routes; it does not implement while workers run, and it does not read what a worker wrote beyond the worker's report.

Read `DESIGN.md`, `IMPLEMENTATION.md`, and the briefs cold from the committed artifacts, even when the previous stage ran in this session. A design that no longer matches the architecture or the intent stops the run and goes back to `design`.

## Outcome of a phase

- `IMPLEMENTATION.md` exists before any work starts, with run identity at the top: tool, session or run ID or URL, start time.
- The phase has units. `refine`'s where it ran. Where the phase has no Units list and is more than one worker's work, `refine` is dispatched for it as a separate context and the run continues from its verdict; a bounce stops the run. Where the phase is one unit, one brief is authored inline from the design's contracts, with the same anatomy as `refine`'s, written to `briefs/` and committed before dispatch.
- Every worker got its brief by path, plus repo, branch, and how to report back. Nothing restated, nothing inlined.
- Dependencies were honoured; only units declared alongside each other ran in parallel.
- Each unit's outcome is recorded in `IMPLEMENTATION.md` against its brief name as it lands, never batched: what was built, surfaces touched, deviations, and per agent the turns and final context where the harness reports them.
- Contradictions a worker reported amended the brief file. The amended brief is what any re-dispatch reads.
- The phase outcome in `DESIGN.md` has been verified against real behaviour by a cheap-tier check: the outcome's own entry point → action → result or observable statement, plus each unit's done evidence. Reports are not verification.
- The phase record in `IMPLEMENTATION.md` closes with the verification result and a **Carried** section: deferred bugs, non-blocking findings, and brief amendments the next refinement must place. Ordered, no status column, "None" when empty.
- Everything is committed. The branch resumes from `DESIGN.md` plus `IMPLEMENTATION.md` alone: units with a recorded outcome are done, the rest are the remaining work.

## Boundary

Declared by the invoker; default **hold**.

- **Hold**: stop after the phase record. Report the outcome, the carried items, and the next phase.
- **Continue**: dispatch a fresh orchestrator for the next phase. Never carry a second phase in this context.

A phase flagged **approach: open** is not built by this skill's default path. Hold at its boundary and report, unless the invoker declared how open phases run (for example `iterate` with the phase outcome as the fixed yardstick).

## After the last phase

Review posture is declared by the invoker; default **terminal**.

- **Terminal**: one independent review via `comprehensive-review` against the whole design, written to `REVIEW.md`. A `blocker` or `high` finding that is in scope and not architectural is resolved by a clean agent: one pass on the allocated model, then one retry on the next model tier, then stop for a human. Then `close-out`, as the last commit before the PR.
- **Pipeline**: pre-flight self-verification only — it builds, the phase outcomes hold, the folder is complete — recorded in `IMPLEMENTATION.md`. No `REVIEW.md`; close-out happens after merge.

"Skip review" is a pipeline declaration, not licence to skip verification.

Then push and open or update the PR with `Workflow-Plan: docs/plans/<NN>-<slug>/` as the first line of the body. Completion is the commits plus that marker.

## Workers

- One worker per unit, on the cheapest worker likely to succeed. Starting allocations, to tune: Claude Code — Haiku for research and small bounded changes, Sonnet for large or ambiguous ones, Opus only where directed. Cursor — Composer unless directed. Codex — GPT5.4 high, mini for exploration, xhigh for review.
- A failed unit gets one retry on the next model tier, then a human.
- Implementing a small unit directly is a judgment call when no worker is running and the orchestrator's context is already hot with the design. Never while workers run.
- Never resume a stalled worker by message. End it, take its handoff, dispatch a fresh one.
- A worker's deferred bug gets a small fresh fixer after the reporting unit is complete, not a reopened worker.

## Rules

- Execute only from an existing design. Do not invent scope.
- Write `IMPLEMENTATION.md` as work lands, never at the end.
- No status files, schedule docs, or renamed folders.
