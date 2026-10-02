# TypeSafe Soft HOLD analysis — diagnostic and miss-identifiability axes

**Evidence only.** No behavior, hooks, Standard unlock, or local `:8080` llama path.

## Comparison against #110

| corpus | scenarios / keys | cells | successful | fires | interpretation |
|---|---:|---:|---:|---:|---|
| #110 preferred TypeSafe (`44764b9`) | 12 pairs × 16 sessions | 192 | 192 | 10 | prior preferred scenario distribution |
| diagnostic state flip | 24 state×question scenarios × 7 reps × 2 classes | 336 | 336 | 67 | non-label-ready representation contrast |
| miss-identifiability + holdout | 52 exact keys + 25 non-Maps keys | 387 | 387 | 242 | post-hoc risk probe; no scoreboard |

#110 preferred fire distribution: **10/192 (0.0521)**. The denominators and representative populations differ, so this is not a treatment comparison.

## 12×7 diagnostic extension

- **336/336** HTTP-200 cells
- state flip: `markers_focus` vs `phase_hints_focus`
- response classes: `binary_fire` and `four_class`
- leak hits: **0**; cell collisions: **0**

| state × response class | n | fires | rate |
|---|---:|---:|---:|
| `markers_focus|dependency_wait|four_class` | 7 | 0 | 0.0 |
| `markers_focus|dependency_wait|binary_fire` | 7 | 0 | 0.0 |
| `markers_focus|context_thrash_compact|four_class` | 7 | 0 | 0.0 |
| `markers_focus|context_thrash_compact|binary_fire` | 7 | 0 | 0.0 |
| `markers_focus|idle_tool_spin|binary_fire` | 7 | 5 | 0.7143 |
| `markers_focus|idle_tool_spin|four_class` | 7 | 5 | 0.7143 |
| `markers_focus|brief_abandon|binary_fire` | 7 | 0 | 0.0 |
| `markers_focus|brief_abandon|four_class` | 7 | 0 | 0.0 |
| `markers_focus|docs_only_drift|binary_fire` | 7 | 2 | 0.2857 |
| `markers_focus|docs_only_drift|four_class` | 7 | 0 | 0.0 |
| `markers_focus|scope_creep_silent|binary_fire` | 7 | 0 | 0.0 |
| `markers_focus|scope_creep_silent|four_class` | 7 | 0 | 0.0 |
| `markers_focus|edit_churn|binary_fire` | 7 | 2 | 0.2857 |
| `markers_focus|edit_churn|four_class` | 7 | 2 | 0.2857 |
| `markers_focus|bash_retry_storm|binary_fire` | 7 | 0 | 0.0 |
| `markers_focus|bash_retry_storm|four_class` | 7 | 1 | 0.1429 |
| `markers_focus|parallel_agent_thrash|binary_fire` | 7 | 4 | 0.5714 |
| `markers_focus|parallel_agent_thrash|four_class` | 7 | 7 | 1.0 |
| `markers_focus|test_flake_loop|binary_fire` | 7 | 0 | 0.0 |
| `markers_focus|test_flake_loop|four_class` | 7 | 3 | 0.4286 |
| `markers_focus|speculative_rewrite|binary_fire` | 7 | 0 | 0.0 |
| `markers_focus|speculative_rewrite|four_class` | 7 | 0 | 0.0 |
| `markers_focus|deliverable_orphan|binary_fire` | 7 | 0 | 0.0 |
| `markers_focus|deliverable_orphan|four_class` | 7 | 0 | 0.0 |
| `phase_hints_focus|dependency_wait|four_class` | 7 | 0 | 0.0 |
| `phase_hints_focus|dependency_wait|binary_fire` | 7 | 0 | 0.0 |
| `phase_hints_focus|context_thrash_compact|binary_fire` | 7 | 0 | 0.0 |
| `phase_hints_focus|context_thrash_compact|four_class` | 7 | 1 | 0.1429 |
| `phase_hints_focus|idle_tool_spin|binary_fire` | 7 | 2 | 0.2857 |
| `phase_hints_focus|idle_tool_spin|four_class` | 7 | 3 | 0.4286 |
| `phase_hints_focus|brief_abandon|binary_fire` | 7 | 2 | 0.2857 |
| `phase_hints_focus|brief_abandon|four_class` | 7 | 0 | 0.0 |
| `phase_hints_focus|docs_only_drift|binary_fire` | 7 | 0 | 0.0 |
| `phase_hints_focus|docs_only_drift|four_class` | 7 | 0 | 0.0 |
| `phase_hints_focus|scope_creep_silent|four_class` | 7 | 1 | 0.1429 |
| `phase_hints_focus|scope_creep_silent|binary_fire` | 7 | 0 | 0.0 |
| `phase_hints_focus|edit_churn|four_class` | 7 | 1 | 0.1429 |
| `phase_hints_focus|edit_churn|binary_fire` | 7 | 0 | 0.0 |
| `phase_hints_focus|bash_retry_storm|binary_fire` | 7 | 5 | 0.7143 |
| `phase_hints_focus|bash_retry_storm|four_class` | 7 | 3 | 0.4286 |
| `phase_hints_focus|parallel_agent_thrash|binary_fire` | 7 | 4 | 0.5714 |
| `phase_hints_focus|parallel_agent_thrash|four_class` | 7 | 3 | 0.4286 |
| `phase_hints_focus|test_flake_loop|binary_fire` | 7 | 5 | 0.7143 |
| `phase_hints_focus|test_flake_loop|four_class` | 7 | 4 | 0.5714 |
| `phase_hints_focus|speculative_rewrite|binary_fire` | 7 | 0 | 0.0 |
| `phase_hints_focus|speculative_rewrite|four_class` | 7 | 0 | 0.0 |
| `phase_hints_focus|deliverable_orphan|binary_fire` | 7 | 0 | 0.0 |
| `phase_hints_focus|deliverable_orphan|four_class` | 7 | 2 | 0.2857 |

The four classes are diagnostic output formats. The seven representatives remain
non-label-ready, so these rates are not joins to gold outcomes.

## Miss-identifiability probe

- **387/387** HTTP-200 cells
- exact sidecar keys with usable tail: **52**
- non-Maps holdout: **75 cells / 25 keys** (4 sidecar-labeled; 21 without sidecar rows)
- sidecar `runaway_like=yes` keys: **4 total**, **1 state-valid**, **3 gated for missing tail**
- HTTP success: **1.0**; leak hits: **0**; collisions: **0**; prior-ID overlap: **0**

| state × question | n | fires | rate |
|---|---:|---:|---:|
| `markers_focus|late_miss_risk` | 52 | 8 | 0.1538 |
| `markers_focus|silent_stall` | 52 | 49 | 0.9423 |
| `markers_focus|activity_without_value` | 52 | 38 | 0.7308 |
| `phase_hints_focus|late_miss_risk` | 52 | 52 | 1.0 |
| `phase_hints_focus|silent_stall` | 52 | 41 | 0.7885 |
| `phase_hints_focus|activity_without_value` | 52 | 49 | 0.9423 |
| `stats_only|late_miss_risk` | 25 | 0 | 0.0 |
| `stats_only|silent_stall` | 25 | 5 | 0.2 |
| `stats_only|activity_without_value` | 25 | 0 | 0.0 |

The probe found a state-valid positive key and produced descriptive fire coverage
on it, but that is not a miss rate: three other positive label keys are not
state-eligible, and there is no validated decision window or negative-control set.
The non-Maps rows are a holdout population; sidecar overlap is not treated as a
false-positive label or a miss score.

## Remaining open

- Add tail-bearing labeled positive prefixes for the three currently gated keys.
- Establish a labeled non-Maps holdout and a pre-specified decision-window protocol.
- Keep H2 nulls/never-fire baselines and markers-vs-phase-hints as exploratory axes.
- Keep all future meters descriptive until those joins are independently validated.
