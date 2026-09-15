---
name: refine
description: Turn the next phase of a signed-off design into dispatchable work — one complete brief per unit, written against the code as it now stands — or bounce the design with the gaps named. Use before each phase is built; skipped when the phase is one unit.
---

# Refine

Refine one phase: the next phase in `DESIGN.md`'s order that has no Units list. Read `DESIGN.md`, `IMPLEMENTATION.md` as it stands, and the previous phase's Carried section, cold from the committed artifacts, even if `design` or `execute` just ran in this session. Write briefs against the code the earlier phases actually left, not the code the design imagined.

## Outcome

- The phase is decomposed into units. A unit is what one worker can hold and finish: one contract, a file surface it can read without exhausting its context, done evidence it can check itself, and a budget it can count.
- Units that may run in parallel own disjoint paths. Two units that must touch the same file are one unit or are sequential.
- Each unit has a brief at `briefs/<phase>-<NN>-<slug>.md` from `templates/brief.md`, addressed to the worker, self-sufficient: a clean agent handed only the brief and the repo can do the work.
- The phase's Units list is written under that phase in `DESIGN.md`: unit, brief path, dependencies, what may run alongside. No status column.
- The previous phase's carried items are placed: absorbed into a unit of this phase, or bounced.
- On the first refinement of a design, every phase has had one coarse check: its surfaces can be located, its contracts are stated, its outcome is provable, its dependency order is real. No briefs beyond this phase.
- A verdict is stated. **Proceed**: unit count, what may run in parallel, anything the orchestrator needs that is not in a brief. **Bounce**: the specific gaps, recorded in `DESIGN.md`'s Open Questions.
- The briefs and the design update are committed together.

## Bounce

Bounce when the phase cannot support briefs: a contract too weak to implement against, a boundary that cannot be set without inventing scope, an outcome no done evidence would satisfy, or a carried item that touches a contract, a boundary, or a phase outcome. Do not fill the gap; return to `design`. Bouncing is a success condition.

## Skip

A phase one worker can carry is not refined; `execute` briefs it inline. When in doubt on two units, skip.

## Rules

- Refine only from an existing design; add no scope.
- Do not implement. Code is read for recon; the plan folder's artifacts are the only writes.
- Cite contracts; never paraphrase them.
- Done evidence is runnable or observable. "Works correctly" is not evidence.
- A unit that cannot be named clearly is not a unit. Do not split to hit a count.
- A unit whose done evidence waits on a long-running process (roughly ten minutes or more) splits at the kickoff: one unit starts it and hands off a short summary; a fresh unit verifies the result.
- Every brief names its consumer. No status, scores, or progress fields anywhere.
