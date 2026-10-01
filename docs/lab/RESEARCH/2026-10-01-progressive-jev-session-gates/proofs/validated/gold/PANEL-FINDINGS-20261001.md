# P0 gold panel — agreement findings (2026-10-01)

**Panel:** signed Sonnet 5.5 (`reviewer_final` only), Composer 2.5, Grok 4.7 high — **Flash drafts excluded.**  
**Schedule:** P0 `75:15` on smoking guns `92a48e004519` (15 cps) and `bb6165018de0` (6 cps) → **21 labeled prefixes.**  
**Machine-readable:** [`p0-panel-agreement-20261001.json`](p0-panel-agreement-20261001.json).

## Hard result — gold rule `A0` is null on both workers

Under pre-registered rule **A0** (earliest checkpoint where **all three** seats have `checkout_recommended=true` at that prefix):

| Worker | A0 | Verified earliest checkout by seat |
|--------|-----|-------------------------------------|
| `92a48e004519` | **null** | Sonnet **null**; Grok **105**; Composer **180** |
| `bb6165018de0` | **null** | Sonnet **null**; Grok **null**; Composer **null** |

There is **no** P0 checkpoint where Sonnet signs checkout on either worker (every signed Sonnet row is `not_yet`). Grok and Composer both recommend checkout on `92a48e004519` from cp **105** through **210**, but Sonnet never joins, so unanimous exit never exists. On `bb6165018de0`, all three seats stay `not_yet` at every cp — consistent with a long legitimate census wait, not a forced exit.

This matches the JSONL sources; these numbers are **not** inferred from Flash drafts.

## Reliability (H5 floor)

| Metric | Value | H5 floor (≥ 0.40) |
|--------|-------|-------------------|
| Krippendorff α (nominal, binary checkout, 3×21) | **0.1189** | **Fail** |
| Cohen κ sonnet ↔ composer | −0.0000 | — |
| Cohen κ sonnet ↔ grok-4.7 | 0.0000 | — |
| Cohen κ composer ↔ grok-4.7 | **0.4262** | moderate pairwise only |

**Pairwise % agreement** (same/different checkout bit at each cp):

| Pair | Overall (21 cps) | `92a48e` only (15) | `bb6165018de0` (6) |
|------|------------------|--------------------|--------------------|
| sonnet ↔ composer | 85.7% | 80.0% | 100% |
| sonnet ↔ grok-4.7 | 61.9% | 46.7% | 100% |
| composer ↔ grok-4.7 | 76.2% | 66.7% | 100% |

High raw agreement on `bb6165018de0` is trivial (all `not_yet`). The smoking gun drives disagreement: Grok checks out from **105** while Sonnet stays `not_yet`; Composer joins checkout only from **180**, so **105–165** are Grok-only checkout on `92a48e004519`.

**Checkout-positive counts (21 cps):** Sonnet **0**, Composer **3** (180, 195, 210 on `92a48e`), Grok **8** (105–210 on `92a48e`).

## Implications for P0 cell tuning

1. **Cannot fit Jev to unanimous gold exit (`A0`) yet** — there is no gold exit turn to target on either smoking gun.
2. **Stop rule for hypothesis work (H5):** α well below 0.40 → do **not** interpret H1–H4 / H6–H7 as evidence for parameter changes until rubric or panel is revised ([`HYPOTHESIS.md`](../../../../HYPOTHESIS.md) H5 consequence).
3. **Panel floor met, gold rule empty:** three independent seats are present (TUNING-PLAN minimum), but **A0 null** blocks the primary gold comparator for `P0`.
4. **Options (not chosen here):** majority rule (2/3 checkout), confidence-weighted aggregation, rubric revision to reduce Sonnet conservatism on Bash-heavy parity work, additional sessions/workers, or a different gold rule — each needs explicit pre-registration before sweep.

## Next steps (research only)

- Revise [`GOLD-LABEL-RUBRIC.md`](../../../../GOLD-LABEL-RUBRIC.md) or judge packs if Sonnet’s fail-open stance is miscalibrated vs Grok/Composer on hidden Bash output.
- Re-label or add human spot-check on `92a48e@105–180` before any non-`A0` gold rule is used in a lock memo.
- Jev replay / sweep remains blocked on H5 until agreement improves or the design explicitly adopts an alternate gold rule.

## Follow-on (same day)

`A_maj` and `A_gc` are computed in [`p0-alt-gold-targets-20261001.json`](p0-alt-gold-targets-20261001.json): both **180** on `92a48e004519` and **null** on `bb6165018de0`, identical at all 21 checkpoints. They are not adopted as the fit target. The chosen next measurement is the Sonnet re-label in [`../../../NEXT-EXPERIMENTS.md`](../../../NEXT-EXPERIMENTS.md). A0 and α in this file are unchanged. Confidence remains **not high**.
