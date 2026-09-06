---
name: refine
description: Turn an approved plan into executable work — decompose it into ordered units and write one complete brief per unit into the plan folder, or report that the plan cannot support briefs yet. Use between `plan` and `execute` when the work is more than one worker can carry.
---

# Refinement

Use this skill to turn a plan into work that can be dispatched without further translation.

`plan` produces intent, scope, implications, light phasing, and acceptance criteria. That is not yet
executable: "implement the core behavior" names a phase, not a task. This skill closes that gap. It
reads the plan and the code, decides what the actual units of work are, and writes each unit's brief
in full — addressed to the agent that will do it, complete enough that the orchestrator can hand it
over verbatim and add nothing.

This skill exists to prevent common failures:

- Briefs are authored inside the dispatch loop, so the decomposition is never inspectable before
  build spend commits to it.
- The orchestrator pays to derive what it then routes — reading the plan and the code deeply enough
  to author briefs is exactly the context it was supposed to stay out of.
- A killed or paused run loses every brief that had not been dispatched yet; nothing on the branch
  says what the remaining work was.
- Whether the plan was decomposable at all is discovered by a worker already running against it.
- Phases that read as sensible prose turn out to overlap, contend for the same files, or depend on
  each other in an order nobody wrote down.
- Briefs get sized to the phase heading instead of to the work, so one worker gets a paragraph and
  another gets a program.
- Scope ambiguity survives into implementation because nobody was ever forced to state a unit's
  boundaries as paths.

The job of this skill is to produce a definitive dispatch list and a complete brief per unit — or,
when the plan cannot support that, to say so specifically and send it back before anything is built.

## When to run

Skip refinement when the change is one bounded slice one worker can carry — `execute`'s ladder rung
one. There, `execute` authors inline at dispatch time as it does today, and a refinement pass is
pure ceremony: the brief would be longer than the work.

Run it when any of these hold:

- The work splits into two or more executable units.
- Units will run in parallel, so their boundaries have to be disjoint rather than merely different.
- The run is expected to span sessions, be resumed, or be picked up by a different agent.
- Execution will be dispatched headlessly, where nobody is present to repair a thin brief.
- The plan's phases are phrased as outcomes ("integrate and verify") rather than as work.

When in doubt on a two-unit change, skip it. Refinement earns its cost on decomposition risk, not on
artifact count.

## Recon

Do not decompose from the plan text alone. The whole value of a brief is that it names real paths,
real contracts, and real done evidence, and none of those are in `PLAN.md`.

Read the plan and any `DESIGN.md` first, then survey the code surface the plan implies: which files
and modules each phase would touch, where the contracts it cites actually live, what already exists
that the plan assumes doesn't (or vice versa), and which surfaces two phases would both want to
edit. Keep this pass shallow and wide — you are mapping ownership, not implementing.

Recon is also the first honest test of the plan. A phase whose code surface you cannot locate is a
phase whose brief you cannot write.

## Decomposition

The unit of work is what one worker can hold and finish: one main contract, a file surface it can
read without exhausting its context, and a done state it can verify itself.

Judge with these proxies:

- How many files or modules must be read before the change is well-understood?
- Is this implementing one fixed contract, or several interacting ones?
- Is it local to one subsystem, or spread across surfaces?
- Can it proceed without waiting on another unit's output?
- Does it still contain meaningful ambiguity a worker would have to resolve by guessing?
- Is its verification straightforward, or cross-cutting?

Two hard constraints:

- **Units that may run in parallel own disjoint paths.** Ownership is stated as paths in the brief,
  and two concurrent units may not name the same file. If they must, they are one unit or they are
  sequential — decide which, and record the dependency.
- **A unit that cannot be named clearly is not a unit.** Do not decompose further to hit a count.
  Fewer, well-bounded units beat more, weakly justified ones.
- **A unit whose done evidence depends on waiting on a long-running subprocess (roughly
  5-10+ minutes) splits at the kickoff boundary.** One unit does setup and starts the
  process, then hands off a short structured summary; a second, fresh unit waits for/verifies
  the result and reports. Folding the wait into the same unit that did the setup produces a
  busy-poll tail and, if the run stalls and gets resumed, a full cache re-embed on resume —
  both of which a clean handoff avoids entirely.

Order the units by real dependency, not by narrative convenience. State for each what it depends on
and what may run alongside it.

## Brief anatomy

One brief per unit, at `docs/plans/<NN>-<slug>/briefs/<NN>-<slug>.md`, written from
`templates/brief.md`. Each brief is addressed to the worker, not to the orchestrator, and is
self-sufficient: a clean agent handed only this file and the repo can do the work.

A brief carries:

- **Consumer and boundaries.** Who this is for, the paths it owns, and what it must not touch —
  including whether it commits or leaves changes in the working tree.
- **Required reading, in order.** Specific files and the specific sections that are binding, not a
  reading list of everything nearby.
- **The goal**, in a sentence or two, in the plan's own terms.
- **The contract it must satisfy**, cited from `PLAN.md`/`DESIGN.md` or from the code, not
  paraphrased into new words. Where a contract is settled, say it is settled.
- **The change spec** — what to add, remove, or restructure, at the level of decisions the worker
  should not have to re-derive, and no lower. It is not a diff.
- **Done evidence** — checks the worker can actually run, expressed as commands where possible, and
  observable statements where not.
- **The report-back shape**, always including the standing instruction: report contradictions
  between this brief and the underlying contracts rather than resolving them silently.

Write to the brief's own consumer, in full, once. The plugin-wide invariant depends on it: context
authors write once, addressed to the consumer; orchestrators route verbatim, never paraphrase. A
brief that assumes the orchestrator will explain it has already broken that.

Guard against the failure this skill could become: a brief with no named consumer is ceremony, and a
brief for work nobody will delegate is worse.

## The dispatch list

Rewrite `PLAN.md`'s Execution Phases from light indicative phasing into the definitive dispatch
list. Each entry names its unit, its brief file, its dependencies, and what may run alongside it.

This replaces the plan's phasing rather than sitting beside it. No second file, no dispatch table
somewhere a later reader has to hunt for, and no status column — the list says what the work is and
in what order, not how far along it is.

## Executability verdict

End with one of two outcomes, stated plainly.

**Proceed.** The units are named, the briefs are written, the order is recorded. Say how many units,
which may run in parallel, and anything the executing orchestrator should know that is not in a
brief.

**Bounce.** The plan cannot support briefs: contracts too weak to implement against, boundaries that
cannot be decided without inventing scope, phases that cannot be ordered because their dependency is
genuinely unknown, or acceptance criteria that no done evidence would satisfy. Do not paper over it
and do not invent the missing decisions — record the specific gaps in `PLAN.md`'s Open Questions,
naming what is missing and what it blocks, and return to `plan`.

Bouncing is a success condition, not a failure. This is a cold read of the plan by a context that
must actually decompose it, and it happens before build spend.

## Workflow

1. Read `PLAN.md`, any `DESIGN.md`, and the stable docs the plan grounds itself in — cold, from the
   committed artifacts, even if `plan` just ran in this session.
2. Apply the skip rule. If the work is one bounded slice, say so and stop; `execute` handles it
   inline.
3. Run the recon pass over the code surface the plan implies.
4. Decompose into ordered units with disjoint ownership, and record their dependencies.
5. Write each unit's brief into `briefs/`, from the template. Write them as you settle each unit —
   do not batch to the end.
6. Rewrite `PLAN.md`'s Execution Phases as the definitive dispatch list.
7. Give the executability verdict. On a bounce, record the gaps in Open Questions and stop.
8. Commit the briefs and the plan update together.

## Rules

- Refine only from an existing plan. Refinement does not add scope; where it finds scope missing, it
  bounces rather than filling the gap.
- Do not implement. Reading code is recon; changing it is the next stage's job. The one exception is
  the plan folder's own artifacts.
- Every brief names a consumer. A brief nobody will be handed should not exist.
- Units that may run in parallel own disjoint paths, stated as paths.
- Prefer fewer, clearly bounded units over more, weakly justified ones. If you cannot name a unit,
  do not split it out.
- Cite contracts; do not paraphrase them into new words. Paraphrase is the loss this stage exists to
  prevent.
- Done evidence must be runnable or observable. "Works correctly" is not done evidence.
- No status, scores, or progress fields anywhere — not in the briefs, not in the dispatch list.
- Briefs are run-scoped. They are committed for traceability and resumability, and close-out deletes
  them when the change lands; write them to be useful now, not to be archived.
