---
name: plan
description: Create or revise implementation plans for this repo. Use when a user asks for a plan, to restructure plan docs, or to define a self-contained work package with clear contracts and acceptance criteria.
---

# Planning

Use this skill to produce plan docs under `docs/plans/` and to tighten the stable docs plan depends on.

This skill exists to prevent common plan failures:

- A local "next step" problem quietly turns into an architectural pivot without widening scope.
- New plans drift from stable architecture or design-intent docs without surfacing and reconciling the disagreement.
- The user's expressed intent is lost through translation and paraphrasing.
- The agent avoids the few questions that would actually improve scope shape, boundaries, sequencing, or non-goals — or, in a headless run, records assumptions that are decorative rather than honest.
- Parallel implementation starts from prose explanations instead of reified contracts when shared contracts are actually needed.
- Plans capture tasks but lose the rationale future agents need to understand why the work exists.
- Agents over-fit to document structure and create documentation cascades that mostly restate the code.
- Acceptance criteria are too vague for a downstream QA agent to act on without a human to ask.

The job of this skill is to capture the user's real intent, validate the scope-shaping decisions that matter, detect when a narrow request implies a broader architectural shift, and leave behind the smallest durable set of plan artifacts that execution, review, and QA can act on without hidden assumptions.

The user, or the dispatching process, has already chosen to enter a plan workflow — don't spend time deciding whether planning is warranted. Treat that choice as evidence the work deserves a deliberate plan, execution, and review.

## Postures

Every plan run happens in one of two postures. Posture is **declared by the invoker, never inferred** — no TTY sniffing, no environment heuristics. Absent a declaration, assume a human is reachable and run interactive.

- **Interactive** (default): scope-shaping questions are asked as they arise and recorded as Q&A in `PROVENANCE.md`. The session ends at a held checkpoint — the plan and (if any) assumption ledger are presented to the user before any execution starts.
- **Headless** (declared explicitly by the invoker — a skill argument, or an explicit statement in the dispatching prompt): every question the skill would otherwise have asked becomes an entry in the plan's **assumption ledger** instead — the question, the answer chosen, the rationale, and what would change if the assumption is wrong. The ledger is a section of `PLAN.md`. The checkpoint is waved through, not held. Downstream review explicitly challenges the ledger, so entries must be honest, not decorative.

Both postures follow the same workflow phases below; only Resolve and Checkpoint behave differently.

## Workflow

Six named phases. Move forward when a phase's output exists — this is not a numbered checklist to satisfy mechanically.

1. **Capture.** Capture the user's real request verbatim, before reading anything else. Create the plan folder (see "The plan folder" below) and write `PLAN.md`'s Intent section verbatim, from `templates/PLAN.md`. This is the first write to disk, in every posture. In interactive posture, also initialize `PROVENANCE.md` from `templates/PROVENANCE.md` (Session + Initial Request) to hold the Q&A record as it accrues; skip it in headless posture, where the assumption ledger inside `PLAN.md` is the whole record.
2. **Ground.** Read the stable docs: `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, and relevant files in `docs/design/`. If they're absent, stale, or stub-only, say so and proceed on what's available — a human may want to run `/workflow:setup` first, but plan never hard-depends on it. Check whether the requested change implies architectural drift, a pivot, or contract changes the stable docs don't yet reflect.
3. **Resolve.** If Ground surfaced a pivot, surface it explicitly to the user (or in the assumption ledger, headless), explain what broader context now applies, identify which stable docs are affected, and widen the plan's scope before continuing — do not keep treating it as a narrow local change. Then resolve the remaining open scope-shaping decisions:
   - Interactive: ask the user the few questions that would materially change scope shape, sequencing, boundaries, compatibility, non-goals, or acceptance criteria. As soon as the user answers, append the turn to `PROVENANCE.md`'s Planning Conversation immediately — do not batch.
   - Headless: for each such question, decide it yourself and record it as an entry in `PLAN.md`'s Assumption Ledger, appended immediately, not batched.
4. **Write.** Write the rest of `PLAN.md` from `templates/PLAN.md` — scope, architectural implications, execution phases, and QA-drivable acceptance criteria (see below). Add a plan-scoped `DESIGN.md` only when the target shape or cross-implementor contracts need explicit reification. Before finalizing, append the Agent Decisions section to `PROVENANCE.md` (interactive) or fold any cross-cutting rationale into the Provenance Notes section of `PLAN.md` (headless).
5. **Challenge.** Run one adversarial review pass, using a clean subagent when possible. It should challenge value, alignment with intent, whether scope was widened enough, missing contracts, internal inconsistency, ordering mistakes, unnecessary documentation, and weak acceptance criteria. In headless posture, the pass explicitly challenges the assumption ledger — is each entry a real decision with a real rationale, or a placeholder? Apply findings that improve the plan and align with intent; report all findings to the user regardless of whether they were applied.
6. **Checkpoint.** Interactive: hold here. Present the plan, and the assumption ledger if one exists, to the user before any execution starts. Headless: wave through — do not hold. The plan folder as it stands is the handoff artifact; downstream review is the backstop that keeps a waved-through ledger honest.

## The plan folder

- One plan folder per change/PR, at `docs/plans/<NN>-<slug>/`. The slug is the unique key; `NN` is best-effort ordering only — nothing may locate a folder by number. Two build agents branching from the same base may land on the same `NN`; that's fine and needs no resolution.
- A plan folder existing on a branch means the work is being built or was built — nothing else. Never create one for deferred or speculative work; that becomes a design-intent doc in `docs/design/` or a tracker issue, not a plan folder.
- Multi-PR programs are not a parent-program folder hierarchy. They are a stable design-intent doc in `docs/design/` that each PR's `PLAN.md` references, plus a sequence of self-contained plan-execute runs.
- The eventual PR carries a body marker line, `Workflow-Plan: docs/plans/<NN>-<slug>/` — the only mechanical way downstream review and QA automation locate the plan folder. Plan does not create the PR, but the folder must exist at the path the marker will point to.

## QA-drivable acceptance criteria

- Acceptance criteria must be observable — state how success is known, not just what should feel true.
- User-facing criteria state **entry point → action → observable result**: where the behavior is reached, what's done, and what's observed — enough for a downstream computer-use QA agent to derive its QA plan mechanically, without asking.
- Non-user-facing criteria (internal contracts, data shape, performance) stay as plain observable statements; the entry-point shape doesn't apply to them.

## Rules

- Explain the why of the plan, not just the work to be done.
- `PLAN.md` always carries the user's own words in its Intent section, verbatim. This is untouchable regardless of posture.
- Ask, or ledger, only the questions that genuinely improve scope shape, sequencing, boundaries, compatibility, non-goals, or acceptance criteria. Do not ask, or ledger, implementation-curiosity questions whose answers can be discovered later during execution.
- Posture is declared by the invoker, never inferred. Absent a declaration, run interactive.
- Prefer one self-contained plan folder per meaningful work package, at the path in "The plan folder" above.
- Use `DESIGN.md` only when it defines target shape, ownership, contracts, boundaries, or measurable acceptance criteria not already cheap to infer from stable docs and code.
- Design should describe the intended outcome and contracts, not implementation detail, unless the contract itself requires it.
- Keep genuinely unresolved open questions visible in `PLAN.md`'s Open Questions section. In headless posture this should rarely hold anything, since the ledger absorbs what would otherwise be a question — but if something truly can't be assumed, say so plainly rather than forcing a ledger entry.
- Stable architecture docs and stable design-intent docs are part of plan. If the plan needs them and they're missing or stale, fix that deliberately as part of the plan output — but never block on it (see Ground).
- Do not let structural compliance replace architectural clarity. If the problem demands a slightly different shape, preserve the purpose of the artifacts rather than forcing a template mechanically.
- `PROVENANCE.md` is optional: write it for interactive sessions with real Q&A history; skip it for headless one-shot runs, where intent, assumption ledger, and decisions live in `PLAN.md` alone.
- When `PROVENANCE.md` is used, write it progressively: create it at Capture, append each Q&A turn as it happens, append agent decisions before finalizing. Do not batch or defer.
- Provenance records intent, not a transcript. Extract the substance — the decision, preference, or direction — in the user's words. Strip tone and filler. Omit conversational asides and anything not intended for persistence. Preserve exact phrasing only when it carries meaning a paraphrase would lose. If in doubt, omit.
- Do not copy credentials, API keys, tokens, or large file dumps into `PROVENANCE.md` or `PLAN.md`.

## Reference

`reference.md`, beside this file, holds the design rationale behind these rules — why the model is shaped this way — for whoever revises this skill later. It is not loaded during normal execution.
