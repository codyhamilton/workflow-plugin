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

### Turn 6

**User responded:** Confirmed `Workflow-Phase:` as the trailer key. Walked scenario mechanics (happy path, redesign, phasing bounce, unclean phase exit, brief-level adjustments, unclean brief exit) with and without the driver, then pushed on whether the terminology used to describe them (`held`, `bounced`, `blocked`, `close-out`, `continue`) was doing functional work or just wrapping semantic meaning into labels that travel as prose anyway. Argued from the unit layer up: a brief exits with a message, no status, and the coordinator's scope (may it adjust a later brief?) is structural, not something the status needs to encode. A phase exits successful, unsuccessful, or null (terminated unknown), plus a message; asked whether unsuccessful ever means anything but escalation, and to whom — the user in an agentic session, the parent coordinator headless. Then, separately: the driver should be runnable from within a cloud agent session as a stdio MCP server, so the cloud agent designs and holds escalation while a driver-backed MCP tool coordinates execution — get status, poll, trigger phases. Over MCP the SDK should default to running just the next phase, not looping to completion. Flagged the cloud-agent-container-lifetime risk (a background phase dispatched via MCP can outlive its host) as real but deferred — local execution keeps the host up for the run, a later addition could run execution on a separate longer-lived host, and it's worth checking whether cloud agent sessions persist longer while a background process is active. Short-term mitigation: bound each background span to one phase by returning after every phase, which is the same shape as the single-phase MCP default already decided.

**Agent decisions:**

- Collapsed the phase report's status enum from four values (`closed`, `held`, `bounced`, `blocked`) to three (`closed`, `incomplete`, `unsuccessful`): checked against the driver's own loop, all three non-`closed`, non-`incomplete` values were already handled identically (print, exit non-zero), so the split carried no functional weight. The distinguishing content moved to the report's free-text `reason` field.
- Dropped `hold`/`continue` as a named posture. Neither `execute` nor the driver ever reads or branches on it; whether a next phase runs is fully determined by which of three things was invoked (a bare call, a coordinator instructed to run to completion, or the driver's CLI vs. MCP front end), not a flag declared upfront or read back. Removing it also removed the `hold`/`held` name collision the old four-value enum had against the posture.
- Added the driver's MCP transport: same resolve/dispatch/report primitive as the CLI, exposed as `status`/`trigger_phase`/`poll` to a calling agent session, defaulting to one phase per call rather than the CLI's run-to-completion default. Added as Phase 4, approach `open` — the primitive is Phase 2/3's provider layer, unchanged; what to do about an orphaned dispatch on host death is not yet settled.
- Recorded the MCP host-lifetime risk in Open Questions rather than solving it: the same unresolved cold-read-on-death gap as a dropped subagent, not a new failure mode, and out of scope for this pass per the user's own framing ("we'll deal with this separately").

### Turn 7

**User responded:** Confirmed briefs stay until `close-out`. Refocused on Phase 1 — the primary, non-driver workflow. Distinguished three shapes: human-driven design then execute (no constraint, the human is the dispatch boundary); unattended design+execute in one session on a harness with subagent nesting (parent → executor → refine + briefs, works); and the same on a harness limited to one level of nesting, where the parent would have to call refine and briefs directly per phase to make up for the missing layer — naive-instructed but still one context accumulating every phase's work. Concluded that shape should not use naive coordination at all and should go to the driver MCP instead, since it bypasses the layering problem entirely. Asked to note this in the design, and to note that the driver should eventually run external to its caller rather than co-located.

**Agent decisions:**

- Named the nesting requirement precisely: naive coordination needs two levels of subagent dispatch (coordinator → `execute`, `execute` → `refine`/workers), not "some nesting." A one-level harness still runs a single `execute` invocation fine but can't also wrap it in a coordinator; flattening the coordinator into the top context to compensate just moves the accumulating-orchestrator problem up one frame rather than avoiding it. Added as Non-goal and Decision, with Phase 1's outcome and a new Provenance Note restating why the threshold is two, not one.
- Recorded, as direction rather than a built phase, that the driver should eventually run on a host external to its caller: today the CLI runs on the invoker's machine (fine, the terminal outlives the run) and the MCP server's phase agent runs on the calling agent's own container (not fine — the same container-lifetime coupling that motivated one-phase-per-call). Added to Decisions, Open Questions, and a Provenance Note; explicitly not scoped to a phase, pending the container-lifetime research already deferred.

## Agent Decisions

- **Driver never commits**: every repo write is a phase agent's. Rationale: the driver holds no model context and should hold no authority over artifacts; its state is stdout and an exit code, which keeps invariant 3 trivially true.
- **Boundary under the driver is `hold`**: the driver is the boundary. Rationale: no new posture is needed; `hold` already means "stop after the phase record and report", which is exactly what a driven phase agent must do.
- **After the last phase, the phase agent still owns review and close-out**: the driver runs one more session for wrap-up and stops on the done commit. Rationale: `execute`'s after-last-phase path already exists and is posture-declared; duplicating it in the driver would be a second orchestrator.
- **Adversarial pass applied** (clean context, one pass): the run gained its own `done` trailer because terminal close-out deletes the file the resolver counts and a death after the last phase looked finished; `continue` moved from `execute` to a coordinator that has done no phase work, because a phase-1 orchestrator dispatching phase 2 is the long-lived orchestrator the design exists to remove; resolution was scoped to `<default>..HEAD` with lowest-missing rather than max-plus-one so merged history and a stray trailer cannot skip a phase; the report became a fenced block in final output so the Cursor provider needs no custom-tool hook; `held` was defined by absence of closure and a trailer-only closing commit was permitted for repair. One finding reversed a user direction — briefs now stay until `close-out` — and is flagged in Decisions for the checkpoint. Rationale for applying it: brief removal made file presence a second encoding of phase state.
