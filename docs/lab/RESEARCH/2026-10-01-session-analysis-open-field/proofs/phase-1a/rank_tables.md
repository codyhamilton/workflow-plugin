# Marker rank tables (phase 1a)

## Combined kill cell — `thrash_screen_strict`

**Kill check:** PASS

Workers: `92a48e004519`, `ca977b9ca0dd`

## Boolean families (thrash prototype cell + poll overlap)

| family | cell n | poll overlap |
|--------|-------:|--------------|
| `frozen_text` | 2 | none |
| `no_mutation` | 6 | `87a380bc64ff` |
| `bash_read_monopoly` | 4 | none |
| `monitor_present_first` | 19 | none |
| `mutation_present_first` | 6 | `87a380bc64ff` |
| `reread_cluster` | 21 | `87a380bc64ff`, `8e36f8e80baa`, `bb6165018de0` |
| `thrash_screen_strict` | 2 | none |

## Numeric families

| family | ρ vs T | ρ vs T (no thrash prototypes) | thrash pct ca977 | thrash pct 92a48e | poll overlap |
|--------|-------:|------------------------------:|-----------------:|------------------:|--------------|
| `compaction_last_le120` | 0.2229371956417723 | 0.12230893919432981 | 95.58823529411765 | 98.52941176470588 | 0 |
| `compaction_delta_le120` | 0.33662012334139724 | 0.23354845797016147 | 95.58823529411765 | 98.52941176470588 | 0 |
| `reread_max` | 0.4012565725410288 | 0.33387903115177703 | 98.52941176470588 | 95.58823529411765 | 0 |
| `text_growth` | 0.2512408929458762 | 0.45015275658873033 | 3.8461538461538463 | 3.8461538461538463 | 3 |
| `peak_ctx_first` | 0.029051996258031176 | 0.08108607337060238 | 27.941176470588236 | 39.705882352941174 | 2 |
| `assistant_text_chars_last` | 0.10183489214657243 | 0.24527619931333797 | 10.294117647058824 | 1.4705882352941178 | 4 |
| `checkpoints_seen_le120` | 0.9555539739295621 | 0.9504816414408656 | 67.6470588235294 | 86.76470588235294 | 1 |
| `monitor_count_first` | -0.2793366021642665 | -0.22956321288347536 | 27.941176470588236 | 27.941176470588236 | 4 |
