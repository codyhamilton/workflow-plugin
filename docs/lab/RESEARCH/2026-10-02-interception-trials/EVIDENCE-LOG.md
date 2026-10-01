# Evidence log — interception / steer-to-stop trials

**Soft Standard HOLD.** Assessment/decision layer only; steer adherence unmeasured.  
LLM agreement is not gold. Flash may be **policy-under-test** or **variant driver** — never silent reference gold.

| Batch | Wave | Status | n_sessions | n_variants | Notes |
|-------|------|--------|------------|------------|-------|
| batch-001 | Wave-0 attempt | **plumbing-only; contaminated (T leak)** | see batch dir | see batch dir | Opus R1–R3 BLOCK. Not score-ready. See `batch-001/LEAKAGE-NOTE.md`. |
| batch-002 | Wave-0 | score-ready-path diagnostics (FP/miss board deferred; windows unidentified) | 22 | 240 | R1–R3 decontaminated. leak_hits=0. |

## Deferred (post batch-002)

**Outcome sheet protocol — landed.** [`OUTCOME-SHEET.md`](OUTCOME-SHEET.md) defines framing-agnostic **near-done** vs **runaway-like** observables, ideal steer windows (`none` / turn range / `ambiguous`), sidecar label schema, and join rules without leaking labels into judge inputs. Opus **R2** documentation gate for Wave-0 is satisfied at the **protocol** layer; **R3** schedule + R1 audit were already fixed in `batch-002/`.

**Session labels — still pending.** No `batch-002/outcome-labels.jsonl`; all `results.jsonl` cells remain `window_status=unidentified`, `outcome_tag=null`. Until human labels exist, `batch-002/` meters stay score-ready-path **diagnostics** only — **not** a formal near-done FP / runaway-await FP/miss leaderboard.

## Rules

1. No row is score-ready while any post-checkpoint field appears in state or prompt (leakage audit required).
2. Length-derived ideal windows are **not** reference evidence.
3. Report `n_sessions_independent` and `n_variants` separately.
4. Score checkpoint t only on sessions that **survived to t** (hazard / at-risk framing).

## Batch notes
- `batch-002/archive-t45-only/`: discarded first decontam run that only sampled checkpoint 45 (allocation bug); not evidence.
- Current `batch-002/` results = schedule-breadth re-run (v2).
