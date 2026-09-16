# Phase Driver

## Intent

User request, verbatim:

> Ok I think we can take this a bit further and draw up a design, dogfooding our own approach.
>
> Our direction here is leaning heavily into the SDKs but these can't be relied on as always available. The workflow is still able to be carried out with a lightweight orchestrator, either through carrying out single-phase execution or where subagent nesting is possible by having the orchestrator run phase execution agents in series, leaving itself a naive coordinator.
>
> We can define these very briefly, and provide a design for the SDK approach. For SDK, a design would be created with the workflow, then the sdk is run to execute it, which carries out the work phases. This only needs to be very lightweight, and could be run directly by the user or by an agent (if the agent is given appropriate keys to use).
>
> We should look at how this supports different providers - the cursor SDK and claude agent sdk work similarly, and we could provide an abstraction that allows either to be used, assuming appropriate key is provided in the environment.
>
> From a high level we have:
>
> * A design skill that produces some architecture and concrete, provable phases
> * An execution skill that refines and executes a phase
> * A tool (backed by cursor/claude SDKs) which can coordinate all phases execution end to end, is provided in the plugin and can be run by a user (or agent if properly configured)
>
> This provides two paths, and they are distinct. when we use execution we don't need the agent orchestrated method to operate exactly like the sdk - let the sdk manage its own directive. Just make sure our agent orchestrated approach stays light and naive.
>
> The SDK approach is something for us to build, to test and validate, not a complete pivot on our execution model.

## Problem

The execute orchestrator is the swing line in a run's cost: bounded to one phase on a cheap model it is 7% of the bill; unbounded on a premium model it is half ([analysis §6](../../analysis/2026-09-08-workflow-vs-field.md)). The workflow's answer is "a fresh orchestrator per phase", but two things stop that from being enforceable:

- **Nothing outside an agent's context knows which phase is next.** "The phase record closes with the verification result" is a prose convention a model recognises; a script, a resuming human, or a fresh agent has to read `IMPLEMENTATION.md` and infer. So the only thing that can drive the loop across phases today is an agent holding the whole run in its head, which is the cost the loop exists to avoid.
- **`continue` is a discipline, not a mechanism.** `execute` says "dispatch a fresh orchestrator for the next phase. Never carry a second phase in this context." Whether that happens depends on the harness having subagent nesting and the orchestrator obeying. There is no path where a plain process, holding no model context, runs the loop.

Scheduled triggers and CI polling were considered and rejected: a schedule has no causal link to a phase closing, and a polling job stays open (and billed) for a run that may take hours.

## Solution Shape

Two distinct ways to run the loop, sharing one deterministic fact.

The **shared fact** is phase closure: the commit that closes a phase carries a trailer naming the plan and the phase. "Which phase is open" becomes a pure function of the branch's git log and `DESIGN.md`'s phase list, readable by anything, no model required. Everything transient — hold, blocked, bounced, verification outcome — stays a live return value of the run that produced it and is never written to the repo.

The **agent-orchestrated path** is the existing workflow, tightened: `execute` runs one phase and closes it with the trailer. At `continue`, the invoking context is a naive coordinator — it dispatches the next phase's `execute` as a subagent, holds only its report, and repeats; where nesting is not available, it holds and names the next phase. It does not read artifacts, resolve state, or mimic the driver.

The **driver path** is a tool in the plugin, `tools/driver/`, run by a person or by an agent holding the keys. Given a plan folder it resolves the open phase from git, runs one phase agent in a fresh session through a provider (Claude Agent SDK or Cursor's headless agent, chosen by the key present in the environment), reads the agent's structured report, and repeats until no phase is open or a report says stop. A run that ends without a report is not a special case: the driver re-dispatches once, and the fresh agent does what a resuming human does — reads the committed artifacts, finishes or reports honestly. The driver never commits; every commit on the branch is a phase agent's.

The driver is built to test and validate the fresh-orchestrator-per-phase economics, not to replace the agent-orchestrated path, which remains the default and must keep working without any SDK present.

### Domain: Phase closure

- Owns: the meaning of "this phase is closed", and the resolution of the open phase. Owned by `execute`.
- Contract:
  - A phase is closed by exactly one commit, the **closing commit**: the commit that records the phase's verification result and Carried section in `IMPLEMENTATION.md`, removes that phase's briefs from `briefs/`, and carries the git trailer `Workflow-Phase: <slug>:<n>` where `<slug>` is the plan folder's slug and `<n>` the 1-based phase index in `DESIGN.md`. The trailer is the attestation that the phase was verified and accepted; it appears on no other commit.
  - The open phase is `max(n for trailers of this slug on the branch) + 1`; with no trailer it is `1`; when it exceeds the count of `### Phase` headings in `DESIGN.md` there is no open phase. A malformed or absent trailer never advances the count.
  - The trailer is commit metadata in the same class as the PR body's `Workflow-Plan:` marker: a mechanical locator, immutable per commit, not a status field in an artifact. Invariant 3 ("nothing in the repo carries status") is unchanged.
- Non-goals: unit-level progress (that is `IMPLEMENTATION.md`'s per-unit record, read by agents, not by the driver); anything transient (hold, blocked, bounced); a phase that was attempted and not closed leaves no trace beyond its ordinary commits.

### Domain: Phase report

- Owns: the one-shot signal from a phase run to whatever invoked it. Owned by the phase agent (`execute`).
- Contract:
  - A phase run ends with one report: `status` ∈ `closed | held | bounced | blocked`, `phase: <n>`, `reason` (free text, required for anything but `closed`). `closed` means the closing commit exists on the branch; `held` means the run stopped at a declared checkpoint or an approach-open phase; `bounced` means `refine` or `execute` sent the design back and Open Questions were written; `blocked` means retries are exhausted and a human is needed.
  - The channel is the invoker's: under the driver, a tool the driver provides to the phase agent and reads from the run's result; under the agent-orchestrated path, the subagent's returned report. The report is never written to the repo and is never trusted across a process boundary — the next invocation re-derives state from Phase closure.
  - A run that ends with no report is **incomplete**. Incomplete is not diagnosed; it is re-dispatched, once.
- Non-goals: carrying state between runs; the driver's own bookkeeping (re-dispatch count, per-phase cost), which lives in the driver process and its output.

### Domain: Driver

- Owns: `tools/driver/`; the loop; provider selection; the reduced tool surface each phase agent runs with. Owned by the plugin.
- Contract:
  - Invocation: `python3 tools/driver/run.py <plan-folder> [--provider claude|cursor] [--review terminal|pipeline] [--max-redispatch N]`, from a checkout on the plan's branch. Provider defaults to whichever key is present in the environment (`ANTHROPIC_API_KEY`, `CURSOR_API_KEY`); both present requires `--provider`; neither is an error before any run starts.
  - Loop: resolve the open phase (Phase closure) → none: exit 0 → run one phase agent in a fresh session with boundary `hold` (the driver is the boundary) and the declared review posture → read the report → `closed`: loop; `held` | `bounced` | `blocked`: print the report, exit non-zero; incomplete: re-dispatch once, then treat as `blocked`. After the last phase closes, the same phase agent has already run `execute`'s after-last-phase path (review or pre-flight, close-out, PR); the driver's job is done when no phase is open.
  - Each phase agent is a fresh session: no resume, no carried transcript. Its prompt is the plan folder path, the branch, the postures, and the instruction to run `execute`; the skill content is what it reads, not what the driver restates.
  - Reduced surface: file read and write, shell for git and the phase's verification, subagent dispatch, and the report tool. No web, no other MCP servers. Subagents the phase agent dispatches get their own surfaces; restricting the coordinator does not restrict its workers.
  - Provider interface: `run_phase(plan, phase, postures) -> Report | None`. One provider per SDK; the loop is provider-agnostic. Each provider reports the run's turns and cost where its SDK exposes them, and the driver prints them per phase — that is the measurement the tool exists to take.
  - The driver never writes to the repo. Every commit is the phase agent's; the driver's state is its stdout and exit code.
- Non-goals: running `design` (a conversation, not a phase); running review or close-out itself (`execute` owns those after the last phase); merging; retrying beyond one re-dispatch; any repo-side status.

### Domain: Naive coordination

- Owns: what `continue` means in the agent-orchestrated path. Owned by `execute`'s skill text.
- Contract: at `continue`, the invoking context dispatches `execute` for the next phase as a subagent with the same postures and holds nothing but its report; on `closed` it repeats, on anything else it stops and reports. Where the harness has no subagent nesting, `continue` degrades to `hold` with the next phase named. The coordinator does not resolve state, read artifacts, or restate briefs.
- Non-goals: parity with the driver; provider selection; cost measurement.

## Architectural Implications

- `docs/ARCHITECTURE.md` **phase boundary** contract gains the closing commit and trailer; **PR Artifact Seam** build-stage contents change: `briefs/` holds only the open phase's briefs, closed phases' briefs are in history.
- `close-out` reads closed phases' briefs from history, or relies on `IMPLEMENTATION.md`'s per-unit outcomes (recorded against brief name) for the record. Its "read as a set" step names this.
- `docs/OVERVIEW.md` gains the driver as a third element beside the skills, with its posture: default path is agent-orchestrated; the driver is optional and needs a key.
- Principle 8 stands. The trailer is the second mechanical marker after `Workflow-Plan:`; `workflow-tuning/principles.md` should say so where it discusses the marker, so the precedent is named rather than rediscovered.
- The Cursor provider's exact headless surface could not be verified from this environment (cursor.com is not reachable here). Its shape — a subprocess or API call that runs one agent in a checkout and returns structured output — is settled; `refine` grounds the flags and output format when it briefs that phase.
- Phase 3 is the natural first subject for the phase-2 driver: build the Cursor provider by driving it with the Claude provider. That is a sequencing choice for the invoker, not a requirement.

## Decisions

- **Two paths, distinct.** The agent-orchestrated path stays light and naive and is the default; the driver is built to test and validate, not to replace it.
- **One trailer, not a status block.** Closure is the single durable fact (`Workflow-Phase: <slug>:<n>`); hold, blocked, bounced, and verification outcome are transient and travel only as the run's report. An earlier four-field trailer was rejected for putting transient state in the durable channel.
- **Trailer key.** The user proposed `plan: <slug>:<phase>`; this design uses `Workflow-Phase:` to sit beside the existing `Workflow-Plan:` PR marker under one namespace. Same value shape, different key — for confirmation at the checkpoint.
- **Briefs are removed at phase closure.** The closing commit cleans up the phase's briefs. Consequence for `close-out` noted above — for confirmation at the checkpoint.
- **Incomplete means re-dispatch.** No diagnosis of why a run did not report; a fresh agent reads the committed state and finishes or reports. Bound: one re-dispatch, matching `execute`'s own one-retry rule.
- **Provider by key.** The provider is chosen by which key the environment holds; an explicit flag overrides.
- **The driver never commits.** All repo writes are the phase agent's.

## Assumption Ledger

None — see PROVENANCE.md.

## Open Questions

None.

## Phases

### Phase 1 — Closure is deterministic

- Outcome: on a branch carrying plan `<slug>` with phases 1..k closed by `execute`, `git log --format='%(trailers:key=Workflow-Phase,valueonly)'` lists exactly `<slug>:1` … `<slug>:k`, each on the commit that closed that phase's record in `IMPLEMENTATION.md` and removed its briefs; and `execute` invoked with `continue` in a harness with subagent nesting dispatches the next phase as a subagent and holds only its report, while without nesting it holds and names the next phase.
- Surfaces: `skills/execute/SKILL.md` (Outcome of a phase, Boundary), `skills/close-out/SKILL.md` (reading set), `docs/ARCHITECTURE.md` (phase boundary, PR Artifact Seam), `docs/OVERVIEW.md`, `plugins/workflow-lab/skills/workflow-tuning/principles.md` (#8 precedent).
- Approach: known
- Depends on: nothing

### Phase 2 — The driver runs a design with Claude

- Outcome: `python3 tools/driver/run.py docs/plans/<NN>-<slug>/` in a checkout with `ANTHROPIC_API_KEY` set, against a signed-off design with two or more phases, runs each open phase in a fresh session, prints each phase's report with its turns and cost, and exits 0 with every phase's closing commit on the branch — or exits non-zero at the first `held`, `bounced`, or `blocked` report, or after one re-dispatch of an incomplete run. `git log` shows no commit authored by the driver.
- Surfaces: `tools/driver/` (new: `run.py`, `providers/claude.py`, `README.md`), `docs/OVERVIEW.md` (the tool's entry).
- Approach: known
- Depends on: Phase 1

### Phase 3 — The driver runs a design with Cursor

- Outcome: the same command with `CURSOR_API_KEY` set (or `--provider cursor`) runs a phase through Cursor's headless agent and yields a report of the same shape; a design whose phase 1 was closed under Cursor and phase 2 under Claude shows no difference to the driver or in the branch beyond the run identity in `IMPLEMENTATION.md`.
- Surfaces: `tools/driver/providers/cursor.py`, `tools/driver/README.md`.
- Approach: known
- Depends on: Phase 2

## Provenance Notes

- **Why not a schedule or a CI job.** A Routine or cron fires independently of a phase closing, so it is either idle or late, and cannot chain phases. A CI job that waits for closure holds a runner open for the whole run. The driver is causal: the next phase runs because the last one reported `closed`, and the process lives only as long as one phase.
- **Why not resume the SDK session.** Resume is the thing the loop exists to avoid: it carries the previous phase's context into the next. Cold read per phase is the invariant; the SDK makes it a mechanism instead of a discipline.
- **Why the trailer is not a status field.** Status fields drift because they restate something else and must be kept in sync. The trailer restates nothing: it is the act of closing, on the commit that closed. It cannot be stale, and it cannot be edited without rewriting history. That is the same reasoning that admits `Workflow-Plan:` on the PR body.
- **Why transient outcomes are not committed.** The next invocation has no reason to trust a previous process's self-report; it re-derives state cold. A committed "blocked" would be a status the repo carries and a fact the next agent should verify anyway.
- **Why the coordinator is naive.** A coordinator that resolves state, reads artifacts, or restates briefs is an orchestrator growing back. Its whole job is dispatch, wait, repeat; the phase agent does the work and `IMPLEMENTATION.md` holds the state.
- **Why the driver is a Python tool under `tools/`.** `tools/cursor/` set the convention: Python 3.10+, no indexing step, each script runnable with `--help`, documented for a fresh agent. The Claude Agent SDK and Cursor's headless agent both have Python or subprocess surfaces; the provider layer is thin.
- **Rejected: a four-field trailer** (`Phase`, `Outcome`, `Boundary`, `Verify`). It mixed one durable fact with three transient ones and would have made the commit message a status record.
