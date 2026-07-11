# Plan skill — design reference

Not loaded during normal skill execution. Consumers: workflow-tuning, and anyone revising this skill later.

This file holds the prose that argues the plan skill's design is *correct*, as distinct from `SKILL.md`, which holds only what changes an executing agent's behavior in an unspecified situation. The test applied throughout: if the agent already trusted the rule, would this sentence change what it does? If no, it belongs here, not in the skill body.

## Why plan and execute stay separate skills

A dedicated planning context has absolute focus on plan quality. A joined plan-then-build workflow makes the plan a stop on the way to the build, with an accuracy cost — the agent's attention is already leaning toward implementation while it should still be interrogating scope. Separation preserves gating, plan validation, adversarial planning, and the option to plan without building. When a single cloud run does both, they run as two separately dispatched contexts (plan, then execute), handed off through the plan folder's artifacts, never fused into one continuous context — fusing them would silently destroy the cold-read pressure the Challenge phase, and downstream review, depend on.

## Why posture is declared, not modal

This is not a human/cloud split expressed as two different skills or two different plugins. Both processes align to one workflow model; the only irreducible difference is whether someone is standing at the plan→execute seam able to hold the checkpoint. Encoding that as a runtime-declared posture, rather than sniffed from environment or TTY, keeps the logic auditable and prevents a misdetected environment from silently skipping a checkpoint a human actually needed, or stalling a headless run waiting on a human who was never there.

## Why the assumption ledger has to have teeth

Headless posture removes the ability to ask, but not the discipline of only raising what actually matters. An assumption ledger padded with decorative or hedged entries defeats its own purpose — it exists so a downstream reviewer, human or automated, can challenge exactly the decisions that would otherwise have been questions. A dishonest or vague ledger entry is worse than an honest gap, because it looks resolved when it isn't.

## Why the backlog taxonomy was removed

The old open-program folder prefix, its numeric renumbering ceremony, the parent-program structure, and a canonical-schedule ROADMAP file were a shadow work-tracking system, built for a repo-as-backlog mental model. In the staged pipeline this plugin now targets, the PR and the issue tracker already carry status; a folder-name taxonomy encoding lifecycle stage duplicates that and inevitably drifts from it. The plan folder now means exactly one thing: this change is being built or was built. Deferred and speculative work moved to design-intent docs and tracker issues, which already have owners built for exactly that job — a plan folder was never the right place for work that isn't happening yet.

## Why `NN` is not a locator

Concurrent build agents branching from the same base can independently pick the same `NN` with no way to coordinate with each other before a PR exists. Making the slug the real key — and stating explicitly that nothing may locate a folder by number — removes a race condition that numeric prefixes would otherwise require a lock, a central registry, or a human to resolve. `NN` still exists because a rough chronological ordering is genuinely useful to a human skimming `docs/plans/`; it just carries no contract.

## Why acceptance criteria must be QA-drivable

This plugin feeds a staged cloud pipeline: the build stage produces a PR, then an automated stage runs computer-use QA against `PLAN.md`'s acceptance criteria with no human present to interpret them. "Entry point → action → observable result" is exactly the shape a QA agent needs to construct its own test steps mechanically; anything vaguer forces it to either guess at what the plan meant or stall waiting for clarification that a headless pipeline can't provide.

## Why `PROVENANCE.md` became optional

A rich interactive session carries a real back-and-forth worth preserving as a debugging and provenance record — what was asked, what was answered, and why it changed the plan. A headless one-shot run has no such back-and-forth; inventing a Q&A transcript that never happened would be ceremony, not provenance. The assumption ledger inside `PLAN.md` already carries the equivalent information for that case: not what was asked and answered, but what was decided and why, and what would change if the decision was wrong.

## Why cold-reader pressure was always the point

The plan session's checkpoint, and now the Challenge phase's adversarial pass, exist to compensate for the same failure mode from two directions: an agent (or a person) that has been reasoning about a change for a while stops seeing its own gaps. A clean reader — a fresh subagent, a held-checkpoint human, or downstream review reading only the artifact — catches what the authoring context can't. Composition at the run level (plan and execute as separate dispatches) and the shift of cold-reader pressure onto downstream review in headless posture are both applications of this same idea, not separate design choices.
