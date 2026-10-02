# TypeSafe response-class calibration wave (Soft HOLD)

## Scope

This wave complements the continuous TypeSafe/catalog volume runner from
[#112](https://github.com/codyhamilton/workflow-plugin/pull/112). The landed
runner exercised the catalog with `binary_fire`; this wave holds the
state-selection and question-format fixed and varies the response class.

The design is:

| axis | selection |
|---|---|
| state × question | the 12 preferred GROWTH pairings frozen by #109 |
| corpus | 9 exact representative `(session_id, checkpoint)` joins |
| response classes | `binary_fire`, `likert_0_3`, `four_class`, `rating_plus_offset` |
| planned cells | `12 × 9 × 4 = 432` |
| checkpoint | one representative mid checkpoint per session |
| framing | H1 only |

The nine joins are selected by exact checkpoint-key presence in the landed
outcome-label sidecar. No nearest-checkpoint interpolation is performed. The
label values are not copied into the state, questions, or API payload.

## Preferred state × question pairs

The pair list is the six P0 and six P1 pairings from the #109 ranking:

- `markers_focus`: `dependency_wait`, `context_thrash_compact`,
  `idle_tool_spin`, `test_flake_loop`
- `recent_delta_brief`: `brief_abandon`, `docs_only_drift`,
  `scope_creep_silent`, `edit_churn`, `bash_retry_storm`,
  `parallel_agent_thrash`, `speculative_rewrite`, `deliverable_orphan`

`phase_hints_focus` and the remaining GROWTH cartesian are intentionally held.
This wave does not claim new scenario coverage; it isolates response-class
distributions on evidence-compatible state/question pairs.

## Response-class mappings

- `binary_fire`: `fire`/`defer`; fire is `fire`.
- `likert_0_3`: urgency `0..3`; fire is rating `>=2`.
- `four_class`: `productive_continue`, `near_completion`,
  `likely_runaway`, `uncertain`; fire is `likely_runaway`.
- `rating_plus_offset`: urgency `0..3` plus a diagnostic offset in
  `{-15, 0, 15, 30}`; fire is rating `>=2`.

These are diagnostic mappings inherited from the batch-002 protocol. They do
not create a gold label or an FP/miss scoreboard.

## Execution and capture

```bash
WF_REPO="$PWD" python3 \
  docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/\
run_typesafe_response_calibration.py
```

The script is resumable. Request, response, error, and row captures are under
the ignored `typesafe-response-calibration/raw/` directory. It writes the
tracked `cells_plan.json` and, only after successful non-400 responses,
aggregate `meters.json` and `METERS.md`.

Missing credentials or HTTP 400 responses create `BLOCKER.md` and withhold
meters; no values are invented.

## HOLD

No hooks, `:8080`, Soft Standard unlock, or product behavior changes are part
of this wave. All results remain diagnostic and Soft HOLD.
