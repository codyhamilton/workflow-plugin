# GROWTH-DESIGN-NOTES — field fill for GROWTH state-selections (Soft HOLD)

**Soft Standard HOLD** — measured-corpus tooling only. No hooks, no Soft Standard unlock, no FP/miss product claims (`window_status` still unidentified). Nothing here needs `:8080`.

Follow-on to #107 (merged; not amended). Analysis seat (Sol catalog `bc-cca7ac7f`) may layer ranking on top; this note covers the implementation only.

## Problem

#107 added three GROWTH state-selections to the scenario sweep:

| state | field it projects |
|-------|-------------------|
| `markers_focus` | `markers` |
| `phase_hints_focus` | `phase_hints` |
| `recent_delta_brief` | `recent` |

No batch-002 snapshot builder ever emitted those keys. Across all 606 checkpoints in `snapshots/`, `snapshots-dense/` and `snapshots-mid/`, `markers`, `phase_hints` and `recent` are present **0** times. `project()` used `full.get(field) or {}` / `[]`, so the judge saw empty fields.

Consequences in the landed #107 results (`typesafe-scenario-sweep/results.jsonl`):

- 2,312 growth-state rows (1,328 `markers_focus`, 492 `phase_hints_focus`, 492 `recent_delta_brief`) judged empty fields. Their fire rates (0.0–0.07) are not evidence about those state shapes.
- `cell_id` did not encode state content, so a plain re-run would have skipped them as already done.

## What the snapshots do carry

| harness | checkpoints | `tail` | `cumulative.tool_histogram` | `delta_since_prior` |
|---------|-------------|--------|-----------------------------|---------------------|
| claude-code | 383 | yes (8 turns: `turn`, `excerpt`, `tool_names`) | yes | yes |
| opencode / codex / cursor | 223 | no (lite prefix, counters or role histogram only) | no | no |

## Fix

`growth_fill.py` derives the three fields deterministically, offline, from `tail` + `cumulative` + `delta_since_prior` only. No schedule, session-length or progress inputs, so nothing leaks beyond what `tail_focus` already shows.

- `markers`: counts over the tail window (`tail_turns`, `tool_turns`, `silent_tool_turns`, `text_only_turns`, `max_same_tool_run`), lexical term counts (`error_terms`, `verify_terms`, `delivery_terms`, `wait_terms`), plus `compaction_event_count`, `reread_path_count`, `delta_new_read_paths`.
- `phase_hints`: tool-class mix (explore / edit / exec / orchestrate / user / other) for the tail and cumulatively, dominant class for each, `tail_has_edit`, `closing_language`. Marked `heuristic, not a label`.
- `recent`: last 4 tail turns as `{turn, tools, text[:160]}`. `recent_delta_brief` still projects the last 2, as designed in #107.

A native field on a snapshot, if a future builder emits one, wins over the derived value.

### Eligibility gate

Lite-prefix packs have no `tail`, so nothing honest can be derived. `project()` raises `GrowthIneligible` and `build_cells()` skips the cell and counts it in `cells_plan.json` (`growth_cells_gated_no_tail`). Empty fields are never sent to the judge.

Effect at the sweep's representative (mid) checkpoint, 41 sessions (`GROWTH-FILL-COVERAGE.json`):

| | sessions |
|---|---|
| eligible (claude-code) | 16 |
| gated, no tail | 25 (opencode 20, codex 3, cursor 2) |

All 16 eligible sessions get non-empty `markers`, `phase_hints` and `recent`. **GROWTH scenarios are therefore 102 scenarios × 16 sessions, not × 41.** Do not report the growth block under the "× 41" headline. Planned at MAX=320: 10,570 cells total, 1,632 of them growth.

### Versioning and stale rows

- Growth cells now hash `growth-fill-v1` into `cell_id` and carry a `state_fill` field, so they are not deduped against the old empty-field rows.
- Old rows stay in `results.jsonl` (history, unmodified). `main()` excludes growth rows without `state_fill` from `meters.json` and records `stale_growth_rows_excluded`.
- Bump `FILL_VERSION` in `growth_fill.py` whenever the derivation changes; that re-runs growth cells only.

## How-to

```bash
cd docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002

# offline checks (no network, no key)
WF_REPO=$(git rev-parse --show-toplevel) python3 test_growth_fill.py   # derivation, gate, sweep wiring
python3 growth_fill.py                                                 # rewrites GROWTH-FILL-COVERAGE.json

# re-run growth cells only (needs TYPESAFE_API_KEY; old rows are not re-sent)
TYPESAFE_API_KEY=... python3 run_typesafe_scenario_corpus_sweep.py
```

`WF_REPO` overrides the hardcoded lab-machine repo path in the sweep runner and `run_batch002_flash_luna_scale.py`. Unset, behavior is unchanged.

## Limits

- Lexical and tool-class heuristics, not ground truth. They give the judge something concrete to read; they do not establish that these states are good predictors.
- Only claude-code sessions can exercise GROWTH states until opencode/codex/cursor builders emit a `tail`. That is the real fix for the coverage gap and is out of scope here.
- No new TypeSafe results are included. The refill needs a key and spend; the tooling above is ready for it.
- The `window_status` caveat from #106 still applies to any fire-rate interpretation.

## Sol analysis overlay: rank evidence-compatible pairs

Machine-readable ranking: [`GROWTH-RANKING.json`](GROWTH-RANKING.json).

### Reset the #107 result interpretation

All 2,312 pre-fill GROWTH rows are stale for state-shape analysis. Their
questions were judged with an empty `markers`, `phase_hints`, or `recent`
field. This includes the 41/41 fire result for
`state.markers_focus|q.silent_stall`: it is a wording response under an empty
state, not evidence that `markers_focus` works. Keep the rows for provenance,
but exclude them from ranking and refill meters as the implementation does.

The filled fields are also three representations of one evidence lineage:
`tail` plus thin `cumulative` / `delta_since_prior` data. A contrast among
them tests representation, not three independent signal sources.

The missing-state problem also predates GROWTH. The 25 tail-less/delta-less
non-Claude-Code sessions all fire for both `tail_focus|q.silent_stall` and
`delta_only|q.silent_stall`: **50 empty-state fires**, equal to 75.8% of all
`silent_stall` fires and 43.1% of all fires in the original 200×41 sweep.
`window_delta_tools` is all-null at all 41 representative snapshots because it
requests delta keys the snapshots do not emit. See the post-#108 caveat in
[`ANALYSIS.md`](../../2026-10-02-interception-steer-to-stop/ANALYSIS.md).
Eligibility gating is therefore required for old and new state shapes; an
empty container is not observed negative evidence.

### Eligibility intersects labels at nine pairs

Reusing the #106 join implementation on the 41 representative
`(session_id, checkpoint)` pairs gives:

| GROWTH-state-eligible claude-code pairs | Count | Later use |
|---|---:|---|
| `label_join_exact` | **9** | Labeled-ready, exact checkpoint only |
| `checkpoint_unlabeled` | 4 | Response distribution only |
| `session_unlabeled` | 3 | Response distribution only |
| **Eligible** | **16** | Non-empty GROWTH state |

The other 25 sessions remain state-ineligible because their lite snapshot has
no `tail`. Do not convert those 25 into empty-state cells, and do not copy a
nearby checkpoint label onto the four checkpoint-unlabeled pairs.

### Preferred pairings before the 102-scenario cartesian

The question must ask about evidence its selected state actually exposes.
Twelve pairings cover the twelve GROWTH questions once:

| Priority | state selection | question formats | Why this state |
|---|---|---|---|
| P0 | `markers_focus` | `dependency_wait`, `context_thrash_compact`, `idle_tool_spin` | Direct wait-term, compaction, silent-tool, and repeated-tool markers |
| P0 | `recent_delta_brief` | `brief_abandon`, `docs_only_drift`, `scope_creep_silent` | Only GROWTH state containing both the brief and recent records |
| P1 | `recent_delta_brief` | `edit_churn`, `bash_retry_storm`, `parallel_agent_thrash`, `speculative_rewrite`, `deliverable_orphan` | Recent tool/text evidence plus interval delta; limitations remain explicit in the ranking JSON |
| P1 | `markers_focus` | `test_flake_loop` | Tail-window verification/error counts and repetition marker |

`phase_hints_focus` is useful as a later representation contrast, but it is
not the best first state for any current question: it has coarse tool-class
mix and no brief, path identity, command outcome, or artifact result.

Run the twelve preferred pairs first: **108 exact-labeled-ready cells/driver**
(12×9), or 192 state-valid cells/driver when the seven not-exact pairs are
retained only for response-distribution diagnostics. Hold the other 90
GROWTH-state pairings until this pass reports non-empty state occupancy and
parse completeness by scenario. This is a spend/ranking rule, not a code
change to the #108 runner.

### Snapshot-builder boundary

The gate is the correct current behavior. A future harness-native fill should
add a prefix-only tail with the same minimum contract:

- ordered turn or event identifier;
- clipped, secret-redacted assistant excerpt;
- ordered tool names for that event;
- no final length, survival, progress fraction, result fire/rating, or outcome
  label.

Do not fabricate tail text from `api_turns`, role histograms, titles, or final
session metadata. Until a harness builder can emit that contract, keep its
GROWTH cells gated.

### What “more informative fire” means here

The objective is not a higher fire rate. It is a non-degenerate response tied
to evidence the state contains, with explicit defer counterevidence (and an
abstention path where a future response class supports it).
The #105 baseline (175/200 zero-fire, with 66/116 fires from
`q.silent_stall`) shows why wording-only fire is not enough. No ranking should
advance to an FP/miss claim until the exact-label gates are satisfied.
