---
name: execute
description: Execute an existing plan from `docs/plans/`. Use when the user wants to implement a planned work package — routing `refine`'s briefs to workers (or authoring one inline for single-worker slices), tracking implementation progressively, and running review sized to the declared posture.
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
- A finished change leaves its plan folder as a pile of interim artifacts nobody ever closes.

The job of this skill is to take a planned work package, confirm it is the right next executable slice, create a short implementation plan, get rightsized workers the briefs they need, keep the orchestrator context lean, run review appropriate to the declared posture, close the plan out, and land the work as a PR that mechanically points back at its plan folder.

## Working Model

Start from the requested plan folder and answer these questions before implementation:

- Does the plan folder contain a `PLAN.md` (and `DESIGN.md`, when the plan uses one) for this change?
- **Has `refine` run?** A `briefs/` directory plus an Execution Phases section that names brief files means the decomposition is already settled — your job is to route it, not to redo it.
- Are the contracts explicit enough in `DESIGN.md`, stable docs, or `PLAN.md` for delegated workers to implement against?
- Does the requested execution still align with current architecture docs and user intent?

If the plan no longer aligns with the architecture or user intent, stop execution and surface that mismatch. Plan problems return to a plan conversation before implementation continues. The plan folder and its PR are the authorities for sequencing.

The user has already chosen a plan/execute workflow. Treat that as evidence that the work is substantial enough to deserve main-thread orchestration and review sized to the posture below.

**Delegation is a judgment call, not a mandate.** Whether to delegate depends on harness capability (some harnesses have no subagents) and context economics: when the orchestrator's context is already hot with the plan — most notably in one-shot composition, where plan just ran in this same session — direct implementation of a small slice can beat paying a cold worker's spin-up cost. Keep the sizing ladder and recon-first method below intact regardless of which way the call goes, and keep the orchestrator from becoming an opportunistic implementor while workers it did dispatch are still running.

## Brief Routing and Authorship

**Plugin-wide invariant: context authors write once, in full, addressed to the consumer; orchestrators route verbatim, never paraphrase.** This skill is where the invariant is exercised for implementation work — and by default you are the router, not the author.

**When `refine` has run** (briefs exist and Execution Phases names them), routing is the whole job:

- Dispatch each worker with its brief routed verbatim plus mechanical pointers — repo path, branch, how to report back, and nothing else. Do not summarize the brief, restate the plan alongside it, or "add context" the brief already carries. If you find yourself explaining the brief, the brief is wrong; fix the brief, do not compensate in the prompt.
- Follow the dispatch list's dependencies. Units marked as running alongside each other own disjoint paths and may go in parallel; the rest wait.
- **Contradictions amend the brief.** When a worker reports a mismatch between its brief and the code or the plan, edit the brief file to record the resolution, then re-dispatch or continue from the amended brief. Never resolve a contradiction only in conversation — the amendment is the traceable record of where the decomposition was wrong, and the only thing a resumed run would see.

**When `refine` was skipped** (the single-worker case, or a slice small enough that refinement was ceremony), author inline at dispatch time while your context is hot with the plan: derive the brief from `PLAN.md`/`DESIGN.md` contracts, write it to `docs/plans/<NN>-<slug>/briefs/`, commit it, and route it. It carries the same anatomy `refine` uses — consumer, owned paths, required reading in order, the contract, done evidence, report-back shape, and the standing instruction to report contradictions rather than resolve them silently.

Guard against the failure mode: this is not "write more artifacts". A brief with no named consumer is ceremony. Do not write a brief for work you are about to do yourself.

## Sizing Method

`refine` owns decomposition when it runs; this section is for the case where it did not, and for judging whether it should have.

Do not size the work from the plan title alone. Start with a small recon pass, then decide how many workers the change actually needs.

- One implementation subagent: one bounded slice, one main contract, modest file surface, low ambiguity. This is the rung where skipping refinement is correct.
- Two to three small implementation subagents: clearly independent bounded slices, or one main slice plus one isolated supporting slice.
- Multiple larger or more capable subagents: only when the slices themselves are cross-cutting, ambiguous, or architecture-heavy.

If you cannot name the slices clearly, do not decompose further — keep the work in one implementation subagent. If the work clearly sits on rung two or three and no briefs exist, that is a signal the plan should have been refined: say so, and either run `refine` first or accept the inline-authorship cost knowingly.

## Optimization Method

Optimize for outcome quality per token, not for maximal autonomy or maximal parallelism.

- Keep the orchestrator context lean. It should hold control state, not duplicate implementation detail.
- Prefer phased execution by default: one plan folder or one executable slice at a time.
- Use the cheapest likely-successful worker available in the current environment for bounded implementation work.
- If the next meaningful step depends on worker output, wait for the worker. Do not let the orchestrator drift into doing the implementation itself while waiting.
- When a task is too large for one worker, prefer several small, clearly bounded workers over one larger agent, then consolidate their output yourself.

**Model allocation.** Starting allocations, not settled ones — configuration to tune as usage data justifies, not doctrine. Spend the quality premium where cognition pays and starve it where the work is rote.

- **Claude Code**: Haiku for research and small bounded changes, Sonnet for large or ambiguous changes. Opus only where directed.
- **Cursor**: Composer-2.5 unless specifically directed otherwise.
- **Codex**: GPT5.4 high for most work, mini for exploration, xhigh for review. Not 5.5.

Several small models with clearly bounded scope tend to be cheaper and faster in aggregate than one larger agent carrying the whole task — but only when the slices are genuinely independent, which is what the Sizing Method is for.

## Review Posture

Review posture is **declared by the invoker, never inferred** from context, harness, or change size. Absent a declaration, assume terminal.

- **Terminal** (default; no downstream review stage declared): run mandatory independent review via the `comprehensive-review` skill and write `REVIEW.md` into the plan folder.
- **Pipeline** (the invoker declares a downstream orchestrated review stage exists — e.g. a cursor automation that reviews the PR): the in-run review drops to a pre-flight self-verification instead — does it build/run, do the acceptance criteria pass locally, is the plan folder complete (`PLAN.md`, progressive `IMPLEMENTATION.md`, `briefs/`). The deep review happens downstream against the PR; do not write `REVIEW.md` from this skill in pipeline posture — that artifact belongs to the pipeline stage.

The user saying "skip review" is an invoker declaration of pipeline (or no-review) posture, not license to silently skip verification — pre-flight self-verification still runs.

## One-Shot Composition

When a single run does plan, refine, and execute back to back, each skill still runs as a separately dispatched context, and the handoff between them is the plan folder's committed artifacts, not the orchestrator's memory of the planning conversation. Execute reads the plan and the briefs cold, exactly as it would on a fresh session days later — a fused context destroys cold-read pressure on both.

## Workflow

1. Identify the target plan folder (`docs/plans/<NN>-<slug>/`) and, if the plan defines phases, the specific phase or slice to execute. Read `PLAN.md`, any `DESIGN.md`, and relevant stable docs cold from the committed artifacts — even immediately after a plan run in the same session (see One-Shot Composition).
2. Record run identity at the top of `IMPLEMENTATION.md` before implementation begins, and write the file now — do not wait until completion:
   ```
   ## Run
   - Tool: <opencode | Claude Code | Cursor | GitHub Copilot | cloud run>
   - Session/Run ID or session URL: <value>
   - Started: <ISO 8601 UTC timestamp>
   ```
   In a cloud/PR flow, record the session URL or run ID; there is no local transcript to point to. For local runs, the `transcript-parser` skill (lab) owns the per-harness formulas for locating a session.
3. Confirm this is the correct next slice: contracts are explicit enough for delegated workers, the execution still aligns with architecture and intent, and any prerequisite phases are satisfied per the plan's own ordering notes and the branch/PR state. If misaligned, stop and return to plan.
4. Do a short recon pass over the likely code surface, then create a lightweight implementation plan for the slice: goal, ordered activities, likely dependencies, decision points, done evidence, likely delegation points. When `refine` has run, its dispatch list already is this plan — read it rather than rebuilding it.
5. Decide execution shape using the Sizing Method and the delegation judgment call above. Do not create more workers than the slice names clearly support.
6. If delegating, get each worker its brief per Brief Routing and Authorship: route `refine`'s brief verbatim where one exists, author and commit one inline where it does not.
7. While workers run, keep orchestration state lean. If blocked on worker output, wait instead of absorbing their implementation work into the main thread.
8. As each slice or worker completes, synthesize its output and append to `IMPLEMENTATION.md` immediately — what was built, files or modules touched, tradeoffs, validation notes, and any intentional deviations from plan wording. Where briefs exist, record the outcome against its brief by name, so a resumed run can read the dispatch list and see which units are done. Never batch this to the end of the run; a killed run must leave the branch resumable from `IMPLEMENTATION.md` alone.
9. Verify the full slice against the plan.
10. Run review per the declared posture (Review Posture, above).
11. If terminal review finds high or critical issues that fit within scope and do not require architectural replanning, have a clean subagent resolve and self-review. Do not default to repeated external review loops unless the change is unusually risky or the user asks for it.
12. **Terminal posture only:** once review has settled and no `blocker`/`high` finding stands, close the plan out via the `close-out` skill — the last commit before the PR. In pipeline posture, do not close out: the downstream stage still needs `REVIEW.md` and `QA.md`, and close-out happens after the PR merges.
13. Push commits and open or update the PR with `Workflow-Plan: docs/plans/<NN>-<slug>/` as the first line of the PR body. Completion is the commits plus that marker.

## Run Artifacts

These exist for the duration of the run and its review. In terminal posture close-out consumes them; in pipeline posture the downstream stage consumes them and close-out follows the merge. Either way they are written as the work happens, not assembled at the end.

- `IMPLEMENTATION.md` (required, written progressively per step 8, never batched to the end)
  Run identity at the top; then what was built, what changed, files or modules touched, important tradeoffs, validation notes, and any intentional deviations from plan wording. In pipeline posture, also record the pre-flight self-verification results here as a subsection.
- `REVIEW.md` (terminal posture only)
  The independent review outcome, findings by severity, fixes applied, residual risks, and final assessment against the plan or contract. Not written by this skill in pipeline posture — that artifact is owned by the downstream pipeline stage.
- `briefs/` (whenever workers were dispatched)
  `refine`'s briefs, amended in place where workers reported contradictions, or the briefs this skill authored inline.

There is no separate status file. Partial or paused state must be recoverable from the branch alone — PRs and the tracker carry status; artifacts carry intent and outcome. **A resumed run reads the dispatch list in `PLAN.md`'s Execution Phases against `IMPLEMENTATION.md`'s recorded per-brief outcomes: units with a recorded outcome are done, the rest are the remaining work, and their briefs are already written.**

## Rules

- Execute only from an existing plan. Do not invent major scope during implementation.
- The plan folder and its PR are the authorities for sequencing and dependency checks.
- Contracts may come from `DESIGN.md`, stable docs, or `PLAN.md`. If they are too weak for delegated implementation, stop and fix plan first.
- Delegation is a judgment call weighing harness capability and context economics, not a default mandate — but when you do delegate, every worker gets a brief: `refine`'s routed verbatim, or one you authored inline.
- A worker's reported contradiction amends the brief file. Never resolve one silently or only in conversation.
- Prefer one clearly bounded worker over several weakly justified workers.
- Prefer phased execution unless the user asks for end-to-end work or the plan makes the coupling unusually strong.
- The orchestrator should not become an opportunistic implementor while workers are running.
- Review posture is declared by the invoker, never inferred; terminal posture runs mandatory independent review, pipeline posture runs pre-flight self-verification only.
- Write `IMPLEMENTATION.md` progressively as each slice completes, not at the end, recording each unit's outcome against its brief by name.
- Record what actually happened, so a resumed run recovers both intent and progress from the branch alone.
- In terminal posture, the run ends with close-out: the plan folder collapses to `PLAN.md` plus its Outcome section before the PR is opened. In pipeline posture, leave the artifacts in place — the stage needs them, and close-out happens after merge.
- Completion is commits pushed plus a PR body whose first line is `Workflow-Plan: docs/plans/<NN>-<slug>/`. Do not rename plan folders or maintain schedule docs.
