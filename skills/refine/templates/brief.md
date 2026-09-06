# Brief: <NN> — <unit name>

Consumer: <the worker that will do this — implementation worker, fixer, reviewer, …>.
Owned paths: `<path/glob>`, `<path/glob>`. Do not touch anything else.
<Commit discipline: e.g. "Do not run git commit or push — leave changes in the working tree." or
"Commit to the current branch when done evidence passes.">
Depends on: <other unit(s), or "nothing — may start immediately">.
Runs alongside: <other unit(s) that own disjoint paths, or "nothing">.

## Required reading, in order

1. `<path>` — <what in it is binding, and which section>
2. `<path>` — <what in it is binding>
3. `<path>` — <what you are changing>

## Goal

<One or two sentences, in the plan's own terms. What this unit is for, not how to do it.>

## Contract

<The contract this unit must satisfy, cited from PLAN.md / DESIGN.md / the code — quoted or
referenced by section, not paraphrased into new words. Say explicitly which decisions are settled
and not open for re-litigation.>

## Changes

### <Area or file group>

<What to add, remove, or restructure, at the level of decisions the worker should not have to
re-derive. Not a diff, and not a list of edits — the decisions plus enough shape to act on them.>

### <Area or file group>

<…>

### Keep untouched

<Anything inside the owned paths that must survive unchanged, and why — the things a worker would
otherwise reasonably tidy away.>

## Done evidence

- `<runnable check, e.g. a grep, a build, a test invocation>` → <expected result>
- <observable statement that can be checked by reading the result>

## Report back

A short summary: what you changed, anything you deviated from in this brief and why, and any
contradiction you found between this brief and the contracts it cites. **Do not resolve
contradictions silently — report them.**

If you find a non-trivial bug outside what your own done evidence requires — real debugging,
not a one-line fix, and not blocking your own contract — do not fix it here. Report it
(symptom, location, root cause if you found one) and leave it; the orchestrator will dispatch
a small, fresh agent to resolve it.
