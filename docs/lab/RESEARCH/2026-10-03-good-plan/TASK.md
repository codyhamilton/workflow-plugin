# Task: what makes a good design or brief (candidate criteria)

Context. An AI-agent workflow produces two planning artifacts. A **design** (DESIGN.md) states the user's intent verbatim, the solution shape (domain boundaries, contracts, ownership), and phases each closed by a provable outcome. A **brief** is a self-contained work order for one worker agent with a clean context: consumer, owned paths, required reading, changes, done evidence, a budget. Designs are consumed by a refinement step that cuts briefs; briefs are executed by agents that have only the brief and the repo.

We want the best-we-can-think-of criteria that distinguish good designs and briefs from bad ones, to be measured on every artifact for cheap comparative analysis. A criterion must be (a) a claim about the artifact text, (b) checkable from text alone, deterministically or by a small LLM given a rubric of concrete levels, (c) linked to a failure that happens downstream (rework, missing scope, defects, worker guessing, wasted cost, unverifiable "done"). Holistic "is this good?" judgements are not usable; concrete, text-checkable criteria are.

Deliver one markdown file in `docs/lab/RESEARCH/2026-10-03-good-plan/candidates/` (your name below). At most 15 candidates, best first. Use exactly this block per candidate:

```
### C<n>: <short name>
- subject: brief | design | both
- claim: <one sentence, concrete, true of the artifact text when satisfied>
- failure_prevented: <the downstream failure>
- evidence: <URL/citation with what it says, or data reference with numbers>; mark `speculative` if none
- checkable_by: deterministic | jev | human-only
- check_recipe: <how to test it from the text; for jev, the 4 levels in one line each>
- counterexample: <a good artifact that violates it, or a bad one that satisfies it>
- confidence: low | medium | high
```

Then a short section `## Does not work` (criteria that sound right but are gameable, unfalsifiable, size proxies, or contradicted by evidence), and `## Gaps` (what you could not determine). Cite real sources only; never invent a reference. Do not pad. Keep tone plain.
