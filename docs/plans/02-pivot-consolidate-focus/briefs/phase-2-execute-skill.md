# Brief: Phase 2 — Execute skill revision

Consumer: the implementation worker for Phase 2. Owned paths: `skills/execute/**` only. Do not touch any other file. Do not run git commit or push — leave changes in the working tree.

## Required reading, in order

1. `docs/plans/02-pivot-consolidate-focus/PLAN.md` — the model (section "The Model" is binding; its 7 decisions are settled)
2. `docs/plans/02-pivot-consolidate-focus/DESIGN.md` — binding contracts, especially "PR Artifact Seam", "Briefs Invariant", and "Plugin Partition"
3. `skills/execute/SKILL.md` — what you are revising

## Goal

Revise the execute skill to the new model: brief-based dispatch, progressive IMPLEMENTATION.md, parameterized review posture, delegation as a judgment rather than a mandate, and the local-harness/model-table payloads moved out of the skill body. The orchestration discipline (lean context, sizing ladder) stays — it is the skill's core value.

## Changes

### Remove (the backlog)

- ROADMAP status-sync steps and rules; `[NEW]-` parent checks; the parent-renaming-to-numeric-prefix completion ceremony; "parent roadmap is the authority for sequencing" (the plan folder and the PR are the authorities now).
- `STATUS.md` as a completion artifact — it violates "nothing carries status." Partial/paused state must be recoverable from progressive IMPLEMENTATION.md alone.

### Brief-based dispatch (the briefs invariant)

This is the central addition. State the plugin-wide invariant once: **context authors write once, in full, addressed to the consumer; orchestrators route verbatim, never paraphrase.** Then the mechanics:

- At dispatch time, the orchestrator derives each worker's brief from PLAN.md/DESIGN.md contracts while its context is hot — the brief is written to `docs/plans/<NN>-<slug>/briefs/` and committed (provenance and debugging truth; no future agent is required to read them to understand the change).
- Worker prompts consist of the routed brief plus mechanical pointers, not an orchestrator summary of the plan.
- A brief names its consumer, its owned paths, required reading, the contract, done evidence, and asks the worker to report contradictions rather than resolve them silently.
- Guard against the failure mode: this is not "write more artifacts." A brief with no named consumer is ceremony. The invariant is authorship + verbatim routing; the artifact is just the medium.

### Progressive IMPLEMENTATION.md

- Written at execution start (session/run identity, execution shape), updated as each slice completes — never batched to the end. A killed run must leave a branch resumable from its artifacts alone. Keep the required content (what was built, files touched, tradeoffs, validation notes, deviations from plan wording); change *when* it is written.
- In a cloud/PR flow, record the run identity (session URL or run ID) instead of local transcript paths.

### Review posture (parameterized, declared by the invoker)

- **Terminal** (default; no downstream review stage declared): mandatory independent review via the comprehensive-review skill, as today.
- **Pipeline** (invoker declares a downstream orchestrated review stage exists): the in-run review drops to a pre-flight self-verification — does it build/run, do the acceptance criteria pass locally, is the plan folder complete (PLAN.md, progressive IMPLEMENTATION.md, briefs) — and the deep review happens downstream against the PR.
- Posture is declared, never inferred. The user saying "skip review" is an invoker declaration.

### Delegation as judgment

Replace "even the smallest planned change should normally be given to at least one implementation subagent" with: delegation depends on harness capability (some harnesses have no subagents) and context economics — when the orchestrator's context is already hot with the plan (one-shot composition), direct implementation of a small slice can beat paying a cold worker's spin-up. Keep the sizing ladder and recon-first method intact; keep "the orchestrator does not become an opportunistic implementor while workers are running."

### One-shot composition

Add briefly: when a single run does plan then execute, each skill runs as a separately dispatched context and the handoff is the plan folder's artifacts, not the orchestrator's memory (see DESIGN.md). Execute reads the plan cold — that cold read is load-bearing.

### Completion in a PR flow

Completion = commits pushed and a PR whose body's first line is the marker `Workflow-Plan: docs/plans/<NN>-<slug>/`. No folder renaming, no roadmap edits.

### Payload relocation

Create `skills/execute/reference.md` holding: (a) the per-harness model-selection tables (Cursor/Claude Code/Codex hints currently in the skill body) — these rot fast and are environment configuration, not orchestration doctrine; (b) the per-harness session-ID capture formulas (currently step 1a), kept for local runs where transcript-parser needs them, as best-effort; (c) any persuading-why prose you relocate. Top of reference.md: consumers are workflow-tuning, skill revisers, and local runs needing harness specifics; not loaded during normal cloud execution. SKILL.md points to it in one line.

### Why-relocation

Same discipline as the whole revision: keep the failure-mode preamble and one-line behavioral rationale; move design-self-justification to reference.md. Test per sentence: *if the agent already trusted the rule, would this sentence change what it does?*

## Done evidence

- `grep -rn "ROADMAP\|\[NEW\]\|STATUS.md" skills/execute/` returns nothing (except, if needed, a line in reference.md explaining what was removed).
- SKILL.md contains: the briefs invariant and dispatch mechanics, progressive IMPLEMENTATION.md, both review postures with declared-not-inferred, delegation-as-judgment, one-shot composition note, PR completion with the marker line.
- `skills/execute/reference.md` exists with model tables, session-capture formulas, and a consumer note at the top.
- The sizing ladder and lean-orchestrator rules survive recognizably.

## Report back

A short summary: what you removed, what you added, any deviation from this brief and why, and any contradiction you found between this brief and the DESIGN.md contracts (report, don't silently resolve).
