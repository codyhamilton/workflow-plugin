# Session-analysis open field — cycle log

| cycle_id | approach | status | api_calls | kill | artifacts |
|----------|----------|--------|-----------|------|-----------|
| `phase-1a-marker-screen` | `marker-screen-margin` | `gate_cleared` | 0 | thrash_screen_strict vs poll: **PASS** (no poll workers in strict cell) | [`../proofs/phase-1a/`](../proofs/phase-1a/) |

## phase-1a-marker-screen

- **Registered:** [`REGISTRATION-phase-1a.md`](REGISTRATION-phase-1a.md)
- **Metric:** marker-family ranks, poll-overlap lists, Spearman vs `T` with/without thrash prototypes; round-trip mismatch rate 0 on pack `cumulative`.
- **Kill (approach §4):** extreme thrash cell must not contain poll-label workers — evaluated on `thrash_screen_strict` (no Edit/Write ∧ reread ≥ 8 ∧ compaction ≥ 8 at last cp ≤ 120).
- **Cox sketch:** exploratory concordance **1.0** on thrash-consensus proxy events (complete separation; not identified). Future gate concordance ≤ 0.70 **not** fired on this sketch.
