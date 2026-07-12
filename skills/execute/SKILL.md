---
name: execute
description: Execute an existing plan from `docs/plans/`. Use when the user wants to implement a planned work package with brief-based delegation, progressive implementation tracking, and review sized to the pipeline posture.
---

# Plan Execution

Use this skill to execute work that has already been planned in `docs/plans/`.

This skill exists to prevent common execution failures:

- Agents implement directly from prose without grounding themselves in the plan contracts.
- The main thread keeps too much implementation detail in its own context and becomes an expensive second implementor.
- Delegation happens without first sizing the task or confirming the work is the right next slice.
- Work is decomposed too early or too aggressively, causing orchestration overhead without real gain.
- Worker prompts are an orchestrator's paraphrase of the plan instead of the plan's own contracts, losing precision at each hop.
- Implementation finishes without review sized to whether anything downstream will look at it again.
- Inefficient agent allocation, giving small work to multiple large agents when one or two small models could have sufficed.
- A killed or paused run leaves nothing on the branch that a future agent could resume from.

The job of this skill is to take a planned work package, confirm it is the right next executable slice, create a short implementation plan, dispatch rightsized workers with authored briefs, keep the orchestrator context lean, run review appropriate to the declared posture, and land the work as a PR that mechanically points back at its plan folder.

## Working Model

Start from the requested plan folder and answer these questions before implementation:

- Does the plan folder contain a `PLAN.md` (and `DESIGN.md`, when the plan uses one) for this change?
- Are the contracts explicit enough in `DESIGN.md`, stable docs, or `PLAN.md` for delegated workers to implement against?
- Does the requested execution still align with current architecture docs and user intent?

If the plan no longer aligns with the architecture or user intent, stop execution and surface that mismatch. Plan problems return to a plan conversation before implementation continues. The plan folder and its PR are the authorities for sequencing now — there is no parent roadmap to consult.

The user has already chosen a plan/execute workflow. Treat that as evidence that the work is substantial enough to deserve main-thread orchestration and review sized to the posture below.

**Delegation is a judgment call, not a mandate.** Whether to delegate depends on harness capability (some harnesses have no subagents) and context economics: when the orchestrator's context is already hot with the plan — most notably in one-shot composition, where plan just ran in this same session — direct implementation of a small slice can beat paying a cold worker's spin-up cost. Keep the sizing ladder and recon-first method below intact regardless of which way the call goes, and keep the orchestrator from becoming an opportunistic implementor while workers it did dispatch are still running.

## Brief-Based Dispatch

**Plugin-wide invariant: context authors write once, in full, addressed to the consumer; orchestrators route verbatim, never paraphrase.** This skill is where the invariant is exercised for implementation work.

Mechanics:

- At dispatch time, while your context is hot with the plan, derive each worker's brief from `PLAN.md`/`DESIGN.md` contracts. Write it to `docs/plans/<NN>-<slug>/briefs/` and commit it — briefs are provenance and debugging truth; no future agent is required to read them to understand the change, but they must be there if one wants to.
- A worker's prompt consists of the routed brief plus mechanical pointers (repo path, branch, how to report back) — not an orchestrator summary of the plan.
- A brief names its consumer, its owned paths, required reading (in order), the contract it must satisfy, the done evidence that shows it satisfied it, and asks the worker to report contradictions between the brief and the underlying contracts rather than resolve them silently.
- Guard against the failure mode: this is not "write more artifacts." A brief with no named consumer is ceremony. The invariant is authorship plus verbatim routing; the brief file is just the medium. Do not write a brief for work you are about to do yourself.

## Sizing Method

Do not size the work from the plan title alone. Start with a small recon pass, then decide how many workers the change actually needs.

Use these proxies:

- How many files or modules must be read before the change is well-understood?
- Is the work implementing to one fixed contract or several interacting contracts?
- Is the work local to one subsystem or spread across multiple surfaces?
- Are there clearly independent slices that can proceed without waiting on each other?
- Is the change well-defined, or does it still contain meaningful ambiguity?
- Will verification be straightforward or cross-cutting?

Use this ladder:

- One implementation subagent: one bounded slice, one main contract, modest file surface, low ambiguity.
- Two to three small implementation subagents: clearly independent bounded slices, or one main slice plus one isolated supporting slice.
- Multiple larger or more capable subagents: only when the slices themselves are cross-cutting, ambiguous, or architecture-heavy.

If you cannot name the slices clearly, do not decompose further. Keep the work in one implementation subagent.

## Optimization Method

Optimize for outcome quality per token, not for maximal autonomy or maximal parallelism.

- Keep the orchestrator context lean. It should hold control state, not duplicate implementation detail.
- Prefer phased execution by default: one plan folder or one executable slice at a time.
- Use the cheapest likely-successful worker available in the current environment for bounded implementation work.
- If the next meaningful step depends on worker output, wait for the worker. Do not let the orchestrator drift into doing the implementation itself while waiting.
- When a task is too large for one worker, prefer several small, clearly bounded workers over one larger agent, then consolidate their output yourself.

Per-harness model-selection hints and session-ID capture formulas live in `reference.md` — they rot fast and are environment configuration, not orchestration doctrine. Not loaded during normal cloud execution; consult it for local runs or when tuning worker allocation.

## Review Posture

Review posture is **declared by the invoker, never inferred** from context, harness, or change size. Absent a declaration, assume terminal.

- **Terminal** (default; no downstream review stage declared): run mandatory independent review via the `comprehensive-review` skill, as today, and write `REVIEW.md` into the plan folder.
- **Pipeline** (the invoker declares a downstream orchestrated review stage exists — e.g. a cursor automation that reviews the PR): the in-run review drops to a pre-flight self-verification instead — does it build/run, do the acceptance criteria pass locally, is the plan folder complete (`PLAN.md`, progressive `IMPLEMENTATION.md`, `briefs/`). The deep review happens downstream against the PR; do not write `REVIEW.md` from this skill in pipeline posture — that artifact belongs to the pipeline stage.

The user saying "skip review" is an invoker declaration of pipeline (or no-review) posture, not license to silently skip verification — pre-flight self-verification still runs.

## One-Shot Composition

When a single run does plan then execute back to back, each skill still runs as a separately dispatched context, and the handoff between them is the plan folder's committed artifacts, not the orchestrator's memory of the planning conversation. Execute reads the plan cold, exactly as it would on a fresh session days later — that cold read is load-bearing (see `DESIGN.md`'s Plugin Partition contract).

## Workflow

1. Identify the target plan folder (`docs/plans/<NN>-<slug>/`) and, if the plan defines phases, the specific phase or slice to execute. Read `PLAN.md`, any `DESIGN.md`, and relevant stable docs cold from the committed artifacts — even immediately after a plan run in the same session (see One-Shot Composition).
2. Record run identity at the top of `IMPLEMENTATION.md` before implementation begins, and write the file now — do not wait until completion:
   ```
   ## Run
   - Tool: <opencode | Claude Code | Cursor | GitHub Copilot | cloud run>
   - Session/Run ID or session URL: <value>
   - Started: <ISO 8601 UTC timestamp>
   ```
   In a cloud/PR flow, record the session URL or run ID; there is no local transcript to point to. For local runs where the `transcript-parser` skill needs a session ID, see `reference.md` for best-effort per-harness capture formulas.
3. Confirm this is the correct next slice: contracts are explicit enough for delegated workers, the execution still aligns with architecture and intent, and any prerequisite phases are satisfied per the plan's own ordering notes and the branch/PR state — not a roadmap. If misaligned, stop and return to plan.
4. Do a short recon pass over the likely code surface, then create a lightweight implementation plan for the slice: goal, ordered activities, likely dependencies, decision points, done evidence, likely delegation points.
5. Decide execution shape using the Sizing Method and the delegation judgment call above. Do not create more workers than the slice names clearly support.
6. If delegating, dispatch each worker with a brief per Brief-Based Dispatch: derive it from the plan's contracts, commit it to `briefs/`, and route it verbatim plus mechanical pointers.
7. While workers run, keep orchestration state lean. If blocked on worker output, wait instead of absorbing their implementation work into the main thread.
8. As each slice or worker completes, synthesize its output and append to `IMPLEMENTATION.md` immediately — what was built, files or modules touched, tradeoffs, validation notes, and any intentional deviations from plan wording. Never batch this to the end of the run; a killed run must leave the branch resumable from `IMPLEMENTATION.md` alone.
9. Verify the full slice against the plan.
10. Run review per the declared posture (Review Posture, above).
11. If terminal review finds high or critical issues that fit within scope and do not require architectural replanning, have a clean subagent resolve and self-review. Do not default to repeated external review loops unless the change is unusually risky or the user asks for it.
12. Push commits and open or update the PR with `Workflow-Plan: docs/plans/<NN>-<slug>/` as the first line of the PR body. Completion is the commits plus that marker — no folder renaming, no roadmap edits.

## Required Completion Artifacts

- `IMPLEMENTATION.md` (required, written progressively per step 8, never batched to the end)
  Run identity at the top; then what was built, what changed, files or modules touched, important tradeoffs, validation notes, and any intentional deviations from plan wording. In pipeline posture, also record the pre-flight self-verification results here as a subsection.
- `REVIEW.md` (terminal posture only)
  The independent review outcome, findings by severity, fixes applied, residual risks, and final assessment against the plan or contract. Not written by this skill in pipeline posture — that artifact is owned by the downstream pipeline stage.
- `briefs/` (whenever workers were dispatched)
  Every brief a worker was actually given, committed for provenance.

There is no separate status file. Partial or paused state must be recoverable from progressive `IMPLEMENTATION.md` alone — a status artifact violates "nothing carries status" (see `DESIGN.md`'s Artifact Taxonomy).

## Rules

- Execute only from an existing plan. Do not invent major scope during implementation.
- The plan folder and its PR are the authorities for sequencing and dependency checks.
- Contracts may come from `DESIGN.md`, stable docs, or `PLAN.md`. If they are too weak for delegated implementation, stop and fix plan first.
- Delegation is a judgment call weighing harness capability and context economics, not a default mandate — but when you do delegate, rightsize the number and capability of workers after a small recon pass, and author each worker's brief yourself per Brief-Based Dispatch.
- Prefer one clearly bounded worker over several weakly justified workers.
- Prefer phased execution unless the user asks for end-to-end work or the plan makes the coupling unusually strong.
- The orchestrator should not become an opportunistic implementor while workers are running.
- Review posture is declared by the invoker, never inferred; terminal posture runs mandatory independent review, pipeline posture runs pre-flight self-verification only.
- Write `IMPLEMENTATION.md` progressively as each slice completes, not at the end.
- Record what actually happened in completion artifacts so future agents can recover both intent and implementation history from the plan folder alone.
- Completion is commits pushed plus a PR body whose first line is `Workflow-Plan: docs/plans/<NN>-<slug>/`. No folder renaming, no roadmap edits — none exist to update.
