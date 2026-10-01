# GROWTH-WAVE — scenario catalog beyond 200×41 (Soft HOLD)

**Soft Standard HOLD** — measured corpus only; no hooks / product wiring / FP-miss board.

## Meters
- n_distinct_scenarios: **297** (prior landed #104: 200)
- n_sessions_swept: **41**
- n_cells incidental: **12169**
- errors: **0**
- growth state-scenarios (markers/phase_hints/recent_delta_brief × questions): **17**

## Exploratory fire (growth states only)
- `state.phase_hints_focus|q.bash_retry_storm` — fire_rate=0.0732 (n=41)
- `state.markers_focus|q.bash_retry_storm` — fire_rate=0.0244 (n=41)
- `state.markers_focus|q.docs_only_drift` — fire_rate=0.0244 (n=41)
- `state.markers_focus|q.edit_churn` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.brief_abandon` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.parallel_agent_thrash` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.test_flake_loop` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.dependency_wait` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.speculative_rewrite` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.context_thrash_compact` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.deliverable_orphan` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.scope_creep_silent` — fire_rate=0.0 (n=41)
- `state.markers_focus|q.idle_tool_spin` — fire_rate=0.0 (n=41)
- `state.phase_hints_focus|q.edit_churn` — fire_rate=0.0 (n=41)
- `state.phase_hints_focus|q.brief_abandon` — fire_rate=0.0 (n=41)

## HOLD
- Soft HOLD unchanged. No Soft Standard unlock.
- Join path: Sol seat `bc-7bfd7ac9` (do not duplicate Composer `bc-53492200`).

## Runway / follow-up
- First MAX=280 pass did **not** reach GROWTH adds (pre-growth list already ~296). Partial GROWTH cells (~17) came from an aborted growth-first probe.
- Script fix: insert GROWTH after NEW×NEW/NEW×FL (~168) before FL expansion; default MAX=320. Fill wave in flight on Ubuntu (`scenario-growth-320-fill`).
- `recent_delta_brief` was 0 in the 297 snapshot — expect coverage after 320 fill.
- Sol trial-design seat writing `GROWTH-DESIGN-NOTES.md` / `GROWTH-RANKING.json` (Codex Sol high; not Flash).
- Soft HOLD unchanged. Join analysis: do not duplicate — Sol `bc-7bfd7ac9`.
