# Thrash-expand (e) shortlist — experiment `ubuntu-thrash-high-score-expand-v1`

**Run:** `20261001-210125` · schedule `75:15` · hybrid_v0 packs only · **panel held** (no seat labels).

Strict ca977 shape (no Edit/Write ∧ max_reread≥8 ∧ compact≥8) empty on remaining T≥75 pool (n=26). Pre-registered N=3 best-available: near-zero-EW non-poll `e8aa4f271927`; high-reread twin `5163c22a6a3e`; high-compact `a318f4b89a6a`. Poll/bash-only class excluded (e.g. `87a380bc64ff` Monitor=6).

Screened open-pajero-maps Claude workers with `T≥75` (n=34; remaining after excludes n=26). Excluded smoking guns `92a48e004519`/`bb6165018de0`, expansion `0aab88c525de`/`036ff3ed4a89`/`0853bc21d3aa`, and (d) thrash `ca977b9ca0dd`/`daf933273c8f`/`7b00225cb824`. Prefer no/near-zero Edit/Write, high max-reread, high compaction, high peak; deprioritize sleep/poll and bash-monitor class.

| Rank | Worker | T | Thrash score | Why ca977-shaped | Safe metrics | Cps |
|-----:|--------|--:|-------------:|------------------|--------------|----:|
| 1 | `e8aa4f271927` | 76 | 25.14 | near-zero Edit/Write + reread/compact (closest remaining to ca977 EW axis) | max_reread=5; paths≥3=2; compact=4; near-zero Edit/Write=3; peak=125388; bash_frac=0.71; Monitor=1 | 1 |
| 2 | `5163c22a6a3e` | 90 | 31.85 | high-reread twin (max_reread=9, peak≈161k); best available after empty strict ca977; Edit/Write present | max_reread=9; paths≥3=1; compact=2; frozen_intervals=1; peak=161373; Monitor=2 | 2 |
| 3 | `a318f4b89a6a` | 95 | 30.38 | high-compact match (compact=8, paths≥3=3, peak≈127k); best available compaction axis after empty strict ca977 | max_reread=5; paths≥3=3; compact=8; frozen_intervals=1; peak=126978 | 2 |

**Reference:** smoking gun `92a48e004519` thrash score ≈ 151; (d) `ca977b9ca0dd` ≈ 71 (max_reread=14, compact=16, no Edit/Write).

**Combined pack:** `thrash-expand-e-judge-packs-20261001-210125.jsonl` (5 rows).

No gold verdicts. No `--call-jev`. No `parent-pull-v1`. Raw gold-bundles/with-state stay gitignored under `ubuntu-raw/`.
