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

## Aggregating these rows

`aggregate_gold.py` reads this directory. A row votes only when `signed` is true. On this file that is the Sonnet `reviewer_final` seat. Unsigned Flash `role=draft` rows stay in `draft_review` (20 checkouts corrected to `not_yet`, one agree on `not_yet`). They do not set `gold_exit`.

Reserved seats `grok-4.7-high` and `composer` stay `pending` until CHM commits signed packs in this directory. Primary `gold_exit` stays null until three seats have voted. That null is an incomplete panel. It is not a decision that either worker should have run to `T`.

```bash
cd docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs
python3 aggregate_gold.py \
  --labels validated/gold \
  --out validated/gold/summary.json
python3 score_vs_gold.py \
  --replay validated/ubuntu-raw/92a48e004519-dry-run-checkpoints-20261001-194107.omit-state.jsonl \
  --replay validated/ubuntu-raw/bb6165018de0-dry-run-checkpoints-20261001-194107.omit-state.jsonl \
  --metrics validated/ubuntu-raw/92a48e004519-dry-run-metrics-20261001-194107.json \
  --metrics validated/ubuntu-raw/bb6165018de0-dry-run-metrics-20261001-194107.json \
  --gold validated/gold/summary.json
```

`score_vs_gold.py` leaves `overshoot`, `false_early`, and `false_late` null while `gold_exit` is null. A dry-run replay still reports `max_allowed_turns = T` because no checkpoint fired. Confidence stays not high.
