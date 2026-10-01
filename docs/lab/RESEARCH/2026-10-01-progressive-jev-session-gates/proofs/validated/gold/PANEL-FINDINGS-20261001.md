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

`A_maj` and `A_gc` are computed in [`p0-alt-gold-targets-20261001.json`](p0-alt-gold-targets-20261001.json): both **180** on `92a48e004519` and **null** on `bb6165018de0`, identical at all 21 checkpoints. They are not adopted as the fit target.

## Experiment (b) — Sonnet re-label `parent-pull-v1` (**FAIL**, 2026-10-01)

Independent Sonnet 5.5 judgments on the same 21 hybrid_v0 pack rows, rubric revision **`parent-pull-v1`**, artifacts [`p0-checkout-verdicts-sonnet-relabel-20261001.jsonl`](p0-checkout-verdicts-sonnet-relabel-20261001.jsonl) and [`p0-checkout-verdicts-sonnet-relabel-SUMMARY-20261001.json`](p0-checkout-verdicts-sonnet-relabel-SUMMARY-20261001.json).

| Outcome | Detail |
|---------|--------|
| Scorecard | **Fail** — stop rule **over-fire** |
| Hold-out | **1** checkout on required hold-out prefix **`92a48e004519@255`** (rule 2) |
| Island cps 180/195/210 | All **checkout** (rule 1 satisfied) |
| Grok-only 105–165 | Sonnet **checkout on all 5** (reported only) |

**Not gold:** discard these rows; signed P0 Sonnet finals in `p0-checkout-verdicts-20261001.jsonl` stand. Do **not** adopt **A_maj** / **A_gc**. No Jev sweep.

**α hint if seat swapped (CHM):** nominal 3×21 α ≈ **0.5674** with this relabel seat — still **does not** override over-fire discard.

**Next measurement (was):** experiment **(c)** — now complete; see §(c) below. Primary next: **(d)** `ubuntu-thrash-screen-before-pack-v1` in [`../../../NEXT-EXPERIMENTS.md`](../../../NEXT-EXPERIMENTS.md). P0 A0/α in the table above are unchanged. Confidence remains **not high**.

---

## Experiment (c) — expansion panel `corpus-expand-hybrid-panel-original` (2026-10-01)

**Panel:** Sonnet 5.5 (`gold_seat`), Composer 2.5, Grok 4.7 high on **hybrid_v0** expansion packs (`expansion-judge-packs-20261001-202909.jsonl`). **Original rubric only** (no `parent-pull-v1`).  
**Schedule:** `75:15` on **`0aab88c525de`** (8 cps), **`036ff3ed4a89`** (6 cps), **`0853bc21d3aa`** (6 cps) → **20** pooled prefixes.  
**Machine-readable:** [`expansion-panel-agreement-20261001.json`](expansion-panel-agreement-20261001.json). Seat JSONLs: `expansion-checkout-verdicts-{sonnet,composer,grok}-20261001.jsonl`.

### Hard result — gold rule `A0` is null on all three expansion workers

| Worker | A0 | Earliest checkout by seat (Sonnet / Composer / Grok) |
|--------|-----|------------------------------------------------------|
| `0aab88c525de` | **null** | null / null / null |
| `036ff3ed4a89` | **null** | null / **135** / null |
| `0853bc21d3aa` | **null** | null / null / null |

Composer alone recommends checkout once (`036ff3ed4a89@135`; runaway + low_progress in rationale). Sonnet and Grok stay `not_yet` there and everywhere else. No prefix has all three seats on `checkout_recommended=true`.

### Reliability (H5 floor) — expansion-only 3×20

| Metric | Value | H5 floor (≥ 0.40) |
|--------|-------|-------------------|
| Krippendorff α (nominal, binary checkout, 3×20) | **0.0000** | **Fail** |
| Cohen κ sonnet ↔ composer | 0.0000 | — |
| Cohen κ sonnet ↔ grok | 0.0000 | — |
| Cohen κ composer ↔ grok | 0.0000 | — |

**Pairwise % agreement** (same/different checkout bit at each cp): sonnet↔composer **95.0%**, sonnet↔grok **100%**, composer↔grok **95.0%**. High agreement reflects shared `not_yet` on 19/20 prefixes; κ ≈ 0 is the prevalence paradox, not “moderate” pairwise reliability.

**Checkout-positive counts (20 cps):** Sonnet **0**, Composer **1**, Grok **0** → **1** total true label across 60 seat-rows.

### Implications

1. **H5 not passed for usable gold** — even though most prefixes agree on `not_yet`, **A0** is null on every expansion worker, so there is still no unanimous gold exit to tune against.
2. **Do not interpret high raw agreement as H5 pass** — agreement-on-false inflates apparent consensus while leaving **A0** empty; expansion α **0.0000** with a single positive seat-label is below the 0.40 floor.
3. **No Jev sweep** — same stop rule as P0. Pooled P0+expansion diagnostic α ≈ **0.1757** (41 cps) also fails H5 and does not create any new **A0**.
4. **Next measurement:** experiment **(d)** `ubuntu-thrash-screen-before-pack-v1` — screen Ubuntu workers for thrash/runaway-like sessions before packing, instead of random long `T ≥ 75` workers ([`../../../NEXT-EXPERIMENTS.md`](../../../NEXT-EXPERIMENTS.md)).
