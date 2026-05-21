---
name: planning
description: Create or revise implementation plans for this repo. Use when a user asks for a plan, to restructure planning docs, or to define a self-contained work package with clear contracts and acceptance criteria.
---

# Planning

Use this skill to produce plan docs under `docs/plans/` and to tighten the stable docs that planning depends on.

This skill exists to prevent common planning failures:

- A local "next step" problem quietly turns into an architectural pivot without widening scope.
- New plans drift from stable architecture docs, design-intent docs, or roadmap intent without surfacing and reconciling the disagreement.
- The user expressed intent is lost through translation and paraphrasing and recorded only second-hand in provenance docs.
- The agent avoids the few questions that would actually improve scope shape, boundaries, sequencing, or non-goals.
- Parallel implementation starts from prose explanations instead of reified contracts when shared contracts are actually needed.
- Plans capture tasks but lose the rationale future agents need to understand why the work exists.
- Agents over-fit to document structure and create documentation cascades that mostly restate the code.

The job of this skill is to capture the user's real intent, validate the scope-shaping decisions that matter, detect when a narrow request implies a broader architectural shift, and leave behind the smallest durable set of plan artifacts that future agents can execute against.

The documents are important, but they are not the goal. The goal is to make architectural intent, boundaries, target shape, and measures of success explicit enough that execution can proceed without hidden assumptions.

## Working Model

The user has already chosen to enter a plan workflow. Do not waste time deciding whether planning is necessary. Instead, use that choice as evidence that the work is substantial enough to deserve thoughtful planning, execution, and review.

Start from the real user request, then test whether it implies any of the following:

- a change to architectural direction
- drift from stable docs such as `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, or `docs/design/*`
- roadmap consequences for later plans or sequencing
- new or changed contracts that downstream implementation must obey

If the answer is yes, widen the scope of the planning work. Do not keep treating the task as a narrow local change.

When a request appears to imply an architectural pivot:

- surface the pivot explicitly to the user
- explain what broader context must now be considered
- identify what stable docs and roadmap entries are affected
- turn the task into an architectural planning conversation, not just a local implementation breakdown

If intent or direction is still unclear after reading the relevant docs, ask the user the missing question rather than silently inventing alignment.

Ask questions only when the answer materially changes:

- scope shape
- sequencing or phasing
- architecture boundaries
- compatibility or migration behavior
- non-goals
- acceptance criteria

Do not ask implementation-curiosity questions whose answers can be discovered later during execution.

Planning works with four document roles:

- Stable architecture docs: concept map, ownership map, invariants, and cross-system relationships.
- Stable design-intent docs: why the system or surface exists and what matters about the target outcome.
- `PLAN.md`: the scoped change, its implications, sequence, and observable success conditions.
- Plan-scoped `DESIGN.md`: optional. Use only when the target shape or shared contracts need reification inside the scope of the change.

Plan structure should help later execution:

- If several plans are really one linked architectural sequence, group them under one parent program in `docs/plans/`.
- Use child plans for separately executable slices inside that program.
- Keep ordering and dependency truth in the nearest relevant `ROADMAP.md`.
- Prefer completion artifacts inside a child plan folder over moving completed plans into a separate archive tree.
- Use `[NEW]-<program>/` for open parent programs that are still planned and negotiable.
- Reserve numeric parent prefixes such as `01-` for implemented parent programs kept as provenance.

## Workflow

1. Capture the user's request verbatim in context. Prefer the full prompt, not a softened paraphrase. Do not write PLAN.md yet — that happens in step 11, after questions are resolved.
1a. Immediately after capturing the verbatim request — before reading stable docs or asking any questions — create the plan directory and write PROVENANCE.md using `templates/PROVENANCE.md`. Fill in Session (label + timestamp + CWD) and the Initial Request section verbatim. This is the first write to disk. PLAN.md is not written until step 11.
2. Read the stable docs first: `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, and relevant files in `docs/design/`. If these docs are absent or contain only stubs, suggest that the user run `/workflow:setup` before continuing — setup creates the stable docs that planning reads, and planning on a repo with no stable docs produces degraded plans.
3. Check whether the requested change implies architectural drift, a roadmap shift, or broader contract changes.
4. If it does, widen scope and surface that implication in the conversation before finalizing the plan.
5. Identify the few decisions that would materially sharpen intent or refine scope shape. Ask those questions before finalizing the plan.
5a. After each Q&A turn: as soon as the user responds, append the turn to the Planning Conversation section of PROVENANCE.md immediately — before continuing. Record the substance of what the user said in their words. Strip tone, filler, and conversational asides. Preserve exact phrasing only when it carries intent that a paraphrase would lose.
6. If stable architecture or design-intent docs appear stale, missing, or misaligned, do not silently assume them updated. Make the shift explicit, then create or update those stable docs as part of the planning output when appropriate.
7. Decide whether the work belongs in an existing `[NEW]-*` parent program, needs a new `[NEW]-*` parent program, or is truly standalone.
8. Before creating a new parent program, check whether the work should instead become a child plan under an existing open parent program.
9. Treat numbered parent programs as implemented provenance. If new work conflicts with or supersedes them, surface that explicitly in the conversation and update docs deliberately rather than silently reshaping history.
10. Update the nearest relevant `ROADMAP.md` when adding or reordering linked plans.
11. Write `PLAN.md` using `templates/PLAN.md`.
11a. Before finalizing the plan: append the Agent Decisions section to PROVENANCE.md. Record each significant decision and the rationale behind it. Focus on decisions that are not obvious from the plan text itself.
12. Add a plan-scoped `DESIGN.md` only when the target shape or cross-implementor contracts need to be made explicit.
13. Run one adversarial planning review pass using a clean subagent when possible. The review should challenge value, alignment, widened scope, missing contracts, internal inconsistency, ordering mistakes, unnecessary documentation, and weak acceptance criteria.
14. Apply review findings where they improve the plan and align with user intent, but always report the review findings to the user.

## Rules

- Explain the why of the plan, not just the work to be done.
- Record the user's own words in the intent section. Prefer verbatim prompt text.
- Ask only the questions that genuinely improve scope shape or target clarity.
- Prefer one self-contained plan folder per meaningful work package.
- Keep parent `PLAN.md` short and decision-oriented. Child `PLAN.md` may be more detailed when it is the executable slice, but it still should not freeze speculative code.
- Use `DESIGN.md` only when it defines target shape, ownership, contracts, boundaries, or measurable acceptance criteria that are not already cheap to infer from stable docs and code.
- Design should describe the intended outcome and contracts, not implementation detail unless the contract itself requires it.
- Acceptance criteria must be observable. State how success is known, not just what should feel true.
- Keep open questions visible. If the plan depends on unresolved choices, say so plainly.
- Stable architecture docs and stable design-intent docs are part of planning. If the plan needs them and they are missing or stale, fix that deliberately.
- If the work is one multi-session program, prefer a parent program folder with ordered child plans over many flat sibling plans.
- Parent programs should own program-level `PLAN.md`, `ROADMAP.md`, and `DESIGN.md` when a program-level design contract is actually needed.
- Open parent programs should use a `[NEW]-` prefix.
- Number a parent program only after implementation when it becomes completed provenance.
- Child plan folders should use numeric prefixes that match roadmap order.
- Ordering should be visible from both the folder tree and the nearest roadmap, not hidden in one place only.
- Existing `[NEW]-` parent programs are the first place to look when deciding whether new work should be folded into an open schedule.
- Treat numbered parent programs as historical implementation provenance. Do not silently mutate them to absorb new planning work.
- Do not use folder moves as the primary completion signal. Future execution should leave completion evidence in the child plan folder.
- `ROADMAP.md` is the canonical schedule and status view for linked work.
- When a `[NEW]-` parent is later renumbered, update titles and headings as well as the folder name. Do not leave stale `[NEW]` labels in the body text.
- Phase schedule exists to support execution and delegation. Contracts come first; schedule comes after.
- When phase schedule is used, make dependencies and parallelizable work clear enough for later execution.
- Do not let structural compliance replace architectural clarity. If the problem demands a slightly different shape, preserve the purpose of the artifacts rather than forcing a template mechanically.
- Write PROVENANCE.md progressively: create it immediately on receipt of the initial request (before reading stable docs), append each Q&A turn as soon as the user responds, append agent decisions before finalizing. Do not batch or defer.
- Provenance records intent, not a transcript. Extract the substance — the decision, preference, or direction — in the user's words. Strip tone and filler. Omit conversational asides and anything not intended for persistence. Preserve exact phrasing only when it carries meaning a paraphrase would lose. If in doubt, omit.
- Do not copy credentials, API keys, tokens, or large file dumps into PROVENANCE.md.
