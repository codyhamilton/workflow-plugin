# Workflow Tuning Reference

Observed lessons from real plan artifacts and execution traces across multiple repos. Empirical, not
architectural — the reasoning the skills are *built on* lives in [principles.md](principles.md).

Use it when:

- improving `plan`, `refine`, `execute`, `comprehensive-review`, `post-build`, or `close-out`
- designing workflow evals
- deciding whether a new process rule is worth its token and maintenance cost

Lessons are numbered for stable citation; numbers are never reused and gaps are expected. A lesson
whose recommendation has been implemented is marked **Landed**, with where it landed — kept rather
than deleted, because the observation is still the evidence for the rule. A lesson whose mechanism
has been superseded is marked **Retired**.

## What Has Held Up In Practice

### 1. Concise plans work — **Landed** (`plan`'s six-phase workflow and `templates/PLAN.md`)

The plan shape has held up well when it stays small and centered on:

- intent
- scope
- implications or ripple effects
- execution phases
- observable acceptance criteria

Observed across free-frontier, lemmings, and garcia-music. These plans steer work without
overcommitting to low-accuracy implementation detail.

The refinement added later (see lesson 26) does not contradict this: the plan stays light, and the
executable detail lives in briefs that are deleted at close-out rather than in a heavier `PLAN.md`.

### 2. Parent program plus child plans — **Retired**

The parent-program / `ROADMAP.md` folder taxonomy this lesson described was removed in the
pivot-consolidate-focus revision. Status now lives in the PR and the tracker, not a folder
hierarchy, and `plan` has no program/child-plan convention. The value the lesson pointed at —
defaulting work to one slice at a time — now comes from a stable design-intent doc in `docs/design/`
plus a sequence of self-contained plan-execute runs. Do not cite this lesson as license to recreate
the taxonomy. Retained only so the retirement is legible.

### 3. Implementation and review artifacts are valuable — **Landed, then scoped**

`IMPLEMENTATION.md` and `REVIEW.md` earned their keep during a run. They preserve what was actually
built, intentional deviations from plan wording, concrete findings, and residual risks — especially
useful for multi-session recovery and for evaluating workflow quality after the fact.

What the lesson got wrong was their *lifetime*. It treated them as durable, which is how plan folders
became piles nobody reads. They are run-scoped: load-bearing while the change is open, redundant once
it lands, because their substance is condensed into the close-out record file and their full text
remains in the commits that introduced them. `close-out` consumes them — along with `PLAN.md` and the
rest of the folder. See lesson 27.

## Stable Docs Versus Plan Docs

### 4. Good stable docs matter — **Landed** (`plan`'s Ground phase, `setup`)

The workflow benefits from concise docs that explain what the code alone does not make cheap to
infer. The most valuable are architecture docs that act like a concept graph or ownership map, and
design-intent docs that explain why a system or surface exists and what matters about the outcome.
Plans then connect current state to target state under those stable anchors.

### 5. Document cascades are real and expensive — **Landed** (`plan`'s failure-mode preamble)

Too much documentation causes a cascade where agents keep producing explanatory prose that mostly
restates what the code already shows. This costs tokens, slows work, and creates drift pressure.

Avoid docs whose main value is free-text restatement of implementation, prose duplication of code
structure, or storage of fragile implementation details that will drift quickly.

This applies to the plugin's own docs. `docs/ARCHITECTURE.md` grew a per-skill responsibilities
section that restated each `SKILL.md` in worse words and had to be cut back to seams and contracts.

## When `DESIGN.md` Is Worth It

### 6. `DESIGN.md` is not universally required — **Landed** (`plan`'s DESIGN.md rules)

Its best interpretation: *the to-be architecture or target shape within the scope of this change.*

Most valuable when it reifies cross-implementor contracts, ownership boundaries, required behavior,
non-goals, or measurable acceptance evidence. Least valuable when it becomes a long free-text
explanation of code that is easier to read directly.

### 7. Repo evidence on `DESIGN.md`

**Free Frontier.** Program-level design earned its cost by capturing game-system contracts and
invariants that crossed multiple slices — the target simulation architecture and shared contracts
across fleets, combat, AI, and persistence. Notably, *not* every slice had its own `DESIGN.md`, and
that seemed healthy: a slice can usually inherit the program design plus its own plan.

**Garcia Music.** `DESIGN.md` is useful when the target shape is visual or experiential and cannot be
inferred cheaply from code — target layout, copy behavior, render rules, data contracts. Closer to
product/design contracts than architecture prose. Risk: UI design docs drift into implementation spec
if not kept disciplined.

**Lemmings.** Highly valuable in contract-heavy architectural remediation, where it reifies
cross-implementor contracts and ownership boundaries that would otherwise be reconstructed
repeatedly from code and conversation. Risk: this repo also showed the documentation multiplication
hazard — a design doc per slice is justified only when the contract surface is genuinely complex.

(The plan folders these observations came from predate the current naming convention. They remain
valid as historical provenance; do not read their paths as the convention.)

### 8. Practical rule for `DESIGN.md` — **Landed** (`plan`, `workflow-tuning`'s Documentation Economy)

Require plan-scoped `DESIGN.md` only when at least one is true:

- multiple implementors need the same contract
- the target shape is materially different from current architecture
- the change introduces or repairs ownership boundaries
- acceptance depends on explicit behavior or interface contracts
- code alone would not make the desired target shape cheap to infer

Otherwise rely on stable docs, a concise `PLAN.md`, and the run's own artifacts.

`close-out` adds the back half of this rule: a `DESIGN.md` that reified contracts outliving the
change is promoted to `docs/design/`; one that was scaffolding is deleted. If neither fits, it should
not have existed.

## Execution Lessons

### 9. Lightweight implementation planning is the right missing middle — **Landed, then split**

Strict orchestration and handoff contracts can overwhelm agent focus and over-reward process
compliance. For most implementation work, prefer a lightweight implementation plan defining goal,
ordered activities, dependencies, decision points, delegation candidates, and done evidence.

This is enough structure for recovery and coordination without forcing premature decomposition. It
survives as `execute`'s step 4 for unrefined work; where `refine` ran, its dispatch list *is* this
plan, written once and committed rather than re-derived per run.

### 10. Cost-aware orchestration should be explicit — **Landed** (`execute`'s Optimization Method)

Optimize for cost-adjusted outcome quality, not maximum autonomy. Heuristics worth preserving: keep
orchestrator context bounded; avoid long-lived high-context agents without clear value; use frontier
models for plan, synthesis, ambiguous architecture, and high-value review; use cheaper, faster, more
obedient models for bounded implementation slices; escalate model class only when the problem demands
it.

Lesson 21 sharpens the cost half of this considerably.

### 11. Orchestrator waiting discipline matters — **Landed** (`execute`, `iterate`)

If the next meaningful step depends on worker output, the orchestrator should wait. The failure mode:
orchestrator spawns workers → continues implementing on its own → context grows → orchestration
collapses into an expensive second implementor. The orchestrator's context should hold control state,
not duplicate implementation detail.

### 16. Orchestrators delegating must not edit deliverable files themselves — **Landed** (`execute`, `post-build`)

When delegating, the parent's edits should be limited to orchestration artifacts and commits: zero
edits to the deliverable files being changed.

The failure mode from lesson 11 has a measurable signature: parent edit count exceeds subagent edit
count despite delegation being present. Observed in `01-workflow-improvements` — parent made 26
edits, subagent implementors 8 combined. The excess was almost entirely post-review remediation: the
parent re-read each file and applied fixes the review agent had identified but not fixed. The review
agent had full context at the point of finding; the parent had to reconstruct it.

If the parent is making deliverable-file edits, either the task was not delegated correctly or the
review agents are not applying their own fixes (lesson 19).

### 17. Small tasks often do not justify individual agent spawns — **Landed** (`execute`'s ladder, `refine`'s skip rule)

Signs a task is below the delegation threshold:

- the implementation agent is expected to use fewer than ~10 tool turns
- it touches 1–3 files with clear, non-ambiguous changes
- the briefing would be longer than the work

Observed in `01-workflow-improvements`: implementation agents used 4–8 turns each, touching 1–3 files.
Total subagent turns 42 vs parent turns 74. Delegation did not move enough work out of the parent to
justify six spawns.

Alternative: implement inline for tasks under ~10 turns, or batch several small tasks into one agent
with a compound brief.

### 18. Explicit model class must be specified in delegation prompts — **Landed** (`execute`'s Model allocation, `iterate`'s table)

Without explicit assignment, spawned agents default to the harness default regardless of task
complexity. Observed in `01-workflow-improvements`: all 6 subagents ran on the default model,
including agents doing 4–8-turn scoped edits over 1–3 files, where the cheap tier was appropriate and
meaningfully cheaper.

Practice: the dispatching skill names a model class per delegation type — the cheap tier for research
and bounded implementation, the capable tier for plan, synthesis, ambiguous architecture, and
high-value review.

### 19. Review agents should apply their own straightforward fixes — **Landed** (`comprehensive-review`'s Resolve or Brief)

The reviewer holds the hottest context on each defect. For a mechanical, localized fix that focused
verification can confirm, dispatching a separate fixer and then a fresh re-reviewer triples the agent
count for a one-line defect. The reviewer applies those fixes itself and closes the finding.

The escalation exceptions are structural: a fix requiring design judgment, touching surfaces beyond
the finding, or depending on intent the reviewer would have to guess. Those get a brief and a
separate fixer, and a *fresh* verifier — not the reviewer, who has committed to a theory of the
defect.

This lesson was previously referenced by lesson 18 before it existed; it now exists.

## Observed From Real Sessions

Harvested from `docs/analysis/`. Each names the session it came from.

### 20. Briefs convert agent direction from decaying to durable — the natural experiment

*Source: garcia-music `iterate` run, session `87e55915`, 4 cycles / 67 subagents / ~11h.*

The strongest evidence in the corpus, and it is causally clean: the `iterate` skill was edited
mid-run, at a single known commit, and the run split 23 subagents before / 44 after.

| Phase | Gate-agent prompt length |
|---|---|
| Cycle 01, guidance inline in `SKILL.md` | 1199 → 213 chars across 7 gates (−82%) |
| Cycles 02–04, guidance moved to `briefs/` passed verbatim | 2833 / 3716 / 3122 chars |

The mechanism is visible in the decay curve. Inline guidance is something the orchestrator re-derives
and compresses at every dispatch, so it degrades under context pressure. A brief is a fixed artifact
it passes unchanged, so it does not. The two "alignment issues" a process-only trace flagged as
orchestrator misbehavior — prompt degradation and a repeated synthesis — are precisely the failure
signature of the briefs-less version.

Honest confound: the user also gave verbal corrections at the same boundary. But a verbal correction
decays as context grows while a brief is re-passed every cycle, so the *sustained* quality across
three later cycles is better explained by the structural change than by the nudge.

This is the empirical backing for the plugin-wide briefs invariant, and the direct argument for
moving brief authorship into `refine` rather than deriving briefs inside a dispatch loop.

**Forward lesson:** the mechanism works, so guard it. A cheap assertion that the briefs exist and are
passed verbatim, before any gated dispatch, would have prevented the entire cycle-01 degradation.

### 21. Cache read dominates cost; output barely moves the bill

*Source: same session, reconstructed from published rates via `tools/cursor/cost_window.py --pricing`.*

Reconstructed spend for the ~82M-token run: ~$29.50, split as:

| Model | $ | cache_read share | output share |
|---|---:|:---:|:---:|
| composer-2.5 | 12.26 | 70% | 14% |
| glm-5.2-high | 8.71 | 65% | 9% |
| sonnet-thinking | 6.80 | 41% | 27% |

The thing you want (output) is 9–14% of spend; the thing you pay for is re-reading accumulated
context. **Model selection for high-volume roles should be driven by cache_read price, not headline
or output price.** Substituting a cheaper cache-read model for the orchestration role in this run cut
that line 58% and the session 17%, on a role whose output quality does not carry the result.

This is the numeric case for `iterate`'s orchestrator pick (cheap cache read *with* strong
long-context fidelity — not the absolute floor) and for keeping orchestrator context lean generally:
context length is a recurring cost, not a one-time one.

### 22. There is no join key from a usage event to a session

*Source: same session, `usage-events-2026-06-26.csv`.*

Three structural facts that make cost attribution hard, all still true:

1. **No join key.** The export's agent/automation ID columns were empty across all rows. Timestamp
   correlation is the only method, and it degrades the moment two sessions overlap in time. On this
   run it was ~97% reliable only because the session was the day's dominant activity.
2. **No dollars in the export.** The cost column reads `Included` or `Free`, never an amount. The
   figure has to be reconstructed from published per-model rates — which is more useful anyway, since
   it splits spend into cache_read / fresh_in / cache_write / output.
3. **Events ≠ agents.** One agent emits many usage events, one per turn. Per-model token totals
   survive this; per-agent attribution does not.

Implication for eval design: cost comparisons must be per-model and per-window, never per-agent, and
any scenario that runs concurrently with other work has unusable cost data.

### 23. Model-selection drift recurs and is expensive

*Source: same session — wrong review model in cycle 03, wrong synthesis model in cycle 04, both
user-corrected.*

Both drifts were the orchestrator substituting its own judgment for a stated per-phase model choice.
The cycle-03 drift alone was the single most expensive event in the run: three review agents on a
premium thinking model, 6.3M tokens in one burst.

Treat model choice per phase as part of the verbatim contract, the same way briefs are — stated in
the dispatching skill, not re-decided per dispatch. This is lesson 18 observed failing in production
rather than in a retro.

### 24. Sub-subagent spawning leaks model selection

*Source: same session — 9 of 67 subagents made their own `Task` calls.*

When a dispatched worker spawns its own agents, the child's model is determined by the parent
worker's prompt, not by the orchestrator's allocation. The intended invariant — the orchestrator is
the sole dispatcher — is unenforceable from the orchestrator's side once a worker has a spawn tool.

Worth watching rather than immediately ruling on: a bounded fan-out inside a worker can be correct.
The signal that matters is whether the sub-spawns are doing work the orchestrator's allocation was
supposed to cost. If a rule is ever added, it belongs in the worker's own skill (where the worker
will read it), not in the orchestrator's.

### 25. Artifacts and git history can silently diverge

*Source: same session — `iteration-01/JUDGEMENT.md` records that the cycle was told to stop after
synthesis, but a consolidation commit exists and the consolidation phases ran.*

The artifact and the history disagree about what happened, and nothing detects it. This is the
failure mode that makes a "record" untrustworthy: not a wrong fact, but an unfalsifiable one.

The general form of the fix is to bind an artifact to the thing it claims, at the moment it claims
it — the same reasoning as the exact-SHA gate. Where an artifact asserts an action produced a commit,
it should name the commit or state its absence.

This is also the strongest argument for `close-out` writing its record *from the artifacts, at the
end*, rather than each phase asserting its own success as it goes.

## Workflow Shape

### 26. A plan is not yet executable work

*Source: this repo's own history, plus the direction-quality data in lesson 20.*

`plan` produces intent, scope, implications, light phasing, and acceptance criteria — "implement the
core behavior" names a phase, not a task. Fusing decomposition, brief authorship, and orchestration
into the execution context costs on four axes: the decomposition is never inspectable before build
spend commits; the orchestrator pays to derive what it then routes; a killed run loses every
undispatched brief; and plan decomposability is discovered by a worker already running against it.

The working shape observed here: the pivot-consolidate-focus run's `briefs/` — four complete
per-agent briefs authored before dispatch — produced the cleanest execution in this repo's history
(the folder has since been closed out to `docs/plans/02-pivot-consolidate-focus.md`; the briefs
themselves are in history at `c21ea12`).
That is the pattern `refine` generalizes.

Watch for the opposite failure: refinement becoming ceremony on single-worker work, where the brief
would be longer than the change (lesson 17). The skip rule exists for exactly that.

### 27. Nothing owned the end of a plan

*Source: this repo's own plan folders.*

Every skill defined what it *wrote*; none defined what *survived*. The result was accretion — plan,
design, provenance, briefs, implementation, review, QA, remediation briefs, all durable by default —
and folders that simply stop, indistinguishable from work in progress.
The post-build-integration folder sat with a plan and an implementation note and no ending for
months.

`close-out` is the fix, and its enabling sentence is the load-bearing part: *the branch history and
the PR are the archive; the record file is the record.* Without that framing an agent will not
delete, because deletion reads as loss.

The first pass at the fix under-specified the collapse — it said what survives (`PLAN.md` plus an
Outcome section) without saying that nothing else does, and the folder survived with it. Agents
closed plans out by *appending* and left the tree standing, `[NEW]-` prefixes and child folders
included. A collapse instruction has to name the end state as a shape, not as a surviving file: one
plan, one file, folder deleted, phases as sections. Absence is not enforceable by describing
presence.

Ordering caveat worth remembering: close-out cannot run inside `post-build`. `REVIEW.md` and `QA.md`
are live inputs to the phases that follow them, and any commit removing them would either break a
later phase or become the trailing commit that unbinds the tested SHA. In pipeline posture close-out
is a post-merge act.

### 28. A skills plugin has no runtime signal that it is stale

*Source: this repo, 2026-07 — plan folders were being created with a `[NEW]-` prefix removed from the
repo months earlier.*

The installed plugin was pinned to the commit immediately before the pivot that removed the backlog
taxonomy. The live cache literally instructed the prefix; the repo did not. Nothing in the session
indicated that the prompt being executed was not the prompt in the repo.

**Every observation of the form "the skill is doing X" is unreliable until the live copy is
checked.** Read the installed skill, not the source, before diagnosing a prompt defect.

The instinctive fix — stamp a version into the artifacts so drift is visible — was considered and
rejected: metadata in artifacts is the thing this workflow keeps removing, and it would report the
drift rather than prevent it. The honest fix is keeping one install path current, and documenting how
to tell which path is live.

## Maintenance Rule

Update this file when executed plans reveal something new about documentation economy, orchestration
cost, phasing, review effectiveness, or where workflow rigor materially improves outcomes.

Do not update it just to restate the current workflow in different words. Do not add a lesson from a
single occurrence without saying so. When a lesson's recommendation lands in a skill, mark it
**Landed** and name where — an implemented lesson left as an open recommendation is how a corpus
turns into a backlog.

## Eval Patterns

*This section grows as actual eval runs produce lessons. Initially empty.*

Record patterns here when eval runs produce non-obvious lessons — e.g. "scenario X consistently shows
higher tool turn counts with model Y," or "quality comparison is unreliable when the reference
implementation is more than 6 months old."

Do not record obvious or generic lessons. Only record findings that would surprise a future evaluator
or change how they interpret results.
