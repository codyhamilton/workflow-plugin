# Shape-signal panel agreement — `shape-signal-panel-v1`

**Date:** 2026-10-01 (Brisbane) · **Protocol:** [`TERMS.md`](../../../TERMS.md) §11

**Weight order (Cody):** (1) shared early signals / shape / inflections — **primary**; (2) exit-turn spread — **secondary**, not a hard fail.

**Seats:** Composer PR [#66](https://github.com/codyhamilton/workflow-plugin/pull/66) · Grok [#67](https://github.com/codyhamilton/workflow-plugin/pull/67) · Sonnet [#68](https://github.com/codyhamilton/workflow-plugin/pull/68). Pack: `shape-signal-judge-packs-20261001-212524.jsonl` (45 rows, hybrid_v0, `75:15`).

**Jev:** No `--call-jev`. **Hold Jev behaviour ship.**

## Highlights table

| Worker | Composer | Grok | Sonnet | Shape majority | Exit (C/G/S) | Spread | Notes |
|--------|----------|------|--------|----------------|--------------|--------|-------|
| `92a48e` | late_pivot | early_thrash | unclear | **split** | 180/90/null | 90 | Shape split, but thrash early signals around ~90 appear in ≥1 seat (Grok exits@90; Composer flags first_clear_thrash@90 in earliness). |
| `ca977b` | early_thrash | early_thrash | early_thrash | **early_thrash** | 90/90/75 | 15 | Unanimous early_thrash; recommended exits 75–90. |
| `bb6165` | late_pivot | unclear | unclear | **unclear** | null/null/150 | — | Wait-bound contrast; majority unclear; exit secondary. |
| `0aab88` | late_pivot | unclear | unclear | **unclear** | null/null/null | — | Agree on productive-then-wait character; no seat names an early thrash exit. |
| `036ff3` | late_pivot | unclear | unclear | **unclear** | 135/null/null | — | Prior expansion Composer-only@135 echoes; still not majority early_thrash. |
| `7b0022` | late_pivot | unclear | unclear | **unclear** | null/null/135 | — | Agree not early_thrash; exit secondary near closure. |
| `5163c2` | late_pivot | unclear | unclear | **unclear** | null/null/null | — | Shape-miss expand class: productive then sanctioned wait; no thrash exit. |

### Spotlight

- **`ca977b9ca0dd`:** unanimous **`early_thrash`**; recommended exits **75–90** (Sonnet 75; Composer & Grok 90). Shared early signals: zero Edit/Write, `_cenc`/divide/`_e2` re-read loop, high compaction, frozen ~167-char text by the first checkpoints.
- **`92a48e004519`:** shape **split** (`late_pivot` / `early_thrash` / `unclear`) but thrash signals around **~90** appear in ≥1 seat (Grok exit@90; Composer earliness notes too_late vs first_clear_thrash@90). Exit spread 90 vs 180 vs null is secondary under §11.
- **Other five:** majority **`unclear`** (Composer often the lone `late_pivot`). Shared character is wait/implement arcs, not ca977 thrash. Finite exits only where a seat names late closure (Sonnet @150 on `bb6165`, @135 on `7b0022`; Composer @135 on `036ff3`).

## Per-worker agreement notes

### `92a48e004519` (T=296)

- **Shape votes:** composer=`late_pivot`, grok=`early_thrash`, sonnet=`unclear` → majority **`split`**
- **Recommended exit:** composer=180, grok=90, sonnet=null; spread=90
- **Shared early signals / agree:**
  - By cp75: zero Edit/Write; heavy _cenc.c / divide.py / _e2.c re-reads; high compaction (~12); tiny assistant text; Bash/Read-only histogram on a small path set.
  - By cp90: interval still Bash-heavy with empty/new_paths empty; re-read counters climb; thrash character already visible (Composer notes too_late vs first_clear_thrash@90 even while labeling late_pivot@180).
- **Disagree:**
  - Shape three-way split: Composer late_pivot (exit 180), Grok early_thrash (exit 90), Sonnet unclear (exit null — later recovery / gates).
  - Exit spread secondary: 90 vs 180 vs null; not a hard fail under TERMS §11.

### `ca977b9ca0dd` (T=109)

- **Shape votes:** composer=`early_thrash`, grok=`early_thrash`, sonnet=`early_thrash` → majority **`early_thrash`**
- **Recommended exit:** composer=90, grok=90, sonnet=75; spread=15
- **Shared early signals / agree:**
  - Unanimous early_thrash: zero Edit/Write; _cenc / divide / _e2 re-read loop; high compaction; frozen ~167-char assistant text by cp75–90.
  - All seats name early thrash checkpoints in the 75–90 band as the first clear mistake-to-continue.
- **Disagree:**
  - Exit only: Sonnet 75 vs Composer/Grok 90 (spread 15 = one interval).

### `bb6165018de0` (T=154)

- **Shape votes:** composer=`late_pivot`, grok=`unclear`, sonnet=`unclear` → majority **`unclear`**
- **Recommended exit:** composer=null, grok=null, sonnet=150; spread=None (1 non-null)
- **Shared early signals / agree:**
  - Census / monitor wait dominates early (standing by / waiting for census); not ca977 zero-edit thrash (Write present; rich text; 0 compactions).
  - Majority shape unclear (2/3); Composer alone late_pivot with null exit (on-brief wait).
- **Disagree:**
  - Sonnet recommends exit 150 (census finish / analysis start); Composer and Grok null.

### `0aab88c525de` (T=192)

- **Shape votes:** composer=`late_pivot`, grok=`unclear`, sonnet=`unclear` → majority **`unclear`**
- **Recommended exit:** composer=null, grok=null, sonnet=null; spread=None
- **Shared early signals / agree:**
  - Implementation trajectory with Edits on alldata_writer; re-reads are owned-file work, not zero-edit thrash.
  - Majority unclear; all three recommended_exit null.
- **Disagree:**
  - Composer labels late_pivot (null exit — sanctioned fixture wait after productive stretch); Grok/Sonnet unclear.

### `036ff3ed4a89` (T=161)

- **Shape votes:** composer=`late_pivot`, grok=`unclear`, sonnet=`unclear` → majority **`unclear`**
- **Recommended exit:** composer=135, grok=null, sonnet=null; spread=None (1 non-null)
- **Shared early signals / agree:**
  - Early Bash-heavy / blocking-wait on compare_disc and long runs; seats note wait windows that can look poll-like but resolve.
  - Majority unclear (Grok+Sonnet); Composer late_pivot@135.
- **Disagree:**
  - Only Composer names recommended_exit 135; others null.

### `7b00225cb824` (T=137)

- **Shape votes:** composer=`late_pivot`, grok=`unclear`, sonnet=`unclear` → majority **`unclear`**
- **Recommended exit:** composer=null, grok=null, sonnet=135; spread=None (1 non-null)
- **Shared early signals / agree:**
  - Edits/Writes present early; wait/pytest stretches are bounded inside an implement-then-wait arc (not ca977 thrash).
  - Majority unclear; Composer late_pivot null.
- **Disagree:**
  - Sonnet exit 135 (commit/push); Composer/Grok null.

### `5163c22a6a3e` (T=90)

- **Shape votes:** composer=`late_pivot`, grok=`unclear`, sonnet=`unclear` → majority **`unclear`**
- **Recommended exit:** composer=null, grok=null, sonnet=null; spread=None
- **Shared early signals / agree:**
  - Early Edit/Write bulk then Perth extractor / monitor wait; rules out ca977-style zero-edit thrash.
  - Majority unclear; all exits null.
- **Disagree:**
  - Composer late_pivot (null); Grok/Sonnet unclear.

## Consequences

1. Signal/shape agreement exists on **several** workers for thrash foreshadowing (`ca977` unanimous; `92a48e` shared ~90 thrash signals despite shape split).
2. Exact exit unanimity is **not** required and was not achieved on the ~300T runaway — expected under §11.
3. Still **hold** Jev behaviour ship and do **not** `--call-jev` until progressive revalidation (TERMS §12) and any validation-phase handoff design are absorbed.
4. Seat prompts are **not** rewritten by this agreement PR.

Machine-readable twin: [`shape-signal-agreement-SUMMARY-20261001.json`](shape-signal-agreement-SUMMARY-20261001.json).
