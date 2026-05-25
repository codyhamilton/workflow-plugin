# Workflow Plugin — Architecture

## Component Map

```
Workflow Plugin (opencode / Claude Code)
├── skills/
│   ├── planning/          → Creates PLAN.md, DESIGN.md, owns provenance capture
│   ├── plan-execution/    → Executes plans, writes IMPLEMENTATION.md + REVIEW.md
│   ├── comprehensive-review/  → Independent review of completed work
│   ├── setup/             → Bootstrap docs/ARCHITECTURE.md + docs/ROADMAP.md
│   └── workflow-tuning/   → Meta-skill: improve workflow itself, run evals
├── docs/
│   ├── OVERVIEW.md        → (this repo's overview)
│   ├── ARCHITECTURE.md    → (this repo's architecture)
│   └── plans/             → PLAN.md artifacts when dogfooding
└── evals/
    ├── scenarios/         → Fixture corpus for skill prompt testing
    └── results/           → Eval run results and comparison tables
```

## Skill Responsibilities

**planning**: Single responsibility is capturing intent and producing durable plan artifacts.
- Reads target repo's stable docs (docs/OVERVIEW.md, docs/ARCHITECTURE.md, docs/design/)
- Captures user intent verbatim in PLAN.md
- Extracts conversation transcript into PROVENANCE.md (via plan-execution session capture, or user-provided session ID)
- Asks only scope-shaping questions
- Optionally writes plan-scoped DESIGN.md for cross-implementor contracts
- Does NOT implement; stops and returns to planning if architectural misalignment detected

**plan-execution**: Single responsibility is orchestrating implementation of an existing plan.
- Reads plan contracts and checks alignment with architecture
- Sizes work and delegates to implementation subagents
- Keeps orchestrator context lean
- Runs mandatory comprehensive review after implementation
- Writes IMPLEMENTATION.md + REVIEW.md completion artifacts
- Does NOT self-review; mandatory independent review is part of execution

**comprehensive-review**: Single responsibility is independent review.
- Reads plan + implementation + review artifacts
- Applies four review lenses
- Writes findings by severity
- Capped at one external loop; self-review for in-scope fixes

**setup**: Single responsibility is bootstrapping missing stable docs.
- Reconnaissance phase: reads existing docs
- Permission gate: asks user before proceeding
- Guided conversation: structured high-to-narrow questions
- Writes docs/ARCHITECTURE.md + docs/ROADMAP.md
- Creates docs/ if absent
- Does NOT plan or execute; hooks into planning afterward

**workflow-tuning**: Single responsibility is improving the workflow itself.
- Holds real-world lessons corpus (reference.md)
- Enables eval mode: behavior validation, reliability testing, variant testing
- Reads existing plan folders as eval fixtures
- Compares skill prompt variants against ground truth
- Does NOT implement target work; meta-layer only

## Cross-Skill Contracts

**planning → plan-execution**:
- planning produces durable PLAN.md with explicit scope, contracts, acceptance criteria
- plan-execution reads PLAN.md as authority; stops if alignment questions arise

**plan-execution → comprehensive-review**:
- plan-execution calls comprehensive-review; mandatory, not optional
- comprehensive-review reads plan + implementation artifacts
- No direct contract; review is post-hoc

**setup → planning**:
- setup creates docs/ARCHITECTURE.md and docs/ROADMAP.md
- planning reads those docs at step 2 of workflow
- No code coupling; dependency is filesystem presence

**planning → workflow-tuning**:
- planning writes PROVENANCE.md; workflow-tuning reads it
- Evals use existing plan folders as fixtures
- workflow-tuning never invokes planning; meta-layer only

## Key Invariants

1. User intent is always captured verbatim in PLAN.md `## Intent` section, never paraphrased
2. Execution always includes independent review; no self-review-only completion
3. Stable docs (docs/ARCHITECTURE.md, docs/OVERVIEW.md, docs/design/) are read by planning, not written by it (planning only updates when the docs are stale and misaligned)
4. Plans are never implementation specs; they are intent, scope, implications, and acceptance criteria
5. DESIGN.md is optional, only when it reifies contracts or target shape not inferrable from code and stable docs
6. workflow-tuning never auto-runs; user-invoked meta-skill only

## Data Flows

**Planning session**:
1. User → planning skill: "I want to <request>"
2. planning reads stable docs, captures request verbatim, records Q&A turns → PLAN.md + PROVENANCE.md
3. planning → user: "Here is the plan; shall I proceed?"

**Execution session**:
1. User → plan-execution skill: "Execute <plan>"
2. plan-execution reads PLAN.md, sizes work, delegates to subagents
3. plan-execution → comprehensive-review → subagent (fixes)
4. plan-execution writes IMPLEMENTATION.md + REVIEW.md in plan folder
5. plan-execution → user: "Plan executed; here are findings"

**Setup session**:
1. User → setup skill: "Set up architecture docs"
2. setup reads existing docs, asks permission, conducts guided conversation
3. setup writes docs/ARCHITECTURE.md + docs/ROADMAP.md
4. setup → user: "Docs created; run /workflow:planning"

**Eval session** (meta):
1. User → workflow-tuning skill: "Eval planning on <fixtures>"
2. workflow-tuning spawns subagents with planning skill prompt + scenario input
3. workflow-tuning compares outputs to ground truth, writes results/
4. workflow-tuning → user: "Comparison table; here are findings"

## Stable References

- [OVERVIEW.md](OVERVIEW.md) — what the plugin is and why
- [skills/planning/SKILL.md](../skills/planning/SKILL.md) — planning skill full prompt
- [skills/planning/templates/PLAN.md](../skills/planning/templates/PLAN.md) — plan template
- [skills/workflow-tuning/reference.md](../skills/workflow-tuning/reference.md) — observed lessons corpus
