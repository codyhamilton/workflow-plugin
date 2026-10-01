# Registration — phase 1a marker screen

**Cycle id:** `phase-1a-marker-screen`  
**Approach:** `marker-screen-margin` ([`CANDIDATE-APPROACHES.md`](../CANDIDATE-APPROACHES.md) §4)  
**Live TypeSafe:** no  
**Workers:** all **34** in `shape-qual-full-maps-v1` inventory  
**Card:** stats features from hybrid_v0 pack rows with `checkpoint_turn` ≤ **120** only  

## Metric

1. Feature JSONL (one row per worker): marker families from [`OPEN-FIELD.md`](../OPEN-FIELD.md) §2, stratum labels, `T`, round-trip vs pack `cumulative` on last early row (peak_ctx at first early row).
2. Rank tables: thrash-consensus percentiles, extreme-cell worker lists, poll-label overlap per family.
3. Spearman correlation with `T`, and same with thrash-consensus workers removed.
4. Text-growth quartile median-`T` table (`checkpoints_seen` ≥ 2).

## Kill (copied)

> The extreme cell that contains both thrash prototypes also contains any worker in the poll-label set. The screen does not proceed to a prose margin; the family definitions come back to the open field.

Operationalized for this cycle as **`thrash_screen_strict`** cell vs poll-label set `{87a380bc64ff, bb6165018de0, 15f24c7ba18c, 8e36f8e80baa}`.

## Alternate E sketch (same cycle, 0 calls)

Cox PH exploratory script with censoring at `T` and thrash-consensus proxy events; document future gate concordance ≤ **0.70**.
