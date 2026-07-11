# Provenance: Pivot, Consolidate, Focus

## Session

- Session: Plan session — cloud agents port (July 11, 2026)
- Timestamp: 2026-07-11T17:25:46Z
- CWD: /home/user/workflow-plugin
- Tool: Claude Code (remote/cloud session)

## Initial Request (verbatim)

> This repo contains a workflow system that up until now I’ve used for human workflows. The main strength of the system so far is the use of artifacts to capture intent, design, decomposition and review of work. Intent especially is valuable later for matching what was done, to why. It’s intentionally less focused on structural enforcement to avoid misalignment - overloading agents with structural compliance requirements ends up having them lose focus.
>
> I think there’s still plenty of room for improvement.
>
> However, now we want to port this into cloud agents, for use in a slightly different manner. I’m leveraging cursor automations to set up a staged process, where Claude code, codex, human workflows build out changes, create a PR, then a cursor automatio carries out an orchestrated workflow to perform reviews, QA using computer use, babysit the pr to merge ready status.
>
> The plan/execute workflow will have a key role in this as the plan will be be used to determine intent, place review outcomes, determine QA plan (from intent and scope)
>
> Secondly the cloud agents doing the build do plan - execute in one workflow and this implies a somewhat different shape than the current skills describe.
>
> Finally we have other skills in the same plugin that are special - iterate, transcript parsing etc don’t need to be in cloud agents.
>
> Have a think about our intent here, suggest how you think we could reconcile what we have against our needs

## Planning Conversation

### Turn 1

**Agent proposed:** Initial reconciliation analysis: a modal split (headless vs interactive), a PR artifact seam contract, QA-drivable acceptance criteria, plugin partition (core vs local), review posture rebalancing, and a per-skill review.

**User responded:** Much of our structural noise is an artifact of the human process. The design is built around an unspoken meta-purpose — a work tracking system. Unimplemented plans sitting in a repo are just a backlog; peel that away and join plan-execute in the same workflow, and the backlog disappears along with ephemeral artifacts that existed only to tell execute how to decompose work — those can live in the active memory of the orchestrator. Rather than a modal process, align both the human and cloud processes to the new model. Ditch the backlog mental model. Consolidate and focus the skills around the new seams. The automation should output its review in the plan folder and adopt the brief approach of iterate — testing showed communication via artifacts is far more reliable: drastic improvements in subagent prompt quality (especially long-context jobs) via defined briefs, and far more accurate review remediation when the orchestrator wasn't acting as a lossy messenger. "The guide here would be not modal but pivot consolidate and focus."

**Agent decisions:**

- Dropped the modal design in favor of one aligned model for human and cloud.
- Raised three challenges: loss of the pre-execution decision gate, active memory not surviving dead containers, and loss of cold-reader pressure on plan quality.

### Turn 2

**Agent proposed:** Unified plan+execute skill with a holdable checkpoint; artifacts change owner and lifetime rather than disappearing (durable = intent/outcome, run-scoped = coordination briefs, nothing carries status); the briefs principle is "author writes once, orchestrator routes verbatim."

**User responded:** There are strong arguments around plan-execute having real distinction we lose in one joined workflow. There is a real risk of loss of focus — currently the plan agent has absolute focus on the quality of its plan document; joined, the plan becomes merely a short stop on the way to the build, with an accuracy cost. Joined workflows are also harder to stop, harder to leverage iterate's plan-and-optional-build, harder to validate plans before build. The strongest outcomes of iterate were that a plan not built has value — "I can plan, and then plan again adversarially to reward creativity." So: retain separate plan/execute and their contracts. Build in the briefs — an interesting approach to test. Strip out the backlog, retain more focused artifacts that rely less on orchestrator translation into subagent prompts, and peel back some reasoning fluff in the existing skills — though grounding in intent stays: "telling an agent what to do is fine, having it know why means it can fill the gaps you don't specify a little better."

**Agent decisions:**

- Plan and execute remain separate skills; the cloud one-shot becomes sequential composition within one run (the pattern iterate already uses), not fusion.
- Adopted the orienting-why vs persuading-why discriminator for trimming skill commentary: keep rationale that changes agent behavior in unspecified situations; relocate rationale that argues the design's correctness to per-skill reference docs.

### Turn 3

**User responded:** Ok do it now. We are relying on a few hypotheses — some relatively well tested but not in this context. Put our theory somewhere, maybe in the readme (concisely). A very next step is going to be to run evals that test these very hypotheses, so it's critical to identify the assumptions that form our approach.

**Agent decisions:**

- This session produces the plan artifacts plus the README hypotheses section; skill revisions are executed in later slices.
- Evals targeting the hypotheses are sequenced as the first execution phase, before skill revisions, per the user's "very next step" direction.

## Agent Decisions

- **Single plan folder, new convention**: This plan deliberately adopts the convention it defines — no `[NEW]-` prefix, no folder renumbering ceremony, status carried by the PR and branch rather than the folder name. Rationale: dogfooding the pivot; the folder exists on a branch that is being built, which is the new invariant.
- **DESIGN.md included**: The PR artifact seam, the artifact taxonomy, and the briefs invariant are cross-implementor contracts consumed by multiple later execution slices and by the external cursor automation. That is exactly the condition under which plan-scoped DESIGN.md is warranted.
- **Evals before revisions**: Phases ordered so hypothesis evals run before the skill rewrites where feasible, because the rewrites themselves are bets on the hypotheses. Where an eval needs a candidate skill variant to test (e.g. briefed dispatch), the variant is built inside the eval phase as a candidate, not merged first.
- **Hypotheses in README**: Chosen over a separate docs file because the README is the first thing both humans and agents read, and the user asked for concision — the hypotheses are the theory of the plugin, not an appendix.
