# Safe judge packs (hybrid_v0) — progressive Jev gold seats 3–4

**Audience:** Workflow System Manager cloud agents (Grok 4.7 high, Composer) applying
[`GOLD-LABEL-RUBRIC.md`](../../../../../GOLD-LABEL-RUBRIC.md) without Ubuntu raw transcripts.

**Status:** commit-safe omit-state / hybrid_v0 budget. Raw `*-gold-bundles-*.jsonl` and
`*.with-state.jsonl` remain **gitignored** under `../ubuntu-raw/`.

## How to judge

For each JSONL row `(worker_id, checkpoint_turn)`:

1. Read **only** that row’s pack fields (do not fetch raw transcripts).
2. Apply the rubric question: *Has continuing this worker past turn `c` already become a mistake?*
3. Answer `not_yet` or `checkout`. If `checkout`, mark ≥1 pattern:
   `runaway` | `low_progress` | `context_thrash` | `scope_drift`.
4. Rationale ≤120 words; cite only turns ≤ `c` that appear in this pack.
5. Do **not** use turn count alone, maps nicknames (“smoking gun”), or prior seats’ labels.

Write one verdict row per pack row (same shape as `../p0-checkout-verdicts-20261001.jsonl`
`role=reviewer_final`: `decision`, `patterns`, `checkout_recommended`, `rationale`,
`first_checkout_guess`, `model`, `signed`).

## Budget (hybrid_v0)

| Field | Cap |
|-------|-----|
| `snapshot_mode` | `hybrid_v0` |
| `tail` | last **N=8** assistant turns |
| `excerpt` | **400** chars (secrets + paths redacted before clip) |
| `brief_anchor` | 500 chars |
| `thrash_top_rereads` | up to 8 paths read ≥3× (repo-relative tokens) |

This is the progressive-gates Jev state budget (`TERMS.md` §5), **not** the full gold
bundle (30×700 / 60k) used by seats 1–2 on local gold-bundles. Cloud seats trade
tail depth for a pack that can leave Ubuntu.

## Row fields

| Field | Meaning |
|-------|---------|
| `worker_id`, `checkpoint_turn`, `schedule` | P0 `75:15` identity |
| `brief_anchor` | First user text, path-redacted |
| `api_turns_note` | `api_turns = c` (prefix length only) |
| `cumulative` | Prefix stats: peak ctx, tool histogram, rereads, compactions, … |
| `delta_since_prior` | New reads + tool histogram since prior checkpoint |
| `thrash_top_rereads` | Same top re-read list as ubuntu-raw thrash table (redacted) |
| `tail` | `[{turn, excerpt, tool_names}]` — tool results omitted |
| `pack_chars` | Serialized size of this pack row |
| `pack_meta` | Provenance + redaction note |

Absolute Ubuntu paths are replaced with `<REPO>/`, `<HOME>/`, `<MOUNT>/…`,
`<TMP_CLAUDE>/…`. Username tokens scrubbed.

## Files

### Smoking-gun seats (run `20261001-194107`)

| File | Rows |
|------|------|
| `92a48e004519-judge-packs-20261001-194107.jsonl` | 15 (cps 75…285) |
| `bb6165018de0-judge-packs-20261001-194107.jsonl` | 6 (cps 75…150) |
| `p0-judge-packs-20261001-194107.jsonl` | 21 combined (convenience) |

### Expansion open-pajero-maps workers (run `20261001-202909`)

Same schema / hybrid_v0 budget / P0 schedule `75:15`. No gold verdicts — packs only.

| File | T | Rows |
|------|---|------|
| `0aab88c525de-judge-packs-20261001-202909.jsonl` | 192 | 8 (cps 75…180) |
| `036ff3ed4a89-judge-packs-20261001-202909.jsonl` | 161 | 6 (cps 75…150) |
| `0853bc21d3aa-judge-packs-20261001-202909.jsonl` | 155 | 6 (cps 75…150) |
| `expansion-judge-packs-20261001-202909.jsonl` | — | 20 combined |

Regenerate locally (needs gitignored gold-bundles on the Ubuntu box):

```bash
python3 docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/build_gold_judge_packs.py \
  --run 20261001-194107 --workers 92a48e004519 bb6165018de0

python3 docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/build_gold_judge_packs.py \
  --run 20261001-202909 --workers 0aab88c525de 036ff3ed4a89 0853bc21d3aa
```

### Thrash-screen shortlist — experiment (d) (run `20261001-204508`)

Screened `T≥75` open-pajero-maps workers for runaway / low_progress / context_thrash-like dry-run signals before packing. Same schema / hybrid_v0 budget / `75:15`. **No gold verdicts** — packs only; panel held.

| File | T | Rows | Screen note |
|------|---|------|-------------|
| `ca977b9ca0dd-judge-packs-20261001-204508.jsonl` | 109 | 3 (cps 75…105) | Top thrash twin of smoking gun (reread/compact, no Edit/Write) |
| `7b00225cb824-judge-packs-20261001-204508.jsonl` | 137 | 5 (cps 75…135) | Sleep/poll runaway class (17 sleep bash) |
| `daf933273c8f-judge-packs-20261001-204508.jsonl` | 122 | 4 (cps 75…120) | Bash-spin + frozen intervals + compaction |
| `thrash-screen-judge-packs-20261001-204508.jsonl` | — | 12 combined | |
| `SUMMARY-thrash-screen-20261001-204508.{md,json}` | — | — | Ranking table (safe metrics) |

```bash
python3 docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/build_gold_judge_packs.py \
  --run 20261001-204508 --workers ca977b9ca0dd 7b00225cb824 daf933273c8f
# then rename combined p0-judge-packs-*.jsonl → thrash-screen-judge-packs-*.jsonl
```

## What is *not* here

- Raw gold-bundles / with-state hybrid prose dumps
- Full 30-turn gold tails
- Jev answers / `--call-jev` results
- Prior seat verdicts (do not contaminate seats 3–4)

## Thrash-expand (e) — `ubuntu-thrash-high-score-expand-v1` (`20261001-210125`)

Best-available ca977-shaped shortlist after empty strict pool (no Edit/Write ∧ max_reread≥8 ∧ compact≥8 on remaining T≥75). Schedule `75:15`. hybrid_v0 (`N=8`, excerpt 400). Panel **held**.

| Worker | T | Cps | Pack |
|--------|--:|----:|------|
| `e8aa4f271927` | 76 | 1 | `e8aa4f271927-judge-packs-20261001-210125.jsonl` |
| `5163c22a6a3e` | 90 | 2 | `5163c22a6a3e-judge-packs-20261001-210125.jsonl` |
| `a318f4b89a6a` | 95 | 2 | `a318f4b89a6a-judge-packs-20261001-210125.jsonl` |

Combined: `thrash-expand-e-judge-packs-20261001-210125.jsonl` (5 rows). Ranking: `SUMMARY-thrash-expand-e-20261001-210125.md`.
