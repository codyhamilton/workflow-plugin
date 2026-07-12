# Post-Build — Reference

Not loaded during normal execution. Consumers: `workflow-tuning`, adapter authors, and anyone revising this skill later. Holds the prose that argues the stage's design is *correct*, as distinct from `SKILL.md`, which holds only what changes an executing agent's behavior in an unspecified situation.

## Origin

Distilled from `codyhamilton/garcia-music`: its `post-build-automation` skill (the first repo adapter, written for a Cursor Automation trigger) and the deploy-babysit and QA phases of its `orchestration` skill. The portable semantics were lifted here; the repo kept its adapter — deploy scripts, staging URLs, seeded identities, model routing. That split is deliberate: the adapter declares this plugin authoritative for artifact semantics, and this skill declares the adapter authoritative for repo mechanics, so neither can drift into the other's territory silently.

## Why the exact-SHA gate is absolute

Branch-level "deployment ready" signals race: the readiness a wait script observes may belong to a previous push, a queued sibling, or a rebuild of an older commit. QA against the wrong build is worse than no QA — it stamps PASS onto behavior the merge will not contain. Proving that a specific deployment's git metadata matches the candidate SHA, resolving that deployment's own URL, and health-checking that same URL closes every substitution path (branch aliases, staging defaults, environment-variable URLs) through which the wrong build sneaks into the matrix.

## Why QA results are never committed

A results commit created after testing has a different SHA than the commit that was tested, so merging it merges an untested commit — the gate would invalidate itself in the act of recording its own success. Even a docs-only trailing commit breaks the SHA binding the whole stage exists to prove. Results therefore live in the PR conversation and automation output, which bind to the tested SHA by reference instead of by mutation. `QA.md` — the matrix — is committed *before* the candidate SHA precisely so the artifact record stays complete without a trailing write.

## Why remediation is finding-scoped and re-review is fresh

The reviewer holds the hottest context on each defect, so it authors the fix instruction (the remediation brief) — but the agent that raised a finding is the worst judge of whether the fix resolved it, having already committed to a theory of the defect. Splitting fix (scoped strictly to accepted findings, so review pressure cannot become scope creep) from verification (a clean context reading only the delta and the stable artifacts) is the same generation/acceptance split the rest of the plugin uses at the divergence bar and the plan Challenge pass.

## Why the loops are bounded

One remediation cycle plus one fresh re-review, one QA remediation cycle, one relaunch of a dead worker. Unbounded "loop until green" burns budget on exactly the changes least likely to converge — a second failed cycle is strong evidence the problem is architectural or environmental, which is human territory. Bounded loops make the stage's cost predictable enough to run on every PR, and make a stop with a specific handoff the honest terminal state rather than an embarrassing one.

## Why discovery never tie-breaks

Folder numbers are best-effort ordering, not identity (two agents branching from the same base can pick the same `NN`), and modification time measures the last touch, not relevance. Any tie-break heuristic converts "the automation reviewed the wrong plan" from an impossible state into a silent one. Requiring the marker, then exactly one diff-derived candidate, then an explicit human-supplied path keeps wrong-plan review structurally unreachable at the cost of an occasional stop-and-ask — the cheap side of that trade.

## Why the stage never merges

Merging is the only irreversible act in the pipeline and the one with no downstream backstop — every other phase's mistake is caught by a later phase or by the merge gate itself. Keeping merge authority outside the stage means the worst a wrong PASS can do is mislead a decision-maker, not ship. If auto-merge is ever wanted, it should be a declared opt-in (the posture pattern), never an inferred default.
