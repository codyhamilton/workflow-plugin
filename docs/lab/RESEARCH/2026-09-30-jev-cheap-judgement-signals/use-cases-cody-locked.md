# Four use cases (Cody-locked)

These are the **proposal core** — each should become a subsection in the Grok white paper with deterministic pre-gate + optional Jev + default soft signal.

## 1. PostToolBatch — in-session size / progress

**Trigger:** `PostToolBatch` after tool batch completes.

**Deterministic pre-gate (examples):**

- API turn count or tool turns ≥ band (workflow-tuning ideal **50–75** turns per worker).
- Estimated context or JSONL size ≥ threshold (e.g. final/peak context **> 125k** neighborhood).
- Parallel fat workers overlap (optional: read from session metadata).

**Optional Jev (advisory):**

- Score or Choice on compact state: progress vs remaining scope, whether session is “still on brief” vs “wandering.”
- Output: **signal** — log + surface to parent/orchestrator (“consider handoff”), not auto-kill.

**Success signal:** Fewer workers crossing 100+ turns without a human noticing; no increase in false hard-stops.

## 2. After refine — brief complexity ratings

**Trigger:** `refine` skill completes; N briefs exist for the phase.

**Deterministic pre-gate:**

- Always emit brief list (ids, titles, line counts) — no Jev required for enumeration.

**Optional Jev:**

- Per-brief **complexity** Score (or rank) on bounded brief text + DESIGN phase outcome.
- Surface **top-k largest** for human or bot review before `execute` dispatch — not block dispatch by default.

**Success signal:** Large briefs get review before spawn; token burn from under-scoped mega-briefs drops.

## 3. Unit complete — “needs review?” confidence

**Trigger:** Unit closing record + trailer observed (subagent stop or phase worker done).

**Deterministic pre-gate:**

- Trailer present; required headings; tests/verifier command exit code if already mechanical.

**Optional Jev:**

- Conditional **“needs review?”** confidence (Score/Choice) on compact closing record — similar shape to phase assert state but **unit-scoped**.
- If confidence high → **maybe** spawn `comprehensive-review` or a small review agent; else log only.

**Success signal:** Review agents run on high-uncertainty units, not every unit.

## 4. Phase complete — alignment sanity

**Trigger:** Phase `workflow-report` closed + git trailer (same window as `assert_phase`).

**Deterministic pre-gate:**

- **`assert_phase.py --deterministic`** (already landed) — authoritative pass/fail.

**Optional Jev:**

- **Alignment sanity** Score: “does closing narrative match design outcome intent?” — logged; may recommend **dig deeper** before bot triggers next phase.
- On disagreement with deterministic, **ignore Jev for gating** (kill line).

**Success signal:** Bot escalates on deterministic fail; Jev adds triage priority on passes that “smell thin.”

## Cross-cutting rules

- Default: **signal**, not gate.
- Jev model pin: **`jev-1.13.0`** (consistent with driver).
- Do not route these through **`classify.py`**.
