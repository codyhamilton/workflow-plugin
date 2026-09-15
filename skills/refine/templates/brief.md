# Brief: <phase>-<NN> — <unit name>

Consumer: <the worker that will do this>.
Owned paths: `<path>`, `<path>`. Touch nothing else.
Commits: <"Leave changes in the working tree." | "Commit to the current branch when done evidence passes.">
Depends on: <unit(s), or nothing>.
Runs alongside: <unit(s) with disjoint paths, or nothing>.
Budget: <N files to read, about N lines to change, N tool turns>. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `<path>` — <the section that is binding>
2. `<path>` — <what you are changing>

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

<One or two sentences in the design's terms: what this unit is for, not how.>

## Contract

<Cited from DESIGN.md or the code, by section or quotation. Say which decisions are settled.>

## Changes

<The decisions the worker should not have to re-derive, and no lower. Not a diff.>

### Keep untouched

<What inside the owned paths must survive, and why.>

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `<runnable check>` → <expected result>
- <observable statement>

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
