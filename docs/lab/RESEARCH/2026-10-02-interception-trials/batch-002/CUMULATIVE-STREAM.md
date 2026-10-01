# CUMULATIVE — batch-002 Flash/Luna streaming
**Updated:** 2026-10-02 01:45:30 AEST
**Soft Standard HOLD.** Sibling owns TypeSafe bulk (~$10 open) — not expanded here.

| Capture | rows | scored |
|---|---:|---:|
| `wave0 root` | 240 | 240 |
| `flash-hframings (A)` | 240 | 240 |
| `luna-a (fail)` | 72 | 0 |
| `luna-b` | 180 | 180 |
| `flash-hframings-b` | 0 | 0 |
| `flash-scale` | 2400 | 200 |
| `luna-scale` | 960 | 60 |
| `flash-mid` | 0 | 0 |
| `luna-mid` | 0 | 0 |
| `luna-h25` | 72 | 72 |
| `luna-vol1` | 0 | 0 |
| `flash-hframings-vol1` | 0 | 0 |

**Flash/Luna cumulative rows (table):** 4164  
**Scored so far:** 992  
**In-flight planned (B+scale+mid targets):** ~5960 additional cells across streams  

## Live streams (this executor)
- B: `flash-hframings-b` 360 + `luna-b` **180 done**
- Scale: `flash-scale` 2400 + `luna-scale` 960 (dense 45…120/5; state-length + deterministic-trim; H1–H5 packs)
- Mid: `flash-mid` 1600 + `luna-mid` 640 (44 inventory sessions T≥30; schedule 30…120/5)

## Soft HOLD
- No hooks / Soft Standard unlock / product behaviour
- Flash+Luna policy-under-test only
- Soft yield Claude/Sol to l-fante
