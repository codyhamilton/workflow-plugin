# Workflow Improvements: Provenance, Setup, and Evals

Three linked improvements to the workflow-plugin, built and reviewed in sequence: progressive
provenance capture in the planning skill, a new `setup` skill that bootstraps a repo's stable docs,
and an end-to-end eval pattern in `workflow-tuning`. All three landed and met their acceptance
criteria. It was the plugin's first self-modification run, planned and executed with its own
plan → execute → review loop.

## Intent

User request, verbatim:

> Consider our workflow skills. This is a simple starting point, but there's a few things we need to add.
> 1. A setup command for the workflow. Initial setup requires ensuring a docs folder is present, and we have our docs for "architecture plus intent". This could be called architecture.md/roadmap.md? consider. Regardless, the setup command has to orchestrate a comprehensive review, look for existing docs, consolidate. It should ask the user if it should do this. If gaps, it should take the user on a guided conversation, asking a series of high level then narrowing questions to come up with architecture and roadmap views, which it documents.
> 2. We need an evaluation system for the skills - running plan/execute commands in controlled environments. these should validate behaviours work as expected, output meets expectations and is reliable, and also be able to test different models and variations head to head (variant testing). It will be very difficult to manage reliable changes to the workflows without an eval system to do so. the workflow-tuning skill should be what does this.
> 3. We need to improve the way we record user intent. We should capture user inputs into a doc as provenance. Specific user inputs (sanitised). These could be pulled from chat transcripts, the harnesses we support all create these. provenance should be exact user inputs (initial/followups/questions responses) along with summary of agent relevant context, e.g. the questions agent asked or a brief of what the agent decided based on that

## Why This Existed

The plugin handled structured plan/execute cycles but had three gaps that blocked iterating on the
workflow itself. Planning read stable docs that nothing created, so new repos got degraded plans.
There was no way to validate that a prompt change improved behavior, which made workflow-tuning
observational only. And intent capture stopped at the initial request — follow-up answers, question
turns, and decision rationale were reconstructed from agent memory rather than recorded.

## What Was Built

Three phases, executed in dependency order, each independently reviewed before the next began. The
surfaces named below are as they existed at the time; several have since been renamed or relocated
by later work (the `planning` skill became `plan`; `setup` moved to the lab plugin; `ROADMAP.md` was
dropped from the convention entirely).

**Changed:** `skills/planning/` (SKILL.md and both templates), `skills/setup/SKILL.md` (new),
`skills/workflow-tuning/` (SKILL.md and reference.md), `evals/` (new tree).

### Phase 1 — Provenance capture

`PROVENANCE.md` gained a template (Session, verbatim Initial Request, per-turn Planning
Conversation, final Agent Decisions) and the planning skill gained three ordered write points: create
the file immediately after capturing the verbatim request and before reading anything else, append
each Q&A turn on receipt, append cross-cutting decisions before finalizing. The recording model is
intent-not-transcript — strip tone and filler, omit what was not meant to persist, preserve exact
phrasing only where a paraphrase would lose meaning.

The approach changed mid-plan. The original design extracted provenance from harness JSONL
transcripts after the fact; the user redirected to progressive writing at the moment each input
arrives, which removed the jq/session-UUID/sanitization mechanics entirely and prevented context
going stale before it was recorded.

### Phase 2 — Setup skill

A six-phase `workflow:setup`: reconnaissance over existing docs and the source tree before speaking,
an explicit permission gate, consolidation that merges partial docs rather than duplicating them and
flags contradictions with observed code, a three-round guided conversation (purpose → components →
state and constraints, one question per round), the doc writes, and a hand-off to planning. The
planning skill's grounding step began suggesting setup when stable docs were absent or thin.

### Phase 3 — Eval system

An eval is a full plan+execute cycle against a fixture scenario — a real repo at a tagged commit with
a known task and a reference implementation — not an assessment of planning output. Two lenses: cost
(agents spawned and their sizes, tool turns per agent and total, context estimates, wall time) and
quality, deliberately loose — "significant delta against baseline?" and "same ballpark as the
reference?" — with no fine-grained rubric. `evals/README.md` documents the scenario, results, and
run formats; `workflow-tuning` gained an Eval Capability section and an Eval Patterns record. The
fixture corpus shipped empty, by design: the pattern ships, the fixtures accrete.

## Deviations

- **`OVERVIEW.md` added to setup's scope.** The plan specified `ARCHITECTURE.md` + `ROADMAP.md`
  only, but planning also read `OVERVIEW.md` — so setup as planned would have left planning still
  reporting missing docs, a loop with no exit. Setup writes it as a mandatory one-paragraph output.
- **Provenance via progressive writing, not transcript extraction.** Changed during planning at the
  user's direction, as above. The plan text was updated in place before execution.
- **Phase 1's live-session test was deferred.** This program's own `PROVENANCE.md` stood in as the
  real example of correct output shape.

## Review

Each phase was independently reviewed and every acceptance criterion across the three was met.
Findings were fixed before the phase was committed: phase 1 — one high (the template labelled a turn
"verbatim" while the instructions said to strip tone; the label was removed) plus three mediums
(step ordering, the two-layer decisions structure, user-volunteered turns). Phase 2 — two highs (the
`OVERVIEW.md` coherence gap above; consolidation was not actually gated by the permission phase) and
two mediums (stale-content handling, the `PROVENANCE.md` condition). Phase 3 — two mediums (a
tool-turns schema mismatch between README and SKILL.md, a missing baseline-immutability guard) and
three lows.

## QA

None beyond review. The output is skill prose; the acceptance criteria were checked by reading the
artifacts the skills produced, and the plugin had no QA stage at the time.

## Residual Risks

- **Provenance compliance is behavioral, not structural.** All three write points depend on the agent
  following ordered steps; nothing forces a write. An agent under context pressure can still batch
  them at the end.
- **The baseline is fixed on the first eval run**, so one anomalous run anchors every later
  comparison. Accepted for v1 over averaging multiple baseline runs.
- **Setup's three-round conversation cap** may be too rigid for a complex system.

## Follow-ups

None tracked as issues. The eval fixture corpus stayed empty and the eval system was never exercised
against a real scenario — later work re-scoped evals out of scope rather than building on this, and
`setup` and `workflow-tuning` were subsequently moved to the `workflow-lab` plugin.

## Decisions Worth Keeping

- **Provenance is a separate file, not a `PLAN.md` section.** It keeps the plan short and
  decision-oriented while leaving the conversation record available to anyone who wants it.
- **Evals must be end-to-end.** The plan is an intermediate artifact; execution is what the workflow
  actually does, so scoring plan output alone measures the wrong thing.
- **Quality comparison stays loose on purpose.** Automated rubrics over open-ended implementation
  tasks are either too rigid or too easy to game; a narrative relative judgment was the honest
  instrument for v1.
- **Dogfooding was the point, not a flourish.** Running the plugin's own loop on itself was how the
  loop's gaps became visible, and it produced the first real examples of each artifact's shape.
