# Guidance — C / compiled default for perf-sensitive builds

**Status:** guidance (non-breaking). No installer, driver, hook, or skill behaviour changes — operators and orchestrators follow this pattern by convention. **Do not ship behaviour changes without Cody**; this file records standing intent only.

**Related:** open-pajero-maps Claude analysis — [`RESEARCH/2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md`](RESEARCH/2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md). Lab pack index — [`RESEARCH/2026-09-30-jev-cheap-judgement-signals/INDEX.md`](RESEARCH/2026-09-30-jev-cheap-judgement-signals/INDEX.md). Peer guidance (Flash sign-off gate) — [`GUIDANCE-flash-review-gate.md`](GUIDANCE-flash-review-gate.md).

**Scope:** **open-pajero-maps** and similar **build systems / perf-sensitive agentic builds** where language and runtime choice materially affect throughput, memory, or phase cost.

## Standing guidance (Cody, via Maps Builder, 2026-10-01)

1. **Not attached to Python.** Python was not the preferred approach for this kind of project; treat language choice as a design decision, not inherited baggage.
2. **Default up front: C / compiled.** For this class of work, **C or another compiled path should have been the default** from the start — not a late rescue after Python proved too slow.
3. **Python → C rewrites are allowed.** Agents may **rewrite Python to C freely**. There is **no design mandate to keep Python** for compatibility or continuity alone.
4. **Stop the recurring anti-pattern.** Each phase **implements hot paths in Python, blows performance**, then **rewrites to C** — that loop wastes orchestrator time and obscures the real architecture. Do not normalize it.
5. **Strategic fix: redesign and strip Python, not another triage round.** Prefer taking maps (and similar projects) **back to design** for a **3D rewrite** that **removes Python from the critical path** rather than patching forward. **Do not** treat **another Python round-trip triage** as the strategic fix when perf and systems shape are the problem.

## What agents should do

| Situation | Preferred move |
|-----------|----------------|
| New perf-sensitive or systems-style build (maps, drivers, batch pipelines) | **Start in C / compiled** (or the project’s agreed native stack); avoid prototyping hot paths in Python “for speed of iteration” when perf is a first-class requirement. |
| Existing Python on hot paths | **Rewrite to C** when warranted — no need to preserve Python for its own sake. |
| Repeated phase pattern: Python perf failure → C rewrite | **Escalate to design**: replan boundaries and runtime, don’t schedule another incremental Python phase. |
| Unclear whether this guidance applies | Ask Cody; **this document does not authorize plugin, skill, or hook changes.** |

## What does not change

- **Skill names, install paths, and execute/design/refine contracts** are unchanged. This guidance does not alter `execute`, `design`, or lab skill text.
- **`assert_phase --deterministic`** and existing **Jev / driver hooks** stay as wired; no new enforcement from this note.
- **Landing policy** for the workflow plugin: **additive, non-breaking docs** may merge; **behaviour changes** still require Cody and the normal proposal path.

## Rationale (one paragraph)

Agentic builds default toward Python because it is easy to draft in, but **maps-class systems work** pays for that choice in **every phase** when hot paths land in an interpreted runtime first. Cody’s standing preference is to **choose compiled up front**, **allow free Python→C migration**, and **break the Python-then-rewrite cycle** by returning to **design for a clean strip of Python** instead of endless triage — so capacity goes to architecture and outcomes, not repeated perf fire drills.
