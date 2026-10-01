# CASE-CATALOG — batch-002 scenarios (Soft HOLD)

**Generated:** 2026-10-02 01:50 AEST  
**Soft Standard HOLD** — no hooks / assert_phase product wiring / Soft Standard unlock.

## Progress metric (WSM / Cody)

**Primary unit = scenario** = `(state-selection case_id × question-format case_id)`.

Progress = **n_distinct_scenarios × n_sessions_swept**, with outcomes compared across the session corpus.

**Not** the main win: identical state×question × many transcript windows (`sched.fixed_15` vs `sched.dense_5`). Schedule/window densification is a **secondary sweep dimension** only.

Phase-gate / review-check are **separate scenario families** (different fed-state + question schemas).

Drivers: TypeSafe (bulk), Flash/Luna (competing approaches). Soft yield Claude/Sol → l-fante.

---

## Scenario families

### Family S — interception policy scenarios (Jev/Flash/Luna)

`scenario_id = state.<sel> × q.<fmt>`  
Optional thin framing (H1/H3/H5) is a **probe variant**, not a new scenario family.  
Response-class (`binary_fire`, `ternary_fire`, …) is an **output-format variant**; default volume uses `binary_fire`.

### Family P — phase-gate scenarios

`pg.outcome_evidence`, `pg.phase_alignment` (+ compact phase-state variants). Soft HOLD only.

### Family R — review-check scenarios

`rv.unit_needs_review`, `rv.refine_brief`, `rv.session_progress` (+ compact unit/brief/progress variants). Soft HOLD only.

---

## State-selection case ids

### Base (multidriver)
| case_id | what it selects |
|---------|-----------------|
| `state.stats_only` | Cumulative counters only |
| `state.stats_plus_delta` | Cumulative + delta |
| `state.hybrid_v0` | Brief + cum + delta + short tail |
| `state.compact_focus` | Compaction/reread/tool-hist focus subset |

### Flash/Luna scale (canonical — PR #102; do not reinvent)
| case_id | what it selects |
|---------|-----------------|
| `state.state_length_short` | Minimal counters |
| `state.state_length_mid` | Mid-length cum + small delta |
| `state.deterministic_trim_v1` | Brief≤120 + cum + tail[-2] |
| `state.deterministic_trim_v2` | Counters + delta only (no prose) |

### TypeSafe trim recipes (char-budget selections; still state-selection)
| case_id | what it selects |
|---------|-----------------|
| `trim.full` / `trim.trim_mid` / `trim.trim_tight` / `trim.stats_only` | Budgeted views of hybrid-ish state |

### NEW state-selections (TypeSafe scenario sweep priority)
| case_id | what it selects |
|---------|-----------------|
| `state.delta_only` | Interval delta only |
| `state.tail_focus` | Tail narrative only |
| `state.tool_hist_focus` | Tool-churn lens |
| `state.brief_cum_no_tail` | Brief + cum, no tail |
| `state.chars_budget_1200` | Extreme 1200-char budget |
| `state.window_delta_tools` | Local window tool/char delta |

---

## Question-format case ids

### Base multidriver
`q.steer_now`, `q.continue_excessively`, `q.productive_arc`, `q.near_done`, `q.thrash_bundle`, `q.defer_recheck`, `q.horizon_exceeded`, `q.plateau_sustained`, `q.boundary_overrun`, `q.waste_intervene`

### Flash/Luna EXTRA (canonical)
`q.recheck_interval`, `q.closing_protect`, `q.scope_drift`, `q.activity_without_value`, `q.tail_risk`, `q.recoverable_stall`


### GROWTH state-selections (wave beyond 200×41)
| case_id | what it selects |
|---------|-----------------|
| `state.markers_focus` | Markers + thin counters |
| `state.phase_hints_focus` | Phase hints + thin cum |
| `state.recent_delta_brief` | Brief + delta + recent[-2] |

### GROWTH questions (wave beyond 200×41)
`q.edit_churn`, `q.bash_retry_storm`, `q.brief_abandon`, `q.parallel_agent_thrash`, `q.test_flake_loop`, `q.docs_only_drift`, `q.dependency_wait`, `q.speculative_rewrite`, `q.context_thrash_compact`, `q.deliverable_orphan`, `q.scope_creep_silent`, `q.idle_tool_spin`

### NEW TypeSafe (≥20) — priority with NEW states
`q.compaction_storm`, `q.reread_loop`, `q.silent_stall`, `q.tool_error_cascade`, `q.context_pressure`, `q.validation_loop`, `q.plan_execute_drift`, `q.handoff_ready`, `q.abort_cheaper`, `q.duplicate_work`, `q.over_polish`, `q.under_verified`, `q.mid_arc_healthy`, `q.early_false_alarm`, `q.late_miss_risk`, `q.recovery_possible`, `q.stop_preserves_value`, `q.continue_learns`, `q.thrash_vs_explore`, `q.user_wait_signal`, `q.resource_asymmetry`, `q.output_starvation`

---

## Secondary dimensions (not scenarios)

| dimension | examples | role |
|-----------|----------|------|
| schedule/window | `sched.fixed_15`, `sched.dense_5` | Secondary evidence only |
| framing probe | H1–H5 | Optional thin probe (default H1 for volume) |
| response-class | binary / likert / ternary / … | Output-format variant |

---

## Sweep policy (scenario-first)

1. Enumerate **distinct scenarios** = cartesian of priority state-selections × question-formats (esp. NEW×NEW, then NEW×FL-extra, then FL-state×NEW-q).
2. For each scenario, round-robin **sessions** (all packs). Use **one representative checkpoint per session** (prefer mid reached cp) — do **not** explode all windows for the same scenario.
3. Meters: `n_distinct_scenarios`, `n_sessions_swept`, `outcomes_by_scenario` (fire rates across sessions). `n_cells` is incidental (= scenarios × sessions × optional thin probes).
4. Soft HOLD throughout.

Runner: `run_typesafe_scenario_corpus_sweep.py` → `typesafe-scenario-sweep/`  
Review family top-up: `run_typesafe_review_topup.py` → `typesafe-review-check/` (separate family R).
