# Thrash-screen (d) shortlist — experiment `ubuntu-thrash-screen-before-pack-v1`

**Run:** `20261001-204508` · schedule `75:15` · hybrid_v0 packs only · **panel held** (no seat labels).

Screened open-pajero-maps Claude workers with `T≥75` (n=29 after excludes). Excluded smoking guns `92a48e004519`/`bb6165018de0` and expansion already packed `0aab88c525de`/`036ff3ed4a89`/`0853bc21d3aa`. Ranked by thrash/runaway-like dry-run signals (reread intensity, paths≥3, compaction, frozen intervals, bash spin, sleep/poll); prefer smoking-gun shape over productive-edit census tails.

| Rank | Worker | T | Thrash score | Why (safe metrics) | Cps |
|-----:|--------|--:|-------------:|--------------------|----:|
| 1 | `ca977b9ca0dd` | 109 | 71.07 | max_reread=14; paths≥3=5; compact=16; no Edit/Write; peak=127736 | 3 |
| 2 | `7b00225cb824` | 137 | 25.75 | max_reread=7; sleep_bash=17; pollish=8 (runaway wait/poll class) | 5 |
| 3 | `daf933273c8f` | 122 | 21.69 | compact=8; peak=125620; bash_frac=0.86; frozen_intervals=2; sleep_bash=6 | 4 |

**Reference:** smoking gun `92a48e004519` thrash score ≈ 151 (max_reread=26, compact=40, frozen=13, no Edit/Write).

**Combined pack:** `thrash-screen-judge-packs-20261001-204508.jsonl` (12 rows).

No gold verdicts. No `--call-jev`. No `parent-pull-v1`. Raw gold-bundles/with-state stay gitignored under `ubuntu-raw/`.
