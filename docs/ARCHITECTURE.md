# Workflow Plugin — Architecture

## Component Map

```
Workflow Plugin (opencode / Claude Code)
├── skills/
│   ├── plan/          → Creates PLAN.md, DESIGN.md, owns provenance capture
│   ├── execute/    → Executes plans, writes IMPLEMENTATION.md + REVIEW.md
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

**plan**: Single responsibility is capturing intent and producing durable plan artifacts.
- Reads target repo's stable docs (docs/OVERVIEW.md, docs/ARCHITECTURE.md, docs/design/)
- Captures user intent verbatim in PLAN.md
- Extracts conversation transcript into PROVENANCE.md (via execute session capture, or user-provided session ID)
- Asks only scope-shaping questions
- Optionally writes plan-scoped DESIGN.md for cross-implementor contracts
- Does NOT implement; stops and returns to plan if architectural misalignment detected

**execute**: Single responsibility is orchestrating implementation of an existing plan.
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
- Does NOT plan or execute; hooks into plan afterward

**workflow-tuning**: Single responsibility is improving the workflow itself.
- Holds real-world lessons corpus (reference.md)
- Enables eval mode: behavior validation, reliability testing, variant testing
- Reads existing plan folders as eval fixtures
- Compares skill prompt variants against ground truth
- Does NOT implement target work; meta-layer only

## Cross-Skill Contracts

**plan → execute**:
- plan produces durable PLAN.md with explicit scope, contracts, acceptance criteria
- execute reads PLAN.md as authority; stops if alignment questions arise

**execute → comprehensive-review**:
- execute calls comprehensive-review; mandatory, not optional
- comprehensive-review reads plan + implementation artifacts
- No direct contract; review is post-hoc

**setup → plan**:
- setup creates docs/ARCHITECTURE.md and docs/ROADMAP.md
- plan reads those docs at step 2 of workflow
- No code coupling; dependency is filesystem presence

**plan → workflow-tuning**:
- plan writes PROVENANCE.md; workflow-tuning reads it
- Evals use existing plan folders as fixtures
- workflow-tuning never invokes plan; meta-layer only

## Key Invariants

1. User intent is always captured verbatim in PLAN.md `## Intent` section, never paraphrased
2. Execution always includes independent review; no self-review-only completion
3. Stable docs (docs/ARCHITECTURE.md, docs/OVERVIEW.md, docs/design/) are read by plan, not written by it (plan only updates when the docs are stale and misaligned)
4. Plans are never implementation specs; they are intent, scope, implications, and acceptance criteria
5. DESIGN.md is optional, only when it reifies contracts or target shape not inferrable from code and stable docs
6. workflow-tuning never auto-runs; user-invoked meta-skill only

## Data Flows

**Planning session**:
1. User → plan skill: "I want to <request>"
2. plan reads stable docs, captures request verbatim, records Q&A turns → PLAN.md + PROVENANCE.md
3. plan → user: "Here is the plan; shall I proceed?"

**Execution session**:
1. User → execute skill: "Execute <plan>"
2. execute reads PLAN.md, sizes work, delegates to subagents
3. execute → comprehensive-review → subagent (fixes)
4. execute writes IMPLEMENTATION.md + REVIEW.md in plan folder
5. execute → user: "Plan executed; here are findings"

**Setup session**:
1. User → setup skill: "Set up architecture docs"
2. setup reads existing docs, asks permission, conducts guided conversation
3. setup writes docs/ARCHITECTURE.md + docs/ROADMAP.md
4. setup → user: "Docs created; run /workflow:plan"

**Eval session** (meta):
1. User → workflow-tuning skill: "Eval plan on <fixtures>"
2. workflow-tuning spawns subagents with plan skill prompt + scenario input
3. workflow-tuning compares outputs to ground truth, writes results/
4. workflow-tuning → user: "Comparison table; here are findings"

## Stable References

- [OVERVIEW.md](OVERVIEW.md) — what the plugin is and why
- [skills/plan/SKILL.md](../skills/plan/SKILL.md) — plan skill full prompt
- [skills/plan/templates/PLAN.md](../skills/plan/templates/PLAN.md) — plan template
- [skills/workflow-tuning/reference.md](../skills/workflow-tuning/reference.md) — observed lessons corpus
