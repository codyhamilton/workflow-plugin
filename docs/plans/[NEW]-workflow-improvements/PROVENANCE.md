# Provenance: [NEW] Workflow Improvements

## Session

- Session: Initial planning (May 19, 2026)
- Timestamp: 2026-05-19T00:00:00Z
- CWD: /home/codyh/workspace/workflow-plugin

## Initial Request (verbatim)

> Consider our workflow skills. This is a simple starting point, but there's a few things we need to add.
> 1. A setup command for the workflow. Initial setup requires ensuring a docs folder is present, and we have our docs for "architecture plus intent". This could be called architecture.md/roadmap.md? consider. Regardless, the setup command has to orchestrate a comprehensive review, look for existing docs, consolidate. It should ask the user if it should do this. If gaps, it should take the user on a guided conversation, asking a series of high level then narrowing questions to come up with architecture and roadmap views, which it documents.
> 2. We need an evaluation system for the skills - running plan/execute commands in controlled environments. these should validate behaviours work as expected, output meets expectations and is reliable, and also be able to test different models and variations head to head (variant testing). It will be very difficult to manage reliable changes to the workflows without an eval system to do so. the workflow-tuning skill should be what does this.
> 3. We need to improve the way we record user intent. We should capture user inputs into a doc as provenance. Specific user inputs (sanitised). These could be pulled from chat transcripts, the harnesses we support all create these. provenance should be exact user inputs (initial/followups/questions responses) along with summary of agent relevant context, e.g. the questions agent asked or a brief of what the agent decided based on that

## Planning Conversation

### Turn 1

**Agent asked:** Should provenance be a separate PROVENANCE.md file or a section added to PLAN.md? Should the docs be ARCHITECTURE.md + ROADMAP.md or other names? Should the eval system be its own skill or part of workflow-tuning?

**User responded (verbatim):**
> form this into a plan within this doc - lets start by dogfooding our own workflow

## Agent Decisions

- **Three features as linked child plans**: The user's request implied three related improvements. Decision: structure as parent program [NEW]-workflow-improvements with three child plans (01-provenance-capture, 02-setup-skill, 03-eval-system) to allow phased execution and clear sequencing.

- **Provenance as separate PROVENANCE.md**: Decision: PROVENANCE.md is a separate file alongside PLAN.md. Rationale: keeps PLAN.md short and decision-oriented (intent, scope, implications, phases, criteria) while making transcript evidence available separately. Durable provenance depends on transcript extraction, not agent convention.

- **Docs named ARCHITECTURE.md + ROADMAP.md**: Decision: confirmed ARCHITECTURE.md (with Purpose, Stack, Component Map, Invariants, Key Data Flows, Stable References sections) and ROADMAP.md (with Current State, Active Work, Planned, Not In Scope). These are the stable docs planning already reads.

- **Eval system as part of workflow-tuning**: Decision: eval modes are an extension of workflow-tuning skill, not a separate skill. Rationale: workflow-tuning already has disable-model-invocation: true marking it as a meta-skill; evals are a meta-layer capability. Keeps the four-skill structure intact.

- **Phased execution sequence**: Decision: 01-provenance first (smallest, foundational), 02-setup second (new skill, depends on provenance for good fixtures), 03-evals third (depends on both for meaningful fixtures and stable docs). This allows learning across phases.

- **Dogfooding**: Decision: use the workflow-plugin's own planning system to plan the improvements to the workflow-plugin. This validates that the workflow can handle self-modification and produces real examples of plan artifacts that become eval fixtures.

- **Stable docs for workflow-plugin**: Decision: create docs/OVERVIEW.md and docs/ARCHITECTURE.md for the workflow-plugin repo itself (not just target repos). This lets the planning skill read them and demonstrates the architecture as documentation.

### Turn 2

**Agent noted:** Child 01 plan had a gap — the JSONL transcript extraction approach required jq filters, session UUID identification, and sanitization rules that weren't specified, leaving a cold executor to invent the mechanics.

**User responded (verbatim):**
> lets improve the plan with some specifics then. I think it's better to keep it simple to start. Just provide guidance in the plan to write to provenance _at the moment the user provides it_. E.g, it can be directed to create the plan directory and write provenance early (while the context is still accurate) before doing anything else. Same for questions - as the user responds, record immediately in the provenance. This will avoid information getting stale in context before it is used, and also provide a refresh point (think of it like progressive summarisation)

**Agent decisions:**

- **Progressive writing over transcript extraction**: Child 01 approach changed from post-hoc JSONL extraction to incremental writing at the moment each input arrives. Rationale: simpler, no external dependencies, agent controls what goes in, prevents context staleness.
- **Three write points**: Initial request (before reading stable docs), each Q&A turn (immediately on response), agent decisions (before finalizing). This matches the progressive summarisation framing the user described.
- **Parent PLAN.md updated**: "transcript-based capture" replaced with "progressive conversation record written incrementally".

### Turn 3

**User clarified (direction, not verbatim):** Provenance is not a perfect transcript. The goal is intent in the user's words — strip tone, omit anything not intended for persistence, record the substance of decisions and directions rather than copying everything said.

**Agent decisions:**

- **Recording model refined**: Child 01 scope updated with explicit guidance: extract intent, not a verbatim log. Tone and filler stripped. Casual remarks and throwaway exchanges omitted. Exact phrasing preserved only when it carries intent a paraphrase would lose.
- **Acceptance criteria updated**: Two new criteria added — "intent over transcript" and "intentional persistence only".

### Turn 4

**User clarified:** Evals must be end-to-end — plan and execute together. The plan is just an intermediate artifact; execute is what matters. Static analysis of plan output is disconnected from what the workflow actually does when run.

**Agent decisions:**

- **Eval unit redefined**: an eval is a full plan+execute cycle on a scenario, not an assessment of planning output alone.

### Turn 5

**User clarified:** Scenarios are real repos cloned at tagged commits with known tasks and reference implementations. Cost is a first-class lens: agents spawned and their sizes, tool use turns, context estimates, wall time. Quality comparison is intentionally loose — "significant improvement or regression vs baseline?" and "in the same ballpark as the reference?" No fine-grained rubrics. Fixture corpus built up over time; system ships with the pattern, not the fixtures.

**Agent decisions:**

- **Child 03 rewritten**: scope, architectural implications, execution phases, and acceptance criteria all revised to reflect e2e eval model, relative comparison, two lenses (cost + quality), and scenario format (repo + tag + task + reference).
- **Cost lens specified**: agents + sizes, tool use turns, context estimates, wall time — all captured in cost-comparison.md.
- **Quality lens specified**: narrative relative comparison against baseline and reference; no rubric.
- **Baseline model**: populated on first eval run from current workflow; reused as comparison point for future candidates.

## Next Steps

Parent PLAN.md finalized. Prepare for execution phase:
1. Execute child plan 01 (provenance capture): add PROVENANCE.md template, modify planning skill with progressive writing guidance
2. Execute child plan 02 (setup skill): create skills/setup/SKILL.md
3. Execute child plan 03 (eval system): extend workflow-tuning with eval modes
