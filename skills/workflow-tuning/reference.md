# Workflow Tuning Reference

This file records observed lessons from real plan artifacts and execution traces across multiple repos.

Use it when:

- improving `plan`, `execute`, or `comprehensive-review`
- designing workflow evals
- deciding whether a new process rule is worth its token and maintenance cost

## What Has Held Up In Practice

### 1. Concise plans work

The current plan shape has generally held up well when it stays small and centered on:

- intent
- scope
- implications or ripple effects
- execution phases
- observable acceptance criteria

Examples:

- `free-frontier/docs/plans/[NEW]-game-systems/PLAN.md`
- `free-frontier/docs/plans/[NEW]-game-systems/03-fleets-pathfinding/PLAN.md`
- `lemmings/docs/plans/04-runtime-entry-surface/PLAN.md`

These plans steer work without overcommitting to low-accuracy implementation detail.

### 2. Parent program plus child plans is a good default

The parent-program model has proven useful in practice:

- parent plan explains why the program exists
- roadmap shows ordering and dependency truth
- child plans keep execution slices focused
- completion artifacts stay in the child folder as provenance

Examples:

- `free-frontier/docs/plans/[NEW]-game-systems/ROADMAP.md`
- `garcia-music/docs/plans/02-player-design-system/ROADMAP.md`
- `lemmings/docs/plans/[NEW]-operator-surface-redesign/ROADMAP.md`

This supports cost control and focus by defaulting work to one slice at a time.

### 3. Implementation and review artifacts are valuable

`IMPLEMENTATION.md` and `REVIEW.md` have earned their keep.

They preserve:

- what was actually built
- intentional deviations from plan wording
- concrete findings
- residual risks

Examples:

- `free-frontier/docs/plans/[NEW]-game-systems/03-fleets-pathfinding/IMPLEMENTATION.md`
- `free-frontier/docs/plans/[NEW]-game-systems/03-fleets-pathfinding/REVIEW.md`
- `lemmings/docs/plans/04-runtime-entry-surface/02-unified-startup-and-readiness-path/IMPLEMENTATION.md`
- `lemmings/docs/plans/04-runtime-entry-surface/02-unified-startup-and-readiness-path/REVIEW.md`

This is especially useful for multi-session recovery and for evaluating workflow quality after the fact.

## Stable Docs Versus Plan Docs

### 4. Good stable docs matter

The workflow benefits from concise docs that explain what the code alone does not make cheap to infer.

The most valuable stable docs are:

- architecture docs that act like a concept graph or ownership map
- design-intent docs that explain why the system or surface exists and what matters about the outcome

Plans then connect current state to the target state under those stable anchors.

### 5. Document cascades are real and expensive

Too much documentation causes a cascade where agents keep producing more explanatory prose that mostly restates what the code already shows.

This costs tokens, slows work, and creates drift pressure.

Avoid adding docs whose main value is:

- free-text restatement of implementation
- duplicating code structure in prose
- storing fragile implementation details that will drift quickly

## When `DESIGN.md` Is Worth It

### 6. `DESIGN.md` is not universally required

Its best interpretation is:

> the to-be architecture or target shape within the scope of this change

It is most valuable when it reifies:

- cross-implementor contracts
- ownership boundaries
- required behavior
- non-goals
- measurable acceptance evidence

It is less valuable when it becomes a long free-text explanation of code that is easier to read directly.

### 7. Repo evidence on `DESIGN.md`

#### Free Frontier

Parent-level design is useful because it captures game-system contracts and invariants that cross multiple child plans:

- `free-frontier/docs/plans/[NEW]-game-systems/DESIGN.md`

This file earns its cost because it defines the target simulation architecture and shared contracts across fleets, combat, AI, and persistence.

By contrast, not every child plan has its own `DESIGN.md`, and that seems healthy. The child plan can often inherit the parent design plus the plan itself.

#### Garcia Music

`DESIGN.md` is useful when the target shape is visual or experiential and cannot be inferred cheaply from code:

- `garcia-music/docs/plans/[NEW]-subscribe-redesign/01-subscribe-visual-redesign/DESIGN.md`
- `garcia-music/docs/plans/[NEW]-subscribe-redesign/02-artist-copy-settings/DESIGN.md`

These docs help because they define target layout, copy behavior, render rules, and data contracts. They are closer to product/design contracts than architecture prose.

Risk: UI design docs can become too detailed and drift into implementation spec if not kept disciplined.

#### Lemmings

`DESIGN.md` is highly valuable in contract-heavy architectural remediation:

- `lemmings/docs/plans/04-runtime-entry-surface/DESIGN.md`
- `lemmings/docs/plans/[NEW]-operator-surface-redesign/01-runtime-surface-api-and-session-contract/DESIGN.md`

These docs earn their cost because they reify cross-implementor contracts and ownership boundaries that would otherwise be reconstructed repeatedly from code and conversation.

Risk: this repo also shows the documentation multiplication hazard. A design doc per child plan is justified only when the contract surface is genuinely complex.

### 8. Practical rule for `DESIGN.md`

Require plan-scoped `DESIGN.md` only when at least one is true:

- multiple implementors need the same contract
- the target shape is materially different from current architecture
- the change introduces or repairs ownership boundaries
- acceptance depends on explicit behavior or interface contracts
- code alone would not make the desired target shape cheap to infer

Otherwise, rely on:

- stable architecture and design-intent docs
- concise `PLAN.md`
- later `IMPLEMENTATION.md` and `REVIEW.md`

## Execution Lessons

### 9. Lightweight implementation planning is the right missing middle

Strict orchestration and handoff contracts can overwhelm agent focus and over-reward process compliance.

For most implementation work, prefer a lightweight implementation plan that defines:

- goal
- ordered activities
- dependencies
- decision points
- delegation candidates
- done evidence

This is enough structure for recovery and coordination without forcing premature decomposition.

### 10. Cost-aware orchestration should be explicit

The workflow should optimize for cost-adjusted outcome quality, not for maximum autonomy.

Observed operating heuristics worth preserving:

- keep orchestrator context bounded
- avoid long-lived high-context agents unless there is clear value
- use frontier models for plan, synthesis, ambiguous architecture, and high-value review
- use cheaper, faster, more obedient models for bounded implementation slices
- escalate model class only when the problem demands more capability

### 11. Orchestrator waiting discipline matters

If the next meaningful step depends on worker outputs, the orchestrator should wait.

Failure mode to avoid:

1. orchestrator spawns workers
2. orchestrator continues doing implementation on its own
3. context grows
4. orchestration collapses into an expensive second implementor

The orchestrator's context should hold control state, not duplicate implementation detail from the workers.

### 16. Orchestrators delegating must not edit deliverable files themselves

When delegating, the parent's edit calls should be limited to orchestration artifacts: `IMPLEMENTATION.md`, `REVIEW.md`, `ROADMAP.md`, and commit operations. Zero edits to the actual deliverable files (skills, code, config being changed).

The failure mode from lesson 11 has a measurable signature: parent edit count exceeds subagent edit count despite delegation being present.

Observed in `01-workflow-improvements`: parent made 26 edits; subagent implementors combined made 8. The excess was almost entirely post-review remediation — the parent re-read each file and applied fixes the review agent had identified but not fixed. The review agent had full context at the point of finding; the parent had to reconstruct it.

Rule: if the parent is making deliverable-file edits, either the task was not delegated correctly, or the review agents are not applying their own fixes (see lesson 19).

### 17. Task granularity threshold: small tasks often do not justify individual agent spawns

Signs that a task is below the delegation threshold:

- implementation agent is expected to use fewer than ~10 tool turns
- task touches 1-3 files with clear, non-ambiguous changes
- the work briefing would be longer than the work itself

At this scale, the parent's coordination overhead (reading the plan, writing the prompt, waiting, reading results back) likely exceeds the cost of inline execution.

Observed in `01-workflow-improvements`: implementation agents used 4-8 turns each (child 01: 6, child 02: 4, child 03: 8), touching 1-3 files per task. Total subagent turns: 42 vs parent turns: 74. Delegation did not move enough of the actual work out of the parent to justify six spawns.

Alternative: implement inline in the parent for tasks expected under ~10 turns, or batch multiple small tasks into one agent with a compound brief.

### 18. Explicit model class must be specified in delegation prompts

Without explicit assignment, all spawned agents default to the system default (currently `general-purpose` / `sonnet-4-6`), regardless of task complexity.

Observed in `01-workflow-improvements`: all 6 subagents ran on `sonnet-4-6`, including implementation agents doing 4-8 turn scoped edits (reading 1-3 files, making focused changes). `haiku` would have been appropriate and meaningfully cheaper.

Required practice: the execute skill must specify model class per delegation type. Suggested defaults:

- plan, synthesis, cross-cutting design review, high-ambiguity judgment: sonnet or opus

Update `execute` skill with explicit delegation rules derived from lessons 16-19:

- orchestrator must not edit deliverable files — only orchestration artifacts
- review agents must apply fixes, not just report (except the three escalation exceptions in lesson 19)
- require explicit model class per delegation type in the briefing template
- document the task granularity threshold and when to inline instead of spawn

### Priority 2

Tighten the rule for when `DESIGN.md` is required versus optional.

### Priority 3

Use existing plan folders as a workflow eval corpus:

- compare plan size to execution quality
- compare presence or absence of `DESIGN.md` to outcome quality
- compare review cost to findings quality
- identify where documentation or orchestration paid for itself and where it did not

## Maintenance Rule

Update this file when executed plans reveal something new about:

- documentation economy
- orchestration cost
- phasing
- review effectiveness
- where workflow rigor materially improves outcomes

Do not update it just to restate the current workflow in different words.

## Eval Patterns

*This section grows as actual eval runs produce lessons. Initially empty.*

Record patterns here when eval runs produce non-obvious lessons — e.g., "scenario X consistently shows higher tool turn counts with model Y," or "quality comparison is unreliable when the reference implementation is more than 6 months old."

Do not record obvious or generic lessons. Only record findings that would surprise a future evaluator or change how they interpret results.
