# Workflow Design Principles

The arguments that recur across the skills in this plugin, written once. Consumers: anyone revising
a skill, adding a new one, or deciding whether a proposed rule is worth its tokens.

This file holds **persuading-why** — the prose that argues a design is correct. It is deliberately
not in any `SKILL.md`, because a skill body should hold only what changes an executing agent's
behavior in an unspecified situation. The test, applied per sentence: *if the agent already trusted
the rule, would this sentence change what it does?* Yes → it belongs in the skill. No → it belongs
here.

Two neighbours, easily confused:

- `reference.md` (beside this file) is the **observed lessons** corpus — numbered, empirical, drawn
  from real execution traces. This file is the **design** corpus: the reasoning the skills are built
  on, whether or not a trace has confirmed it yet.
- `README.md`'s operating hypotheses are the **falsifiable** subset of these principles, each naming
  its validation route. Where a principle here is genuinely untested, the hypothesis list is where
  that is admitted.

A principle stops being useful the moment it becomes a slogan applied without judgment. Each entry
below names where it is instantiated and — where one exists — where it is deliberately *not*.

---

## 1. Orienting-why belongs in the skill; persuading-why belongs here

A skill that states the failures it prevents helps an agent fill gaps the prompt never anticipated:
faced with an unspecified situation, it can reason from what the rule is for. A skill that argues its
own correctness spends context on convincing a reader who has already complied.

Instantiated by: the "This skill exists to prevent…" preamble every skill carries, and by the
existence of this file.

The failure this guards against is not verbosity — it is a skill body that reads as a defence of
past decisions rather than as instructions.

## 2. Cold readers keep artifacts honest

An agent that has been reasoning about a change for a while stops seeing its own gaps. Every quality
gate in this plugin is the same move from a different angle: force a context that did not author the
thing to work from the artifact alone.

Instantiated by: `plan`'s Challenge pass and its held checkpoint; the rule that `execute` reads the
plan cold from committed artifacts even when `plan` just ran in the same session; `refine`'s
executability verdict, which is a cold read by a context that must actually decompose the plan;
`comprehensive-review`'s independence; the plan-sufficiency judgment, which is cold-reader pressure
recorded as data.

This is also why one-shot composition dispatches `plan` and `execute` as separate contexts rather
than fusing them. A fused context would still produce both artifacts and would silently destroy the
pressure that makes them good.

## 3. Posture is declared, never inferred

Where a workflow's behavior depends on whether a human is reachable, or whether a downstream stage
exists, that fact is declared by the invoker — not sniffed from a TTY, an environment variable, or
the shape of the change.

Instantiated by: `plan`'s interactive/headless; `execute`'s terminal/pipeline review posture;
`close-out`'s terminal/pipeline placement; `iterate`'s rule that it always declares posture
explicitly when dispatching a composed skill.

Inference fails in both directions and fails silently. A misdetected environment either skips a
checkpoint a human actually wanted or stalls a headless run waiting for someone who was never there.
A declaration is auditable; a heuristic is not. The corollary is that every posture needs a stated
default for when nobody declares — and the default is always the safe one: assume a human is
reachable, assume no downstream stage exists.

## 4. Briefs beat paraphrase

**Context authors write once, in full, addressed to the consumer; orchestrators route verbatim,
never paraphrase.** This is the plugin's widest invariant.

Instantiated by: `refine` authoring implementation briefs and `execute` routing them;
`comprehensive-review` authoring remediation briefs and `post-build` routing them by path;
`post-build` and `iterate` both routing their standing worker briefs from `briefs/` by path.

Paraphrase loses precision at every hop, and the loss compounds silently — nobody can see what was
dropped. Authoring at the point of hottest context and routing untranslated is the only mechanism
that makes the hop lossless. The author writes the brief because the author knows the thing; the
orchestrator does not restate it because restating is where the loss lives.

Two corollaries:

- **The static/dynamic split.** A worker's prompt has two parts. *Static direction* is the worker's
  own registered skill, which only the worker loads — the instruction text never enters the
  orchestrator's context at all. *Dynamic context* is the handful of lines only this run knows:
  paths, SHAs, URLs, finding IDs. The orchestrator authors exactly that and nothing more.

  **Static direction is a file, not a registered skill.** `post-build`'s worker phases were briefly
  promoted to registered dispatch-only skills, on the theory that registration bought better
  loading behavior on both sides and that a skill name resolves anywhere while a path depends on
  install location. Both halves were wrong, and reverting them is the cleaner design. A brief is
  read, not invoked, so it needs no description, no invocation gating, and no registry entry — a
  worker told to read an absolute path does so unconditionally, where a skill it must decide to
  load is a decision that can go the other way. Registration also charges rent the whole time:
  every registered skill's name and description sit in every session's context, so four workers
  nobody outside `post-build` can invoke were taxing every unrelated conversation. The path
  argument dissolves once the orchestrator resolves `briefs/<name>.md` against its own skill
  directory before dispatching — it knows where it was loaded from, which is exactly the fact the
  worker lacks. Registration earns its cost only for an entry point a human or a peer skill names;
  worker direction is neither.
- **Authorship moves upstream where it can be reviewed.** Deriving briefs inside the dispatch loop
  works, but the decomposition is never inspectable before build spend, and a killed run loses every
  brief not yet dispatched. `refine` exists to move that authorship into its own reviewable stage.
  The trade is real and worth naming: `refine`'s briefs are colder than `execute`'s would have been,
  which is why `refine` does its own recon and why a worker's reported contradiction amends the
  brief file rather than being resolved in conversation.

The guard: a brief with no named consumer is ceremony. The invariant is authorship plus verbatim
routing; the file is only the medium.

## 5. Generation and acceptance split across agents

Criteria given to a generator become a target it games. Criteria given to a filter stay a filter. So
where a bar must actually hold, the agent that produces the candidate and the agent that judges it
are different agents, and only the judge holds the tests.

Instantiated by: `iterate`'s divergence bar (a licensed planner generates, a clean approver holds
the three tests — and the split between `briefs/challenger-license.md` and
`briefs/divergence-approver.md` *is* the split); `plan`'s Challenge pass; `post-build`'s rule that a
fresh verifier, never the reviewer and never the fixer, rules on a delegated remediation.

Deliberately *not* applied where the loop cost exceeds the independence benefit:
`comprehensive-review` fixes mechanical, localized, obviously-correct findings in place, because
dispatching a separate fixer and a fresh re-reviewer triples the agent count for a one-line defect.
The split becomes load-bearing exactly where the fix requires judgment — which is why the reviewer
still authors the brief for structural findings (it holds the context) but does not attempt them.

The second move that gives such a bar teeth is **inverting the default**: asked to find a materially
different approach, an agent will always return one and rationalize it. Making "I cannot find a
genuine fork" the expected, valid answer is what converts the bar from decoration into a gate.

## 6. Loops are bounded

One remediation cycle plus one fresh verification. One QA remediation cycle. One checks fix cycle.
One relaunch of a dead worker. A fixed relay of hardening passes, never "review until clean".

Instantiated by: `post-build` throughout; `iterate`'s harden relay and its cycle cap;
`execute`'s rule against repeated external review loops.

Unbounded loops burn budget on exactly the changes least likely to converge. A second failed cycle
is strong evidence the problem is architectural or environmental — human territory. Bounded loops
make a stage's cost predictable enough to run on every change, and they make *stopping with a
specific handoff* the honest terminal state rather than an embarrassing one.

## 7. Right-size by classification, not by uniformity

A uniform full process is correct for planned functional work and wrong for a one-line docs fix.
Burning review, QA, and plan ceremony on a non-functional diff teaches the automation that every
change is product risk and spends the budget that belonged to changes that can ship broken behavior.

Instantiated by: `post-build`'s intent × surface × size classification and its absorb path;
`execute`'s sizing ladder and its "delegation is a judgment call" framing; `refine`'s skip rule;
`plan`'s rule that `DESIGN.md` is written only when it reifies something.

Two disciplines make right-sizing safe rather than merely cheap. **Over-classify when unsure** — a
docs majority must not hide a behavioral hunk. And **record the judgment**, so a skip is auditable
rather than silent. The limits matter as much as the switch: `post-build` may absorb a docs skim but
may never absorb independent review of functional change, verification of a delegated fix, browser
QA, or SHA proof.

## 8. Nothing in the repo carries status

A plan folder existing on a branch means the work is being built or was built — nothing else. There
is no status file, no folder-name taxonomy, no schedule doc, no completion marker.

Instantiated by: the plan-folder convention; the absence of `STATUS.md` and `ROADMAP.md`;
`close-out`'s rule that a closed plan is not *marked* closed — it is simply a file instead of a
folder.

The removed system (an open-program folder prefix, numeric renumbering ceremony, a parent-program
hierarchy, a canonical schedule file) was a shadow work tracker built for a repo-as-backlog mental
model. The PR and the issue tracker already carry status; a second encoding of it in file names
duplicates them and then drifts from them. Deferred and speculative work belongs to design-intent
docs and tracker issues, which are built for exactly that job.

The same instinct returns in new costumes and should be refused each time: a version stamp in an
artifact, a progress column in a dispatch list, a score on a review. Metadata in artifacts is the
thing this workflow keeps removing. When an artifact's staleness is the real problem, the honest fix
is to keep the source current, not to teach the artifact to complain.

## 9. Discovery never tie-breaks

When more than one candidate answers "which plan folder is this?", the stage stops and asks. It
never picks by folder number, modification time, or lexical order.

Instantiated by: `post-build`'s marker-first discovery with a single-candidate diff fallback;
`comprehensive-review`'s "the marker is the only mechanical location mechanism"; `plan`'s rule that
`NN` is best-effort ordering and nothing may locate a folder by it.

Numbers are not identity: two agents branching from the same base can independently pick the same
`NN` with no way to coordinate before a PR exists, and making the number a locator would require a
lock, a registry, or a human. Modification time measures the last touch, not relevance. Any
tie-break heuristic converts "the automation reviewed the wrong plan" from an impossible state into
a silent one. An occasional stop-and-ask is the cheap side of that trade.

## 10. Gates bind to exact identity

A gate that proves something about "the branch" or "the latest deployment" proves nothing about the
commit that will merge.

Instantiated by: `post-build`'s exact-SHA deploy proof, its single end-of-work checks read on the
candidate SHA, and its absolute rule that no commit follows the tested commit — which is why QA
results are never committed, why `QA.md` is committed *before* the candidate SHA, and why
`close-out` runs after merge in pipeline posture rather than at the end of the stage.

Branch-level readiness signals race: the readiness a wait script observes may belong to a previous
push, a queued sibling, or a rebuild of an older commit. QA against the wrong build is worse than no
QA — it stamps PASS onto behavior the merge will not contain. And a results commit created after
testing has a different SHA than the commit that was tested, so recording success would invalidate
the gate in the act of recording it. Results therefore live in the PR conversation and automation
output, which bind to the tested SHA by reference instead of by mutation.

The ordering follows from the same rule: gates belong after the last write. Review settles the code,
then QA tests settled code once, then checks are read on what remains.

## 11. An artifact's first job is to be a forcing function

Requiring an artifact guarantees the activity happened. The handoff payload is secondary.

Instantiated by: `execute`'s progressive `IMPLEMENTATION.md` (which forces the run to stay
resumable); `refine`'s briefs (which force scope to be stated as paths); `iterate`'s per-cycle
artifacts.

Three consequences. **Specify the seam, not the substance** — require only what the consumer must
mechanically locate (a branch name, code pointers, a brief path, N separable options) and mandate
qualitative prose everywhere else. **Never add score or status metadata**, which invites Goodhart
gaming. And **every artifact names a consumer or a gate**; one with neither is ceremony, which is
also why `PROVENANCE.md` is optional — a headless run has no Q&A to record, and inventing a
transcript that never happened is ceremony wearing provenance's clothes.

The corollary at the other end: an artifact whose consumers are gone has finished its job. That is
what makes `close-out` safe. The branch history and the PR are the archive; the single record file
`close-out` leaves behind is the record. Nothing deleted at close-out is lost — what is removed is
the obligation on every future reader to sift it.

## 12. Artifacts are written for their consumer, mechanically

Where the next reader is a machine or a headless agent, the artifact's shape is a contract, not a
style preference.

Instantiated by: `plan`'s QA-drivable acceptance criteria (entry point → action → observable
result), which is exactly what a computer-use QA agent needs to derive test steps without asking;
`comprehensive-review`'s verdict enum, which a pipeline branches on without interpretation; the
`Workflow-Plan:` marker; `post-build`'s final output schema.

Anything vaguer forces the consumer to guess or to stall waiting for a clarification a headless
pipeline cannot provide. The reverse also holds: where the consumer is a human reading years later,
prose beats structure, and imposing a schema is the same mistake in the other direction.

## 13. Prior work is the cheapest spec

Existing code is the most precise specification available. A challenger handed real code diverges
meaningfully; one handed a prose summary diverges cosmetically.

Instantiated by: `iterate`'s sequential candidates, each receiving prior builds as working code;
its harden relay, where each pass receives its predecessors' findings; `close-out`'s reliance on
the actual artifacts rather than the closing agent's memory of the run.

This is also why losing branches are never deleted — they are the reified alternatives and the
richest provenance the exercise produces.

## 14. Sequential relays diverge; parallel fan-outs mode-collapse

Parallel reviewers with separate focuses are best-of-n sampling with no divergence pressure: they
converge on the same obvious subset and miss the long tail. Hand each pass its predecessors'
findings and tell it to push past them, and the passes diverge by construction.

Instantiated by: `iterate`'s harden relay and its sequential candidates.

Deliberately *not* applied where breadth is the point rather than depth:
`comprehensive-review` runs two or three parallel lenses on a cross-cutting change, because
different lenses are different questions, not competing answers to the same one. The distinction is
whether the agents are sampling the same space (relay) or partitioning it (fan-out).

Sequential also buys what parallel cannot: no write contention, an accumulating record that stays
consistent, and each pass reviewing the corrected state its predecessors left.

## 15. Convergent phases must verify, not just capture

Every phase that opens options is cheap to get wrong; the phase that closes them is not. An additive
merge of separately-reviewed parts produces a whole no review has ever seen, and the seam is exactly
where breakage and duplication live.

Instantiated by: `iterate`'s split of consolidation into capture (additive) then harden (verifies
and locks); `post-build`'s fresh verification of delegated remediation; `execute`'s verification of
the full slice against the plan, not just of each worker's output.

A soft base compounds — everything later builds on it. The bar at a convergent phase is
*deliverable*, not *design*: does it work end to end, is it resilient, is it free of the graft's
duplication. And it must self-limit, or it relitigates the decision that produced it.

## 16. Criteria are discovered by building, not declared up front

For work whose success conditions are not knowable in advance, scoring candidates against a checklist
written before anything existed measures the wrong thing.

Instantiated by: `iterate`'s `OUTCOMES.md`, revised each cycle by the synthesis agent from what the
builds revealed, with the yardstick written before the selection so the selection cannot bend it.

Deliberately *not* applied to ordinary planned work, where acceptance criteria are written up front
on purpose — the point of a plan is to fix the target before the build. `iterate` exists precisely
for the cases where that is impossible; treating every change that way would be an excuse for
unfalsifiable work.
