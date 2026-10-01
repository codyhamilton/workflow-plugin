# Shape-signal panel (v1) shortlist — experiment `shape-signal-panel-v1`

**Run:** `20261001-212524` · schedule `75:15` · hybrid_v0 packs · **panel held** (Phase 1: docs + packs only).

**Gold protocol (Cody 2026-10-01):** supersedes unanimous A0 / ≥2 A0 gate. Per-seat questions cover shape (`late_pivot` vs `early_thrash`), why T is large, inflection points, early signals, and recommended exit + earliness. **Agreement worth:** multi-model agreement on early signals / shape / inflections ≫ exact exit turn; exit-turn spread is a secondary metric, not a hard fail.

**Pool:** reopen Maps `T≥75` including prior A0-null / shape-miss; prefer diverse; include ~300T runaway; no padding. All packs **reused** (no new `build_gold_judge_packs.py` run).

| Rank | Worker | T | Cps | Pack source | Diversity role | Why chosen |
|-----:|--------|--:|----:|-------------|----------------|------------|
| 1 | `92a48e004519` | 296 | 15 | reuse `92a48e004519-judge-packs-20261001-194107.jsonl` | `runaway_~300T` | P0 smoking gun / ~296T runaway; prior A0 null |
| 2 | `ca977b9ca0dd` | 109 | 3 | reuse `ca977b9ca0dd-judge-packs-20261001-204508.jsonl` | `prior_A0_hit` | thrash-screen (d) A0=90 hit; early_thrash candidate |
| 3 | `bb6165018de0` | 154 | 6 | reuse `bb6165018de0-judge-packs-20261001-194107.jsonl` | `P0_null_contrast` | P0 hold-out / census-wait; A0 null; possible late_pivot or healthy long |
| 4 | `0aab88c525de` | 192 | 8 | reuse `0aab88c525de-judge-packs-20261001-202909.jsonl` | `expansion_null_long` | expansion (c) A0 null; long census-wait class |
| 5 | `036ff3ed4a89` | 161 | 6 | reuse `036ff3ed4a89-judge-packs-20261001-202909.jsonl` | `expansion_null_partial` | expansion (c) A0 null; Composer-only @135 (disagreement mass) |
| 6 | `7b00225cb824` | 137 | 5 | reuse `7b00225cb824-judge-packs-20261001-204508.jsonl` | `thrash_null_sleep_poll` | thrash-screen (d) A0 null; sleep/poll runaway class |
| 7 | `5163c22a6a3e` | 90 | 2 | reuse `5163c22a6a3e-judge-packs-20261001-210125.jsonl` | `shape_miss_expand` | thrash-expand (e) shape-miss; A0 null |

**Combined pack:** `shape-signal-judge-packs-20261001-212524.jsonl` (45 rows). Leak-scan: **PASS** (needles `/home/`, `codyh`, `/media/`, `/mnt/`, `sk-ant`).

**Hold:** no seats in this task. No `--call-jev`. No `parent-pull-v1`. Hold Jev behaviour ship until signal-agreement notes exist on several workers.
