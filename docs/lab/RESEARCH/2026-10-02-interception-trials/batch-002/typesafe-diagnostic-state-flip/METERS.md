# METERS — TypeSafe diagnostic state flip

**Soft Standard HOLD** — diagnostic evidence only; no hooks, behavior, unlock, or FP/miss scoreboard.

This extends the non-label-ready 12×7 response-calibration stratum from #114.
It compares `markers_focus` with `phase_hints_focus` across the same
twelve preferred pairs and seven diagnostic representative joins.

- status: **complete**
- representative pairs: **7**
- planned cells: **336**
- successful cells: **336**
- HTTP/error rows: `{"200": 336}`
- cell-id collisions: **0**

| state × response class | n | fire | fire rate |
|---|---:|---:|---:|
| `markers_focus|binary_fire` | 84 | 13 | 0.1548 |
| `markers_focus|four_class` | 84 | 18 | 0.2143 |
| `phase_hints_focus|binary_fire` | 84 | 18 | 0.2143 |
| `phase_hints_focus|four_class` | 84 | 18 | 0.2143 |

These are response distributions only. The seven representatives are
not label-ready, and no label value entered a request.
