# Provenance: Phase Driver

Interactive posture only. Headless runs carry intent, the assumption ledger, and decisions in `DESIGN.md` alone.

## Session

- Session: Initial design (September 16, 2026)
- Timestamp: 2026-09-16T14:52:49Z
- CWD: /home/user/workflow-plugin

## Initial Request (verbatim)

> With the changes on this branch, the thing to consider is how we would run this. We've identified the orchestrator is a cost driver - how can we manage the refine/execute loop over multiple phases while not building up a larger orchestrator. E.g. can we have a triggered loop, each iteration being fresh - what options are there available to us within claude code as an example

## Design Conversation

### Turn 1

**User responded:** The orchestrator is a cost driver; the refine/execute loop over multiple phases must not build up a larger orchestrator. Is a triggered loop possible, each iteration fresh, within Claude Code?

**Agent decisions:**

- Surveyed the harness's own options: a GitHub Action polling the plan folder with headless `claude -p`; a Claude Code Remote Routine spawning a fresh session per firing.

### Turn 2

**User responded:** Neither fits. A routine fires independently of ongoing work, so it does not link phases. A GitHub Action has to stay active throughout a long job. What about the Cursor SDK or the Claude Agent SDK — both give a top layer that allows contained phasing, and let us limit the orchestrator agent at each phase by tool limiting, cutting its context and focusing its role.

**Agent decisions:**

- Dropped schedule- and CI-driven options; recorded why in Provenance Notes.
- Adopted the SDK layer: one fresh session per phase, tool surface reduced per phase, causal chaining (a phase runs because the previous one closed) instead of polling.

### Turn 3

**User responded:** Sketch a design for a driver. Also fill the gap — there is no deterministic way to track phasing that an SDK could rely on.

**Agent decisions:**

- Proposed commit trailers on the phase-closing commit as the deterministic signal, by analogy to the `Workflow-Plan:` PR marker, initially with four fields (phase, outcome, boundary, verify).

### Turn 4

**User responded:** Go simpler: `plan: <slug>:<phase>` marks a phase as committed. The closing commit cleans up the briefs, updates the plan doc to mark the phase complete, and is a statement that it has been reviewed and accepted. That is enough to determine the next open phase; within a phase the execution agent owns refinement and breakdown to closure. If an agent fails to close a phase, the SDK launches another, which discovers implementation state and closes properly. Exit conditions that are not closure are reported through the execution agent's output to the SDK, or a custom tool; every other incomplete exit just results in a new execution agent that discovers state and executes or reports normally.

**Agent decisions:**

- Reduced the durable signal to one trailer. Transient outcomes (hold, blocked, bounced, verification) become the run's report, never committed.
- "Updates the plan doc" read as `IMPLEMENTATION.md`'s existing phase record, not a field in `DESIGN.md`, keeping principle 8 intact.
- Incomplete runs are re-dispatched, not diagnosed; the fresh agent reads committed state cold.
- Re-dispatch count and per-phase cost are driver-process bookkeeping, not repo state.

### Turn 5

**User responded:** Draw up a design, dogfooding our own approach. SDKs cannot be relied on as always available: the workflow must still run with a lightweight orchestrator — single-phase execution, or where subagent nesting is possible, an orchestrator running phase execution agents in series as a naive coordinator. Define those briefly and design the SDK approach: a design is created with the workflow, then the SDK is run to execute it. Lightweight; runnable by a user or by an agent given keys. Support both the Cursor and Claude Agent SDKs behind one abstraction, chosen by the key in the environment. Two paths, distinct: the agent-orchestrated method need not operate like the SDK; keep it light and naive. The SDK approach is to build, test, and validate — not a pivot on the execution model.

**Agent decisions:**

- Four domains: Phase closure (shared fact), Phase report (transient channel), Driver (the tool), Naive coordination (the agent path's `continue`).
- Three phases: closure made deterministic in the skills and docs; the driver with the Claude provider; the Cursor provider.
- Trailer key aligned to the existing `Workflow-` namespace (`Workflow-Phase:`) rather than `plan:`; flagged for the checkpoint.
- Briefs removed at phase closure per the user's Turn 4; consequence for `close-out` flagged for the checkpoint.
- Cursor's headless surface could not be fetched from this environment; treated as `refine`'s Ground for phase 3, not an open question.

## Agent Decisions

- **Driver never commits**: every repo write is a phase agent's. Rationale: the driver holds no model context and should hold no authority over artifacts; its state is stdout and an exit code, which keeps invariant 3 trivially true.
- **Boundary under the driver is `hold`**: the driver is the boundary. Rationale: no new posture is needed; `hold` already means "stop after the phase record and report", which is exactly what a driven phase agent must do.
- **After the last phase, the phase agent still owns review and close-out**: the driver stops when no phase is open. Rationale: `execute`'s after-last-phase path already exists and is posture-declared; duplicating it in the driver would be a second orchestrator.
