---
name: execute
description: Execute an existing plan program or child plan from `docs/plans/`. Use when the user wants to implement a planned work package with delegation, progress tracking, completion artifacts, and mandatory review.
---

# Plan Execution

Use this skill to execute work that has already been planned in `docs/plans/`.

This skill exists to prevent common execution failures:

- Agents implement directly from prose without grounding themselves in the plan contracts.
- The main thread keeps too much implementation detail in its own context and becomes an expensive second implementor.
- Delegation happens without first sizing the task or confirming the work is the right next slice.
- Work is decomposed too early or too aggressively, causing orchestration overhead without real gain.
- Implementation finishes without an independent review pass.
- Inefficient agent allocation, giving small work to multiple large agents when one or two small models could have sufficed
- Completed work loses provenance because the execution trace is not written back into the plan folder and roadmap status is not synchronized.

The job of this skill is to take a planned work package, confirm that it is the right next executable slice, create a short implementation plan, rightsize implementation subagents, keep the orchestrator context lean, run mandatory review after implementation, and write completion artifacts back into the relevant plan folder.

## Working Model

Start from the requested plan program or child plan and answer these questions before implementation:

- Is this work inside an open `[NEW]-*` parent program?
- Does the parent `ROADMAP.md` indicate prerequisites, ordering constraints, or coordinated slices that affect execution?
- Are the contracts explicit enough in `DESIGN.md`, stable docs, or `PLAN.md` for delegated workers to implement against?
- Does the requested execution still align with current architecture docs and user intent?

If the plan no longer aligns with the architecture, roadmap, or user intent, stop execution and surface that mismatch. Plan problems should return to a plan conversation before implementation continues.

The user has already chosen a plan/execute workflow. Treat that as evidence that the work is substantial enough to deserve:

- main-thread plan and orchestration
- delegated implementation work
- independent review

Even the smallest planned change should normally be given to at least one implementation subagent, because the main thread is typically the most expensive place to hold detailed implementation context.

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
- Prefer phased execution by default: one child plan or one executable slice at a time.
- Use the cheapest likely-successful worker available in the current environment for bounded implementation work.
- Let the environment determine the exact worker type or model choice. Choose based on task shape, not on a hardcoded provider rule.
- Escalate worker capability when the slice is genuinely ambiguous, cross-cutting, or has already failed for capability reasons.
- If the next meaningful step depends on worker output, wait for the worker. Do not let the orchestrator drift into doing the implementation itself while waiting.

Hints for subagent selection:
 - For typical small bounded work, a low cost, fast model like GPT mini or Haiku or Composer 2/Kimi (e.g if running in Cursor) with high effort where possible, is more cost effective than a larger model.
 - Several small models with clear bounded scope are cheaper and faster than one larger agent with union scope
 - However, decomposition into those smaller agents depends on the work being able to be cleanly sliced. If it can't, then keep it together and use a larger agent.
 - Review agents require cross-cutting context, requiring larger models with greater effort budgets.

## Workflow

1. Identify the target parent program and child plan to execute.
1a. Capture the current session ID and write the Session section to IMPLEMENTATION.md before implementation begins. This lets the `transcript-parser` skill locate this session reliably after execution completes.
   - opencode: read `OPENCODE_RUN_ID` from the environment. If `OPENCODE` is set, use this as the session ID directly.
   - Claude Code: find the most recently-modified `.jsonl` in `~/.claude/projects/{project-hash}/` and read `sessionId` from any line. Project hash = working directory path with `/` replaced by `-`, prefixed with `-`.
   - Cursor: find the most recently-modified directory under `~/.cursor/projects/{project-name}/agent-transcripts/` and use its name as the session ID.
   - Write to IMPLEMENTATION.md at the top before filling in other content:
     ```
     ## Session
     - Tool: <opencode | Claude Code | Cursor | GitHub Copilot>
     - Session ID: <uuid>
     - Started: <ISO 8601 UTC timestamp>
     ```
2. Read the parent `PLAN.md`, `ROADMAP.md`, and any relevant `DESIGN.md`, plus the child `PLAN.md` and any child `DESIGN.md`.
3. Confirm that prerequisites are satisfied and that this is the correct next slice according to the roadmap.
4. If the plan needs architectural revision, unclear contract changes, or roadmap reshaping, stop and return to plan rather than improvising execution.
5. Do a short recon pass over the likely code surface, then create a lightweight implementation plan for the slice:
   - goal
   - ordered activities
   - likely dependencies
   - decision points
   - done evidence
   - likely delegation points
6. Decide how many implementation subagents are justified. Default to at least one implementation subagent. Do not create more workers than the slice names clearly support.
7. Delegate implementation. Workers should own explicit files, modules, or bounded responsibilities and implement against explicit contracts rather than vague prose summaries.
8. While workers run, keep orchestration state lean. If blocked on worker output, wait instead of absorbing their implementation work into the main thread.
9. Synthesize worker outputs, complete any remaining orchestration or integration work, and verify the slice against the plan.
10. Do not self-review as the only review. Run a mandatory comprehensive review after implementation using the `comprehensive-review` skill.
11. If review finds high or critical issues that fit within scope and do not require architectural replanning, have a clean subagent resolve and self-review. Do not default to repeated external review loops unless the change is unusually risky or the user asks for it.
12. Write completion artifacts into the executed child plan folder.
13. Update the relevant `ROADMAP.md` status to reflect reality.
14. If the parent program is now fully implemented, write parent-level completion artifacts and rename the parent from `[NEW]-...` to the next numeric provenance prefix, updating headings and titles as well.

## Required Completion Artifacts

Each executed child plan should gain:

- `IMPLEMENTATION.md`
  Session section (tool name, session ID, start timestamp) at the top; then: what was built, what changed, files or modules touched, important tradeoffs, validation notes, and any intentional deviations from plan wording.
- `REVIEW.md`
  The independent review outcome, findings by severity, fixes applied, residual risks, and final assessment against the plan or contract.

When useful, execution may also add:

- `STATUS.md`
  Current state if execution is partial or paused across sessions.

If the parent program is completed as a whole, add analogous parent-level completion artifacts before renaming it to a numeric prefix.

## Rules

- Execute only from an existing plan. Do not invent major scope during implementation.
- The parent roadmap is the authority for sequencing and dependency checks.
- `[NEW]-` parents are the live execution backlog. Numbered parents are implemented provenance and should not be reopened casually.
- Contracts may come from `DESIGN.md`, stable docs, or `PLAN.md`. If they are too weak for delegated implementation, stop and fix plan first.
- Use delegated implementation by default for plan/execute work, but rightsize the number and capability of workers after a small recon pass.
- Prefer one clearly bounded worker over several weakly justified workers.
- Prefer phased execution unless the user asks for end-to-end work or the plan makes the coupling unusually strong.
- The orchestrator should not become an opportunistic implementor while workers are running.
- Mandatory independent review is part of execution, not optional cleanup.
- Record what actually happened in completion artifacts so future agents can recover both intent and implementation history.
- Keep `ROADMAP.md` status accurate as execution progresses or completes.
- Only rename a parent program to a numeric prefix when the program is fully implemented and its provenance artifacts have been written.
