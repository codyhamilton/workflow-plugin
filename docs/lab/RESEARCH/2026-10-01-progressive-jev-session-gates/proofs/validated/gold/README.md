# Progressive Jev — multi-model gold checkout verdicts (P0)

**Status:** three-seat P0 gold panel (Sonnet signed final + Composer + Grok 4.7); Flash drafts excluded from panel metrics.  
**Agreement:** [`PANEL-FINDINGS-20261001.md`](PANEL-FINDINGS-20261001.md), [`p0-panel-agreement-20261001.json`](p0-panel-agreement-20261001.json).  
**Not committed here:** raw gold-bundles / ubuntu-raw transcripts (gitignored under `../ubuntu-raw/`).

## What `checkout_recommended` means

From [`GOLD-LABEL-RUBRIC.md`](../../../../GOLD-LABEL-RUBRIC.md): at labeled turn `c`, has continuing this worker past `c` already become a mistake?

| Value | Meaning |
|-------|---------|
| `false` (`decision=not_yet`) | Prefix still supports more work, or evidence too thin |
| `true` (`decision=checkout`) | Fresh worker / stop is warranted; requires ≥1 pattern |

Turn count alone must not drive checkout. Patterns: `runaway`, `low_progress`, `context_thrash`, `scope_drift`.

## P0 schedule

`first_at=75`, `interval=15` → checkpoints `75,90,105,…` while `c <= T`.

| Worker | T | Checkpoints labeled |
|--------|---|---------------------|
| `92a48e004519` | 296 | 15 (75…285) |
| `bb6165018de0` | 154 | 6 (75…150) |

## Review chain (Cody Flash gate)

1. **DeepSeek Flash** (`deepseek/deepseek-flash` via OpenCode) drafts each `(worker, cp)` from the gold-bundle row only.
2. **Claude Sonnet 5.5** (`claude-sonnet-5-5` via `claude -p`) independently re-judges and **agree/correct**s the draft.
3. Only `role=reviewer_final` rows with `signed=true` count as signed labels for downstream use.
4. **Composer 2.5** and **Grok 4.7** gold seats on redacted judge packs (`packs/p0-judge-packs-*.jsonl`).

## Safe packs for cloud seats (3–4)

See [`packs/`](packs/) — hybrid_v0 redacted judge packs (`N=8`, excerpt 400) derived from
gitignored gold-bundles. WSM points Grok / Composer at `packs/p0-judge-packs-*.jsonl`
(or per-worker files). No raw Ubuntu paths.

## Files

| File | Contents |
|------|----------|
| `p0-checkout-verdicts-20261001.jsonl` | 42 rows = 21 cps × (Flash draft + Sonnet final) |
| `p0-checkout-verdicts-composer-20261001.jsonl` | Composer seat, 21 cps |
| `p0-checkout-verdicts-grok-20261001.jsonl` | Grok seat, 21 cps |
| `p0-checkout-verdicts-SUMMARY-20261001.json` | Two-seat summary (pre-panel); see panel JSON for A0 |
| `p0-panel-agreement-20261001.json` | Three-seat A0, pairwise agreement, α |
| `p0-alt-gold-targets-20261001.json` | A_maj and A_gc from the signed JSONL. Both 180 / null. Not a fit target |
| `p0-checkout-verdicts-sonnet-relabel-20261001.jsonl` | Experiment **(b)** `parent-pull-v1` Sonnet seat — **discarded as gold** (over-fire @255) |
| `p0-checkout-verdicts-sonnet-relabel-SUMMARY-20261001.json` | (b) scorecard + CHM α hint ≈ 0.57 — **not** adopted |
| `PANEL-FINDINGS-20261001.md` | Human-readable panel result |
| `expansion-checkout-verdicts-*-20261001.jsonl` | Experiment **(c)** three-seat labels (20 cps each) |
| `expansion-panel-agreement-20261001.json` | **(c)** A0, α, pairwise metrics |
| `thrash-screen-checkout-verdicts-*-20261001.jsonl` | Experiment **(d)** three-seat labels (12 cps each) |
| `thrash-screen-panel-agreement-20261001.json` | **(d)** A0, α, pairwise metrics |
| `thrash-screen-panel-SCORECARD-20261001.md` | **(d)** gate table (H5 pass; Jev still blocked) |
| `thrash-expand-e-checkout-verdicts-*-20261001.jsonl` | Experiment **(e)** three-seat labels (5 cps each) |
| `thrash-expand-e-panel-agreement-20261001.json` | **(e)** A0 null × 3; α undefined (all `not_yet`) |
| `thrash-de-panel-agreement-20261001.json` | **(d)+(e)** 17 prefixes; still one A0 (`ca977b9ca0dd` @ 90) |
| `thrash-expand-e-panel-SCORECARD-20261001.md` | **(e)** gate table (miss; Jev still blocked) |

## Headline result (three-seat panel)

- Flash (excluded from gold panel): checkout on almost all `92a48e004519` cps; Sonnet signed final **always `not_yet`** on both workers.
- Grok earliest checkout on `92a48e004519`: **105**; Composer: **180**; Sonnet: **null**.
- **A0** (unanimous checkout): **null** on both workers — no cp where all three seats agree checkout.
- Krippendorff α = **0.1189** (< H5 floor 0.40). Confidence remains **not high**; panel count meets floor but gold exit does not.
- **A_maj** and **A_gc** recomputed from the signed JSONL are both **180** on `92a48e004519` and **null** on `bb6165018de0` ([`p0-alt-gold-targets-20261001.json`](p0-alt-gold-targets-20261001.json)). They are documented alternates, not the fit target.
- Experiment **(b)** Sonnet re-label under `parent-pull-v1` **failed** (hold-out checkout at `92a48e@255`; checkout on all Grok-only 105–165). Relabel JSONL is **not** gold.
- Experiment **(c)** expansion panel **complete** — **A0 null** on `0aab88c525de`, `036ff3ed4a89`, `0853bc21d3aa`; expansion-only α **0.0000** (3×20); see [`expansion-panel-agreement-20261001.json`](expansion-panel-agreement-20261001.json) and [`PANEL-FINDINGS-20261001.md`](PANEL-FINDINGS-20261001.md) §(c).
- Experiment **(d)** thrash-screen panel **complete** — **A0 = 90** on `ca977b9ca0dd` only (**null** on `daf933273c8f` and `7b00225cb824`); thrash-only α **0.8276** (3×12) **passes** H5. Jev stays blocked (single A0). See [`thrash-screen-panel-agreement-20261001.json`](thrash-screen-panel-agreement-20261001.json) and [`PANEL-FINDINGS-20261001.md`](PANEL-FINDINGS-20261001.md) §(d).
- Experiment **(e)** thrash-expand panel **complete — miss.** Strict ca977 shape empty on the remaining maps pool. **A0 null** on `e8aa4f271927`, `5163c22a6a3e`, and `a318f4b89a6a` (0/5 checkout, every seat). Expand-only α is **undefined** (all `not_yet`; a 1.0 De=0 convention is not a pass). Combined (d)+(e) α **0.8377** on 17 prefixes still has **one** non-null A0. Jev stays blocked. See [`thrash-expand-e-panel-agreement-20261001.json`](thrash-expand-e-panel-agreement-20261001.json) and [`PANEL-FINDINGS-20261001.md`](PANEL-FINDINGS-20261001.md) §(e). Next: **(f)** — [`../../../NEXT-EXPERIMENTS.md`](../../../NEXT-EXPERIMENTS.md).

No `--call-jev` / `TYPESAFE_API_KEY` was used for labeling or this aggregation.
