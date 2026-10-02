# TypeSafe GROWTH volume — Soft HOLD

**Status:** trial evidence and docs only. No hooks, Standard behavior,
product wiring, Pilot, or live behavior ship is authorized.

## Preferred #109 cut

The twelve ranked GROWTH scenarios were each evaluated against the 16
tail-valid representative sessions:

- **192 cells:** 108 exact label-joined cells (12 × 9) and 84 diagnostic-only
  cells (12 × 7).
- **12 distinct scenarios**, one representative checkpoint per session.
- **0 HTTP/API errors**, 192/192 raw response captures.
- The 25 sessions without a usable prefix tail remained gated and were not
  represented as empty GROWTH state.

Scenario pairs:

| State | Questions |
|---|---|
| `state.markers_focus` | `dependency_wait`, `context_thrash_compact`, `idle_tool_spin`, `test_flake_loop` |
| `state.recent_delta_brief` | `brief_abandon`, `docs_only_drift`, `scope_creep_silent`, `edit_churn`, `bash_retry_storm`, `parallel_agent_thrash`, `speculative_rewrite`, `deliverable_orphan` |

Meters: [`typesafe-growth-cut/meters.json`](typesafe-growth-cut/meters.json)  
Rows: [`typesafe-growth-cut/results.jsonl`](typesafe-growth-cut/results.jsonl)

## Distinct case catalog

The follow-on sweep uses 9 state selections × 42 question formats × 3 response
classes = **1,134 distinct cases**, with three representative corpus cells per
case:

- **3,402 cells**, balanced at 378 per state and 1,134 per response class.
- Response classes: `binary_fire`, `ternary_fire`, `likert_0_3`.
- Corpus coverage uses one mid representative per session, not transcript
  window slices.
- Growth states use only tail-valid sessions; unsupported tail-less cells are
  gated rather than filled.
- **0 HTTP/API errors**, 3,402/3,402 raw response captures.

Meters: [`typesafe-case-catalog-v3/meters.json`](typesafe-case-catalog-v3/meters.json)  
Rows: [`typesafe-case-catalog-v3/results.jsonl`](typesafe-case-catalog-v3/results.jsonl)

These results are descriptive volume evidence only. They do not establish
precision, recall, false positives, misses, or a behavior threshold.
