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

The **shared fact** is phase closure: the commit that closes a phase carries a trailer naming the plan and the phase. "Which phase is open" becomes a pure function of the branch's git log and `DESIGN.md`'s phase list, readable by anything, no model required. Everything transient — incomplete, unsuccessful and why, verification outcome — stays a live return value of the run that produced it and is never written to the repo.

The **agent-orchestrated path** is the existing workflow, tightened: `execute` runs one phase, closes it with the trailer, and stops. It never dispatches its own successor, under any invocation. A bare call simply stops there; a coordinator — a context that has done no phase work, instructed to run the design through — dispatches each phase's `execute` as a subagent, holds only its report, and repeats; where nesting is not available, it holds and names the next phase, the same as a bare call. It does not read artifacts, resolve state, or mimic the driver.

The **driver path** is a tool in the plugin, `tools/driver/`, run by a person or by an agent holding the keys, over two front ends: a CLI that owns the loop itself, and an MCP server that exposes the same primitive one phase at a time to a calling agent session. Given a plan folder it resolves the open phase from git, runs one phase agent in a fresh session through a provider (Claude Agent SDK or Cursor's headless agent, chosen by the key present in the environment), reads the agent's structured report, and — under the CLI — repeats until the run is done or a report says stop; under MCP, returns after one phase and leaves the loop to the caller. A run that ends without a report is not a special case: the driver re-dispatches once, and the fresh agent does what a resuming human does — reads the committed artifacts, finishes or reports honestly. The driver never commits; every commit on the branch is a phase agent's.

The driver is built to test and validate the fresh-orchestrator-per-phase economics, not to replace the agent-orchestrated path, which remains the default and must keep working without any SDK present.

### Domain: Phase closure

- Owns: the meaning of "this phase is closed", and the resolution of the open phase. Owned by `execute`.
- Contract:
  - A phase is closed by the **closing commit**: the one commit carrying the git trailer `Workflow-Phase: <slug>:<n>`, where `<slug>` is the plan folder's slug and `<n>` the 1-based phase index in `DESIGN.md`. Normally it is the commit that closes the phase record in `IMPLEMENTATION.md` with its verification result and Carried section. A re-dispatched agent that finds the record closed and verified but no trailer closes with a trailer-only commit. The trailer is the attestation that the phase was verified and accepted; it appears on no other commit.
  - The run ends with the **done commit**: the commit carrying `Workflow-Phase: <slug>:done`. Terminal posture: the close-out commit. Pipeline posture: the commit that records pre-flight in `IMPLEMENTATION.md`. Pushing and opening the PR follow it and are idempotent.
  - Resolution reads the branch's own commits (`<default>..HEAD`), never merged-in history. With `N` = the count of `### Phase` headings in `DESIGN.md`, the **open phase** is the lowest `n` in `1..N` with no trailer. When every `n` has one and there is no `done` trailer, the run is in **wrap-up**. With `done`, the run is **done**. A malformed trailer never counts.
  - A bounce after any closure revises only phases above the highest closed index; `N` never drops below it.
  - The trailer is commit metadata in the same class as the PR body's `Workflow-Plan:` marker: a mechanical locator, immutable per commit, not a status field in an artifact. Invariant 3 ("nothing in the repo carries status") is unchanged.
- Non-goals: unit-level progress (that is `IMPLEMENTATION.md`'s per-unit record, read by agents, not by the driver); anything transient (incomplete, unsuccessful, and why); the presence or absence of files in the folder — briefs stay until `close-out`, and nothing is inferred from them; a phase that was attempted and not closed leaves no trace beyond its ordinary commits.

### Domain: Phase report

- Owns: the one-shot signal from a phase run to whatever invoked it. Owned by the phase agent (`execute`).
- Contract:
  - A phase run ends with one report: `status` ∈ `closed | incomplete | unsuccessful`, `phase: <n> | done`, `reason` (free text, required for anything but `closed`). `closed` means the closing commit (or the done commit) exists on the branch. `unsuccessful` covers every case where the run stopped without closing and the next step needs a decision only a human or the design conversation can make — an approach-open phase, a design that no longer matches the architecture, a `refine`/`execute` bounce with Open Questions written, retries exhausted. The specific reason travels in `reason`, not in the status: nothing downstream branches differently on which kind of unsuccessful it was, so the status stays one value and the content stays prose. `incomplete` means the run's final output had no report block at all; it is not diagnosed, it is re-dispatched once, and a second incomplete is treated as `unsuccessful`. `closed` takes precedence: a run that closed and then stopped reports `closed`.
  - The wire format is provider-independent: the run's final output contains exactly one fenced block tagged `workflow-report` holding a JSON object with those three fields. Under the driver it is read from the provider's result; under the agent-orchestrated path it is the subagent's returned report. It is never written to the repo and never trusted across a process boundary — the next invocation re-derives state from Phase closure.
- Non-goals: carrying state between runs; the driver's own bookkeeping (re-dispatch count, per-phase cost), which lives in the driver process and its output; a taxonomy of *why* a run was unsuccessful — that is `reason`'s job, not the status enum's.

### Domain: Driver

- Owns: `tools/driver/`; the loop; provider selection; the reduced tool surface each phase agent runs with. Owned by the plugin.
- Contract:
  - Invocation: `python3 tools/driver/run.py <plan-folder> [--provider claude|cursor] [--review terminal|pipeline] [--max-redispatch N]`, from a checkout on the plan's branch. Provider defaults to whichever key is present in the environment (`ANTHROPIC_API_KEY`, `CURSOR_API_KEY`); both present requires `--provider`; neither is an error before any run starts.
  - Loop: resolve (Phase closure) → **done**: exit 0 → **open phase `n`**: run one phase agent in a fresh session for phase `n`, the declared review posture → **wrap-up**: run one phase agent told that every phase is closed and only `execute`'s after-last-phase path remains → read the report → `closed`: loop; `unsuccessful`: print the report, exit non-zero; `incomplete`: re-dispatch once, then treat as `unsuccessful`.
  - Each phase agent is a fresh session: no resume, no carried transcript. Its prompt is the plan folder path, the branch, the phase or wrap-up, the review posture, and the instruction to run `execute`; the skill content is what it reads, not what the driver restates.
  - Reduced surface: file read and write, shell for git and the phase's verification, and subagent dispatch. No web, no MCP servers. Subagents the phase agent dispatches get their own surfaces; restricting the coordinator does not restrict its workers.
  - Provider interface: `run_phase(plan, phase, postures) -> Report | None`. One provider per SDK; the loop is provider-agnostic. Each provider reports the run's turns and cost where its SDK exposes them, and the driver prints them per phase — that is the measurement the tool exists to take.
  - The driver never writes to the repo. Every commit is the phase agent's; the driver's state is its stdout and exit code.
  - **Transport.** The resolve → dispatch-one-phase → read-report primitive backs two front ends, both calling the same provider layer. The CLI (`run.py`) owns the loop itself and defaults to running the plan to completion or first `unsuccessful`. An MCP server (stdio) exposes the same primitive — `status` (resolve, read-only), `trigger_phase` (dispatch one phase agent), `poll` (check an in-flight dispatch) — to a calling agent session instead, most usefully a cloud agent that ran `design` and is the natural escalation target for anything `unsuccessful`. The MCP front end defaults to **one phase per call**, not the CLI's run-to-completion: it dispatches, returns, and leaves the loop — continue, retry, escalate — to the calling session, which decides per its own `closed | incomplete | unsuccessful` read of the report. This bounds any single background span under MCP to one phase's run rather than the whole design.
  - Whether a next phase runs after `closed` is never a flag the driver reads or writes — it is a property of which front end is loop-owning: the CLI loops by default, the MCP front end returns after one phase by default. Same as the agent-orchestrated path (Naive coordination, below): nothing is declared, only invoked.
- Non-goals: running `design` (a conversation, not a phase); running review or close-out itself (`execute` owns those after the last phase); merging; retrying beyond one re-dispatch; any repo-side status; keeping the MCP server process alive across its host session's own lifetime — a phase agent dispatched via MCP and orphaned by its host container dying mid-run is the same unresolved case as an agent-orchestrated subagent dying mid-phase (Phase closure's cold-read gap), not a new one.

### Domain: Naive coordination

- Owns: what happens after one phase closes, in the agent-orchestrated path. Owned by `execute`'s skill text.
- Contract: `execute` always stops at its closing commit and reports; it never dispatches the next phase itself. Whether another phase runs next is not a posture `execute` checks or a flag declared to it — it is a property of the invocation, exactly as under the driver (Domain: Driver, Transport): a bare `execute` call has nothing dispatching a successor and simply stops; a **coordinator** — the context that invoked the first `execute` and has done no phase work, instructed to run the design through completion — dispatches `execute` for each phase in series as a subagent with the declared review posture, holding nothing but each report, and repeats on `closed`. On anything else (`incomplete` after its one re-dispatch, or `unsuccessful`) it stops and relays the report, unresolved. Where the harness has no subagent nesting, the coordinator holds after one phase and names the next — the same behaviour as a bare call, because there is nothing to nest into, not a distinct declared state. The coordinator does not resolve state, read artifacts, or restate briefs.
- Non-goals: parity with the driver; provider selection; cost measurement; a `hold`/`continue` posture — see Architectural Implications.

## Architectural Implications

- `docs/ARCHITECTURE.md` **phase boundary** contract gains the closing commit, the done commit, and resolution. `hold`/`continue` is dropped as a named posture in the **Postures** table: `execute` always stops at its closing commit, and whether a next phase runs is a property of which invocation dispatched it — a bare call, a coordinator instructed to run to completion, or the driver's CLI vs. MCP front end (Domain: Driver, Transport) — not a flag declared to `execute` or read back from a report.
- `execute`'s after-last-phase path gains one statement: invoked when every phase is closed, it runs only that path and ends with the done commit.
- `docs/OVERVIEW.md` gains the driver as a third element beside the skills, with its posture: default path is agent-orchestrated; the driver is optional and needs a key.
- Principle 8 stands. The trailer is the second mechanical marker after `Workflow-Plan:`; `workflow-tuning/principles.md` should say so where it discusses the marker, so the precedent is named rather than rediscovered.
- The Cursor provider's exact headless surface could not be verified from this environment (cursor.com is not reachable here). Its shape — a subprocess or API call that runs one agent in a checkout and returns its final output as text — is settled, and the report format depends on nothing more than that; `refine` grounds the flags when it briefs that phase.
- Phase 3 is the natural first subject for the phase-2 driver: build the Cursor provider by driving it with the Claude provider. That is a sequencing choice for the invoker, not a requirement.

## Decisions

- **Two paths, distinct.** The agent-orchestrated path stays light and naive and is the default; the driver is built to test and validate, not to replace it.
- **One trailer, not a status block.** Closure is the single durable fact (`Workflow-Phase: <slug>:<n>`); everything transient — incomplete, unsuccessful, and why, and verification outcome — travels only as the run's report. An earlier four-field trailer was rejected for putting transient state in the durable channel.
- **Trailer key: `Workflow-Phase:`.** Confirmed at the checkpoint, sitting beside the existing `Workflow-Plan:` PR marker under one namespace.
- **Briefs stay until `close-out`.** Reverses the user's proposal that the closing commit cleans up the phase's briefs, on the adversarial pass's finding: removal would make `briefs/` a second encoding of phase state that can drift from the trailer, leave the Units list in `DESIGN.md` citing paths a re-dispatched agent cannot read, and force `close-out` and PR-seam changes for no gain since `close-out` already deletes the folder — still for confirmation at the checkpoint.
- **The run has a closure too.** A `done` trailer on the commit that ends the after-last-phase path, so wrap-up is resolvable cold and a run that dies between the last phase and the PR is re-dispatched rather than reported finished.
- **No `hold`/`continue` posture.** Whether a next phase runs is a property of the invocation (bare call, coordinator told to run to completion, driver CLI vs. MCP), never a flag declared to or read from `execute`. `execute` always stops at its closing commit; nothing else changes between what used to be called `hold` and `continue`.
- **Report status is three values, not four.** `closed | incomplete | unsuccessful`. `held`, `bounced`, and `blocked` collapsed into `unsuccessful`: nothing downstream ever branched differently on which of the three it was — the driver's loop printed and exited non-zero on all three identically — so the distinction was semantic labelling of the reason, not a functional state. The reason moves to the report's free-text `reason` field.
- **The report is a fenced block in final output.** Provider-independent, so the Cursor provider needs no custom-tool hook and no repo write.
- **Incomplete means re-dispatch.** No diagnosis of why a run did not report; a fresh agent reads the committed state and finishes or reports. Bound: one re-dispatch, matching `execute`'s own one-retry rule.
- **Provider by key.** The provider is chosen by which key the environment holds; an explicit flag overrides.
- **The driver never commits.** All repo writes are the phase agent's.
- **The driver also runs as an MCP server.** Same resolve/dispatch/report primitive, a second front end. CLI defaults to looping to completion; MCP defaults to one phase per call, returning to let the calling agent session (e.g. a cloud agent that ran `design`) hold the loop and decide next/retry/escalate. Bounds any MCP-hosted background span to one phase. A phase dispatched via MCP and orphaned by its host container dying mid-run is the same unresolved cold-read gap as a dead subagent under the coordinator, not a new failure mode — tracked, not solved, here.

## Assumption Ledger

None — see PROVENANCE.md.

## Open Questions

- MCP host lifetime: a cloud agent's container can be reclaimed mid-phase, orphaning the dispatched phase agent. Local/CLI use avoids this because the host is the invoker's own machine, kept up for the run's duration. Deferred; noted in Phase 4.

## Phases

### Phase 1 — Closure is deterministic

- Outcome: on a branch carrying plan `<slug>` with phases 1..k closed by `execute`, `git log <default>..HEAD --format='%(trailers:key=Workflow-Phase,valueonly)'` lists exactly `<slug>:1` … `<slug>:k`, each on the commit that closed that phase's record in `IMPLEMENTATION.md`, and after the after-last-phase path `<slug>:done` on the commit that ended it; `execute` stops at its closing commit and reports on every invocation, never dispatching a successor itself; and a coordinator instructed to run the design to completion, in a harness with subagent nesting, dispatches each phase in series holding only reports, while without nesting it holds and names the next phase — the same behaviour either way, since nothing is declared to `execute`, only invoked around it.
- Surfaces: `skills/execute/SKILL.md` (Outcome of a phase, Boundary, After the last phase), `docs/ARCHITECTURE.md` (phase boundary, Postures), `docs/OVERVIEW.md`, `plugins/workflow-lab/skills/workflow-tuning/principles.md` (#8 precedent).
- Approach: known
- Depends on: nothing

### Phase 2 — The driver runs a design with Claude

- Outcome: `python3 tools/driver/run.py docs/plans/<NN>-<slug>/` in a checkout with `ANTHROPIC_API_KEY` set, against a signed-off design with two or more phases, runs each open phase and then wrap-up in fresh sessions, prints each run's report with its turns and cost, and exits 0 with every phase's closing commit and the done commit on the branch — or exits non-zero at the first `unsuccessful` report, or after one re-dispatch of an `incomplete` run. Re-run on a done branch, it exits 0 without starting a session. `git log` shows no commit authored by the driver.
- Surfaces: `tools/driver/` (new: `run.py`, `providers/claude.py`, `README.md`), `docs/OVERVIEW.md` (the tool's entry).
- Approach: known
- Depends on: Phase 1

### Phase 3 — The driver runs a design with Cursor

- Outcome: the same command with `CURSOR_API_KEY` set (or `--provider cursor`) runs a phase through Cursor's headless agent and yields a report of the same shape; a design whose phase 1 was closed under Cursor and phase 2 under Claude shows no difference to the driver or in the branch beyond the run identity in `IMPLEMENTATION.md`.
- Surfaces: `tools/driver/providers/cursor.py`, `tools/driver/README.md`.
- Approach: known
- Depends on: Phase 2

### Phase 4 — The driver runs over MCP

- Outcome: `tools/driver/mcp_server.py` run as a stdio MCP server exposes `status` (resolve the open phase, read-only), `trigger_phase` (dispatch one phase agent for the currently open phase or wrap-up, default one phase per call), and `poll` (check an in-flight dispatch); a calling agent session against a signed-off, multi-phase design can drive the run to completion one `trigger_phase` call at a time, reading `closed | incomplete | unsuccessful` off each result exactly as the CLI's loop does, with no commit authored by the server. Container death mid-dispatch is named as a known, unresolved case (Open Questions) rather than silently handled.
- Surfaces: `tools/driver/mcp_server.py` (new), `tools/driver/README.md`.
- Approach: open — the primitive is known (it is Phase 2/3's provider layer, unchanged); what "handle an orphaned dispatch" means once the container-lifetime question is researched is not.
- Depends on: Phase 2

## Provenance Notes

- **Why not a schedule or a CI job.** A Routine or cron fires independently of a phase closing, so it is either idle or late, and cannot chain phases. A CI job that waits for closure holds a runner open for the whole run. The driver is causal: the next phase runs because the last one reported `closed`, and the process lives only as long as one phase.
- **Why not resume the SDK session.** Resume is the thing the loop exists to avoid: it carries the previous phase's context into the next. Cold read per phase is the invariant; the SDK makes it a mechanism instead of a discipline.
- **Why the trailer is not a status field.** Status fields drift because they restate something else and must be kept in sync. The trailer restates nothing: it is the act of closing, on the commit that closed. It cannot be stale, and it cannot be edited without rewriting history. That is the same reasoning that admits `Workflow-Plan:` on the PR body.
- **Why transient outcomes are not committed.** The next invocation has no reason to trust a previous process's self-report; it re-derives state cold. A committed "unsuccessful" would be a status the repo carries and a fact the next agent should verify anyway.
- **Why the coordinator is naive, and why it is not `execute`.** A coordinator that resolves state, reads artifacts, or restates briefs is an orchestrator growing back. So is a phase-1 orchestrator that dispatches phase 2 and waits: it holds the phase-1 build for the whole run, which is exactly the lifetime the loop exists to bound. The coordinator's whole job is dispatch, wait, repeat, from a context that never did phase work; the phase agent does the work and `IMPLEMENTATION.md` holds the state.
- **Why the run has its own trailer.** Without it, "every phase closed" is indistinguishable from "finished": terminal close-out deletes the folder the resolver counts phases in, and a run that dies after the last phase but before the PR would be reported done. The done commit is the same kind of fact as a closing commit — the act, on the commit that did it.
- **Why briefs are not removed at closure.** `close-out` already deletes the folder, `IMPLEMENTATION.md` already says which units are done, and `refine`'s Units list cites brief paths by name. Removing briefs earlier would add a file-presence signal that can disagree with the trailer, which is the drift principle 8 exists to prevent.
- **Why the report is text, not a tool.** Every provider returns final output; not every provider offers a custom-tool hook. A fenced block in final output is the smallest contract both SDKs can meet, and it keeps the report out of the repo without depending on either SDK's surface.
- **Why the driver is a Python tool under `tools/`.** `tools/cursor/` set the convention: Python 3.10+, no indexing step, each script runnable with `--help`, documented for a fresh agent. The Claude Agent SDK and Cursor's headless agent both have Python or subprocess surfaces; the provider layer is thin.
- **Rejected: a four-field trailer** (`Phase`, `Outcome`, `Boundary`, `Verify`). It mixed one durable fact with three transient ones and would have made the commit message a status record.
- **Why `held`/`bounced`/`blocked` collapsed to `unsuccessful`.** The driver's own loop already handled all three identically — print the report, exit non-zero — and nothing else in the design branched on which one it was. A status value that never drives a different decision is decorative; the reason it exists to convey belongs in `reason`, the same free-text channel a unit's failure message already uses back to its phase orchestrator. Distinguishing report-level statuses from prose content this way is the same reasoning applied one layer down when a unit fails: no schema, just a message, because the coordinator's decision space (retry, or hand to a human) doesn't change with the detail.
- **Why `hold`/`continue` is not a posture.** Checked against the driver: it has no such flag, and running it at all already commits to looping until done or `unsuccessful` — there was never a choice to declare. The same is true one layer up: a bare `execute` call stops because nothing dispatches a successor, and a coordinator loops because it was told to run the design through, not because either read a `hold`/`continue` value. The posture language described the invocation, not a state the system held; removing it removes a false degree of freedom, and incidentally removes the `hold`/`held` name collision the report-status enum had with it.
- **Why the driver also runs over MCP, and why it defaults to one phase.** A cloud agent that ran `design` is the natural home for escalation (`unsuccessful`) and for `design` itself on a bounce — both are conversations, not phases, and both already have to happen somewhere with model context. Exposing the driver's dispatch-one-phase primitive to that session, rather than only a batch CLI, lets the same session that designed the work also coordinate and escalate it. Defaulting to one phase per call, rather than mirroring the CLI's full loop, bounds the background span of any one MCP tool call to a single phase's run — relevant because a cloud agent's host container can be reclaimed on a timeline the driver doesn't control, unlike a human's own terminal running the CLI.
