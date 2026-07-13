# Post-Build — Reference

Not loaded during normal execution. Consumers: `workflow-tuning`, adapter authors, and anyone revising this skill later. Holds the prose that argues the stage's design is *correct*, as distinct from `SKILL.md`, which holds only what changes an executing agent's behavior in an unspecified situation.

## Origin

Distilled from `codyhamilton/garcia-music`: its `post-build-automation` skill (the first repo adapter, written for a Cursor Automation trigger) and the deploy-babysit and QA phases of its `orchestration` skill. The portable semantics were lifted here; the repo kept its adapter — deploy scripts, staging URLs, seeded identities, model routing. That split is deliberate: the adapter declares this plugin authoritative for artifact semantics, and this skill declares the adapter authoritative for repo mechanics, so neither can drift into the other's territory silently.

## Why the stage right-sizes instead of always running full

A uniform full stage (recovered intent → review → QA matrix → deploy babysit → browser QA) is correct for planned functional work and wrong for a one-line docs fix or a CI-only tweak. Burning browser QA and plan-folder ceremony on non-functional diffs teaches the automation the wrong lesson (that every PR is product risk) and wastes the budget that should be reserved for changes that can ship broken behavior. Classification by intent source, surface, and size is the single switch: over-classify as functional when unsure, never let a docs majority hide a behavioral hunk, and record the judgment in the report so skips are auditable rather than silent.

## Why no-plan is tiered, not uniform

`RECOVERED-INTENT.md` exists so a human or agent that skipped the workflow still gets a real review of **functional** risk — not a rubber stamp of behavior. Inventing a plan folder and full QA path for every markerless PR recreates ceremony the author deliberately skipped, usually for changes that never needed it. Ad-hoc trivial/small non-functional work may leave no plan folder; functional no-plan work still recovers intent and reviews for real. The anti-rubber-stamp rule is about behavior risk, not about forcing artifacts.

## Why the orchestrator may absorb trivial non-functional work

Independence is load-bearing when a second context must challenge functional claims or verify someone else's fix. It is not load-bearing for skimming a docs diff and reading CI. Mirroring execute's "delegation is a judgment call," absorption keeps the parent lean and cheap on the cases where a cold worker's spin-up costs more than the work. Hard limits keep absorption from eating the stage: no absorbed functional review, no absorbed remediation verification, no absorbed browser QA or SHA proof.

## Why QA is only for functional / driveable need

Browser QA proves user-observable behavior on a live deployment. Non-functional changes have no such behavior to prove; internal-only functional changes may need review and green checks without a UI matrix. Running QA anyway either tests nothing useful or forces an undriveable matrix that looks like coverage. Skipping QA is honest when classification says so; missing an **applicable** QA case is still a failed gate.

## Why required checks are read once, at the end of the work

Proactive deploy babysitting (poke, redeploy, re-wait until something looks green) races CI and invents progress, and polling checks between phases buys nothing — the checks that matter are the ones on the final candidate SHA, which does not exist until review and remediation have settled the code. So the stage reads required checks exactly once, after the last code-changing phase, waiting for conclusion without interfering. Fixing a failed check is itself conditional: one bounded cycle, only for non-trivial functional/mixed changes whose failure this PR caused. On trivial or non-functional changes a failing check is cheaper for a human to triage than for the stage to guess at — leaving it failing and saying so is the honest outcome, not a shortfall. Deploy proof remains mandatory **when QA needs a live URL** — checks-green is not a substitute for exact-SHA proof of the URL under test.

## Why the exact-SHA gate is absolute

Branch-level "deployment ready" signals race: the readiness a wait script observes may belong to a previous push, a queued sibling, or a rebuild of an older commit. QA against the wrong build is worse than no QA — it stamps PASS onto behavior the merge will not contain. Proving that a specific deployment's git metadata matches the candidate SHA, resolving that deployment's own URL, and health-checking that same URL closes every substitution path (branch aliases, staging defaults, environment-variable URLs) through which the wrong build sneaks into the matrix.

## Why QA results are never committed

A results commit created after testing has a different SHA than the commit that was tested, so merging it merges an untested commit — the gate would invalidate itself in the act of recording its own success. Even a docs-only trailing commit breaks the SHA binding the whole stage exists to prove. Results therefore live in the PR conversation and automation output, which bind to the tested SHA by reference instead of by mutation. `QA.md` — the matrix — is committed *before* the candidate SHA precisely so the artifact record stays complete without a trailing write. When QA is skipped, there is no matrix to commit.

## Why the reviewer fixes in place, and delegated remediation gets fresh verification

The reviewer holds the hottest context on each defect. For a mechanical, localized fix that focused verification can confirm, dispatching a separate fixer and then a fresh re-reviewer triples the agent count for a one-line defect — the loop cost exceeds the independence benefit, so the reviewer applies those fixes itself and closes the findings in its own run. The generation/acceptance split becomes load-bearing exactly where the fix requires judgment: for structural findings the reviewer authors a brief (it writes the fix instruction because it has the context) but does not attempt the fix, and once a delegated fixer has committed to a theory of the fix, a clean verifier — not the reviewer, who committed to a theory of the defect — reads only the delta and the evidence. Same split the plugin uses at the divergence bar and the plan Challenge pass, applied only where it pays.

## Why worker prompts are standing briefs

An orchestrator that hand-derives each worker's prompt pays twice: the derivation bloats its own context with instructions only the worker needs, and the instructions themselves drift — each run re-invents phrasing, drops a rule, or paraphrases the skill it should be routing. Shipping the per-phase briefs beside the skill (`briefs/`) makes the worker instructions versioned artifacts: the orchestrator routes a file reference plus a short parameter block, review of the instructions happens in the plugin repo, and every run dispatches the same discipline. The reviewer needs no such brief because `comprehensive-review` — a full skill — already is one. Per-finding remediation briefs are different animals: they are run-specific context authored by the reviewer into the plan folder; the standing `remediation-fixer.md` brief carries only the discipline that never changes between findings.

## Why QA runs after review

QA exercises the deployed build, so every code change after QA unbinds its results from the SHA under test. Review and remediation are the phases most likely to change code; running them first means QA tests settled code once, instead of being rerun (or silently invalidated) by a post-QA fix. The same logic pins the checks gate after remediation and QA planning: gates belong after the last write.

## Why the loops are bounded

One remediation cycle plus one fresh verification, one QA remediation cycle, one checks fix cycle, one relaunch of a dead worker. Unbounded "loop until green" burns budget on exactly the changes least likely to converge — a second failed cycle is strong evidence the problem is architectural or environmental, which is human territory. Bounded loops make the stage's cost predictable enough to run on every PR, and make a stop with a specific handoff the honest terminal state rather than an embarrassing one.

## Why discovery never tie-breaks

Folder numbers are best-effort ordering, not identity (two agents branching from the same base can pick the same `NN`), and modification time measures the last touch, not relevance. Any tie-break heuristic converts "the automation reviewed the wrong plan" from an impossible state into a silent one. Requiring the marker, then exactly one diff-derived candidate, then an explicit human-supplied path keeps wrong-plan review structurally unreachable at the cost of an occasional stop-and-ask — the cheap side of that trade.

## Why the stage never merges

Merging is the only irreversible act in the pipeline and the one with no downstream backstop — every other phase's mistake is caught by a later phase or by the merge gate itself. Keeping merge authority outside the stage means the worst a wrong PASS can do is mislead a decision-maker, not ship. If auto-merge is ever wanted, it should be a declared opt-in (the posture pattern), never an inferred default.
