# Phase 1a — marker screen (`marker-screen-margin`)

**Approach:** `marker-screen-margin` · **API calls:** 0 · **Pack:** shape-qual-full-maps-v1 (n=34)

**Round-trip gate:** PASS (mismatch rows=0)

**Kill check (thrash_screen_strict cell vs poll labels):** PASS

- Strict cell workers (2): `92a48e004519`, `ca977b9ca0dd`
- Poll overlap: none

## Spearman vs T (numeric families)

| family | ρ all | ρ without thrash prototypes | poll overlap in extreme tail |
|--------|------:|----------------------------:|------------------------------|
| `compaction_last_le120` | 0.2229371956417723 | 0.12230893919432981 | 0 |
| `compaction_delta_le120` | 0.33662012334139724 | 0.23354845797016147 | 0 |
| `reread_max` | 0.4012565725410288 | 0.33387903115177703 | 0 |
| `text_growth` | 0.2512408929458762 | 0.45015275658873033 | 3 |
| `peak_ctx_first` | 0.029051996258031176 | 0.08108607337060238 | 2 |
| `assistant_text_chars_last` | 0.10183489214657243 | 0.24527619931333797 | 4 |
| `checkpoints_seen_le120` | 0.9555539739295621 | 0.9504816414408656 | 1 |
| `monitor_count_first` | -0.2793366021642665 | -0.22956321288347536 | 4 |

## Cox sketch (exploratory)

- Status: `exploratory_ok`
- Concordance index: 1.0
- Future gate (concordance ≤ 0.70): would not kill Alternate E on this proxy

See `cox_sketch.json` and `run_cox_sketch.py`.
