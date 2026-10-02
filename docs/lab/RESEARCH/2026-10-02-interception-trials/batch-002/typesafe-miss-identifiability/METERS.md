# METERS — TypeSafe miss-identifiability probe

**Soft Standard HOLD** — corpus and post-hoc analysis only; no behavior, hooks, unlock, or FP/miss scoreboard.

This probe repeats exact sidecar checkpoint keys with H2 risk questions and
flips `markers_focus` against `phase_hints_focus`. The sidecar is joined
after capture; no label value is sent to TypeSafe.

- exact label keys planned: **52**
- non-Maps holdout cells: **0** (0 sidecar-labeled keys; 0 without sidecar rows)
- planned cells: **387**
- successful cells: **387**
- HTTP counts: `{"200": 387}`
- HTTP success rate: **1.0**
- cell-id collisions: **0**
- overlap with prior result cell IDs: **0**
- leak spotcheck hits: **0**
- unique `runaway_like=yes` keys: **1**
- total positive label keys: **4** (gated for missing tail: **3**)
- positive keys with any fire: **1**

Harness mix: `{'claude-code': 312, 'cursor': 6, 'codex': 9, 'opencode': 60}`
Project mix: `{'open-pajero-maps': 294, 'open-pajero-maps (worktree ceiling-only)': 18, 'garcia-music': 15, 'lemmings': 27, 'workflow-plugin': 24, 'llama.cpp': 6, 'free-frontier': 3}`

| state × question | n | fire | fire rate | positive rows | fire on positive |
|---|---:|---:|---:|---:|---:|
| `markers_focus|late_miss_risk` | 52 | 8 | 0.1538 | 1 | 0 |
| `markers_focus|silent_stall` | 52 | 49 | 0.9423 | 1 | 1 |
| `markers_focus|activity_without_value` | 52 | 38 | 0.7308 | 1 | 1 |
| `phase_hints_focus|late_miss_risk` | 52 | 52 | 1.0 | 1 | 1 |
| `phase_hints_focus|silent_stall` | 52 | 41 | 0.7885 | 1 | 1 |
| `phase_hints_focus|activity_without_value` | 52 | 49 | 0.9423 | 1 | 1 |
| `stats_only|late_miss_risk` | 25 | 0 | 0.0 | 0 | 0 |
| `stats_only|silent_stall` | 25 | 5 | 0.2 | 0 | 0 |
| `stats_only|activity_without_value` | 25 | 0 | 0.0 | 0 | 0 |

`fire_on_runaway_positive_rows` is a descriptive coverage diagnostic.
It is not a miss rate: the corpus is sparse, labels are checkpoint-local,
and no validated decision window or negative control protocol exists.
