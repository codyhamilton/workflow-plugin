# Lineage — prior work and scope boundary

## Landed: phase-boundary Jev assert spike

**Doc:** [`../../PROPOSALS/2026-09-30-jev-hook-assertion-spike.md`](../../PROPOSALS/2026-09-30-jev-hook-assertion-spike.md) (`status: landed`)

**Code:** `tools/driver/assert_phase.py`, `tools/driver/phase_assert.py`, fixtures/tests, eval `trailer-completeness` verifier.

**Scope:** One Score question (`outcome-evidence`) on **compact phase state** at phase close; deterministic kill line; Jev logged on `--live`.

**This white paper is NOT:** redoing spike C, changing assert thresholds, or expanding classify calibration.

## Strategy pass: Grok Bot driver reorient

**Doc:** [`../../ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../../ANALYSIS/2026-09-30-grokbot-driver-reorient.md)

**Relevant lines:**

- Grok Bot supervises; workers stay inside `execute`.
- Jev for **assert hooks** at boundaries; classify = chart only.
- Evaluator–optimizer pattern → phase verify + Jev assert + comprehensive-review.

**This white paper IS:** the **next layer** — **in-session** and **refine / unit / phase** *soft* judgements (use cases 1–4), still behind deterministic pre-gates where they exist.

## Backlog context

- P1 assert + first outcome row: **done** (`../../BACKLOG.md`).
- P3 parked: “LangGraph-style evaluator–optimizer for **brief quality**, offline, using an assert rather than session kind” — use case **2** connects here but stays hook/signal oriented, not offline-only.

## Proposal

- File: [`../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) (`status: draft`).
- Linked from [`../INDEX.md`](../INDEX.md). Backlog: spike the hooks when Cody accepts; the white-paper item is done.
