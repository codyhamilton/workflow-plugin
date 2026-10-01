# Evidence log — interception / steer-to-stop trials

**Soft Standard HOLD.** Assessment/decision layer only; steer adherence unmeasured.  
LLM agreement is not gold. Flash may be **policy-under-test** or **variant driver** — never silent reference gold.

| Batch | Wave | Status | n_sessions | n_variants | Notes |
|-------|------|--------|------------|------------|-------|
| batch-001 | Wave-0 attempt | **plumbing-only; contaminated (T leak)** | see batch dir | see batch dir | Opus R1–R3 BLOCK. Not score-ready. See `batch-001/LEAKAGE-NOTE.md`. |
| batch-002-multidriver | Wave-0-multi | TypeSafe+Flash+Luna lever diagnostics (FP/miss board deferred) | ~20 | 2500+ TypeSafe-k1 / ~5k+ cum live | Soft HOLD. R1–R3. No invented outcome labels. |
| batch-002 | Wave-0 | score-ready-path diagnostics (FP/miss board deferred; windows unidentified) | 22 | 240 | R1–R3 decontaminated. leak_hits=0. |

## Deferred (post batch-002)

**Outcome sheet protocol — landed.** [`OUTCOME-SHEET.md`](OUTCOME-SHEET.md) defines framing-agnostic **near-done** vs **runaway-like** observables, ideal steer windows (`none` / turn range / `ambiguous`), sidecar label schema, and join rules without leaking labels into judge inputs. Opus **R2** documentation gate for Wave-0 is satisfied at the **protocol** layer; **R3** schedule + R1 audit were already fixed in `batch-002/`.

**Session labels — landed (sidecar).** `batch-002/outcome-labels.jsonl` has **20/20** rows (`label_status=labeled`, `labeler=chm-sol-adjudication`, `protocol_rev=outcome-sheet-v1`, independence attestation all false). Blind Sol adjudication from transcript digests only (no Flash rating/fire). Soft HOLD remains: `results.jsonl` cells stay `window_status=unidentified` / `outcome_tag=null`; FP/miss scoreboard **not** claimed.

**Corpus analysis — landed (docs).** [`../2026-10-02-interception-steer-to-stop/ANALYSIS.md`](../2026-10-02-interception-steer-to-stop/ANALYSIS.md) inventories batch-002 streams (incl. **200×41** TypeSafe scenario sweep #104), exploratory fire/rating tables, and **PROVISIONAL** outcome join ([`analysis/PROVISIONAL-join-wave0-flash.jsonl`](../2026-10-02-interception-steer-to-stop/analysis/PROVISIONAL-join-wave0-flash.jsonl)). Re-run: `batch-002/analyze_corpus.py`.

**TypeSafe lever join — landed (derived evidence).**
[`batch-002/typesafe-outcome-join/COVERAGE.md`](batch-002/typesafe-outcome-join/COVERAGE.md)
joins 5420/5420 committed lever rows (20/20 sessions; 67/67 unique
session-checkpoint keys) to the existing sidecar. No committed lever row is
unlabeled. `typesafe-k4` is meter-only (1500 reported cells, no committed
`results.jsonl`) and remains unmeasurable at row level. Soft HOLD; no FP/miss
board or product claim.

## Rules

1. No row is score-ready while any post-checkpoint field appears in state or prompt (leakage audit required).
2. Length-derived ideal windows are **not** reference evidence.
3. Report `n_sessions_independent` and `n_variants` separately.
4. Score checkpoint t only on sessions that **survived to t** (hazard / at-risk framing).

## Batch notes
- `batch-002/archive-t45-only/`: discarded first decontam run that only sampled checkpoint 45 (allocation bug); not evidence.
- Current `batch-002/` results = schedule-breadth re-run (v2).

## Flash/Luna streaming expand (2026-10-02 01:45 AEST)

Soft HOLD. Complementary to sibling TypeSafe bulk. Captures: `luna-b/` (180 done), `flash-hframings-b/` (in flight), `flash-scale/`+`luna-scale/` (2400+960 dense/trim axes), `flash-mid/`+`luna-mid/` (T≥30 expand). See `batch-002/CUMULATIVE-STREAM.md`. No hooks unlock.
