# TypeSafe continuous volume wave 2 — Soft HOLD

**Generated:** 2026-10-02 12:51:37 AEST  
**Base:** master tip `06776c4` (post-#112 and #113)

This is a post-#112 replication/depth wave. It is measured corpus evidence
only: no hooks, `:8080`, Standard unlock, product wiring, or behavior ship.

## Landed volume

| Family | Cells | Replication shape | Fires |
|---|---:|---|---:|
| Preferred GROWTH cut | **576** | 12 ranked state×question pairs × 16 tail-valid sessions × early/mid/late checkpoints | 29 |
| Case catalog replication | **3,402** | 1,134 existing case IDs × three checkpoint replications | 135 |
| **Wave 2 total** | **3,978** | 41 corpus sessions; explicit checkpoint role in every row | **164** |

All **3,978/3,978** requests returned HTTP 200; no API/error rows were
recorded. Raw response captures are retained under the ignored `raw/`
directory. The resumable plan, rows, meters, and descriptive case statistics
are in [`typesafe-growth-wave2/`](typesafe-growth-wave2/).

## Replication meters

| Checkpoint role | Cells | Fires |
|---|---:|---:|
| `early` | 1,326 | 48 |
| `mid` | 1,326 | 45 |
| `late` | 1,326 | 71 |

The GROWTH family gates 25 tail-less sessions at each of three checkpoint
roles (**75 gated cells**); it does not substitute empty state. The catalog
family has 1,134 cases and 3,402 measured replications, with 378 cells per
state selection and 1,134 per response class.

## Descriptive observations

- The observed wave fire count is **164 / 3,978 (4.12%)**. This is a
  descriptive judge-output rate, not precision, recall, false-positive, miss,
  or policy-threshold evidence.
- The preferred GROWTH replication is **29 / 576 (5.03%)**; its
  `markers_focus` pairs account for 25 fires and its `recent_delta_brief`
  pairs account for 4.
- Across the catalog replication, `silent_stall` is the highest-fire question
  format at **37 / 81**, followed by `output_starvation` at **15 / 81**.
  This continues the prior wording/state sensitivity and should not be read
  as a validated outcome relationship.
- Late checkpoints have more observed fires than early or mid checkpoints in
  this wave (**71**, **48**, and **45** respectively). Checkpoint position is
  a replication axis here, not a ground-truth outcome label.

## Reproduction

The runner is [`run_typesafe_growth_volume.py`](run_typesafe_growth_volume.py).
It can resume the landed output with:

```sh
TS_RUN_STAGE=wave2 \
TS_CASE_OUT=typesafe-growth-wave2 \
python3 run_typesafe_growth_volume.py
```

The cell ID includes the wave, case/scenario, session, checkpoint role, and
checkpoint, so reruns skip completed rows without colliding with #112.
