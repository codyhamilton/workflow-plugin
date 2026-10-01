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
| `PANEL-FINDINGS-20261001.md` | Human-readable panel result |

## Headline result (three-seat panel)

- Flash (excluded from gold panel): checkout on almost all `92a48e004519` cps; Sonnet signed final **always `not_yet`** on both workers.
- Grok earliest checkout on `92a48e004519`: **105**; Composer: **180**; Sonnet: **null**.
- **A0** (unanimous checkout): **null** on both workers — no cp where all three seats agree checkout.
- Krippendorff α = **0.1189** (< H5 floor 0.40). Confidence remains **not high**; panel count meets floor but gold exit does not.
- **A_maj** and **A_gc** recomputed from the signed JSONL are both **180** on `92a48e004519` and **null** on `bb6165018de0` ([`p0-alt-gold-targets-20261001.json`](p0-alt-gold-targets-20261001.json)). They are documented alternates, not the fit target. Next measurement: [`../../../NEXT-EXPERIMENTS.md`](../../../NEXT-EXPERIMENTS.md).

No `--call-jev` / `TYPESAFE_API_KEY` was used for labeling or this aggregation.
