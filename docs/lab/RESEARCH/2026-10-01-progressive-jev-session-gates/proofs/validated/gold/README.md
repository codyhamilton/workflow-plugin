# Progressive Jev — multi-model gold checkout verdicts (P0)

**Status:** two-seat draft gold (Flash draft → Sonnet 5.5 signed review).  
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
4. Optional Grok/Composer: **skipped** (no credentials on this machine without new secrets).

## Files

| File | Contents |
|------|----------|
| `p0-checkout-verdicts-20261001.jsonl` | 42 rows = 21 cps × (Flash draft + Sonnet final) |
| `p0-checkout-verdicts-SUMMARY-20261001.json` | Models, per-judge first-checkout, A0 note |

## Headline result (this run)

- Flash: checkout on almost all `92a48e004519` cps and most early `bb6165018de0` cps.
- Sonnet 5.5: **corrected every Flash checkout to `not_yet`** on both workers (one Flash `not_yet` at `bb6165018de0@150` agreed).
- A0 unanimous gold exit: **null** on both workers with this two-seat panel.
- Panel remains **underpowered** vs TUNING-PLAN’s three-judge floor until Grok (or another seat) is added.

No `--call-jev` / `TYPESAFE_API_KEY` was used for this PR.
