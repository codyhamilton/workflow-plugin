# Compact Jev state schemas (closed)

**Pin:** `jev-1.13.0` · **Budget guard:** `jev_signal_schemas._size_guard` rejects state JSON **> 12k chars** (tests use **< 16k** request blob).

**Validated:** `python3 -m unittest test_proofs.py` dry-builds all four requests via `jev_signal_schemas.py`.

## Relationship to `jev_state_slice` / `assert_phase`

| Layer | Question id | Role |
|-------|-------------|------|
| `phase_assert.jev_state_slice` | `outcome-evidence` | **Kill line** mechanical pass/fail; Score ≥ 2.5 logged on `--live` |
| Cheap judgement #4 | `phase-alignment-sanity` | **Advisory** dig-deeper on deterministic **pass** only; never moves `decision_source` |
| #1–#3 | `session-progress`, `refine-brief-complexity`, `unit-needs-review` | No `evaluate_assert()`; driver/hook JSONL only |

## 1. PostToolBatch — progress / size (after gate)

**Type:** Score `progress_vs_scope` + Choice `handoff_recommended`

```json
{
  "question_id": "session-progress",
  "slug": "…",
  "phase": 3,
  "brief_id": "unit-3c-api",
  "api_turns": 88,
  "peak_ctx_tokens": 127000,
  "transcript_bytes": 4200000,
  "last_tool_batch": ["Read:path", "Grep:pat"],
  "design_outcome_line": "one line from DESIGN"
}
```

## 2. Post-refine — brief complexity

**Type:** Score `brief_complexity` (one request per brief)

```json
{
  "question_id": "refine-brief-complexity",
  "slug": "…",
  "phase": 3,
  "brief_id": "6c87c96bd9bb",
  "brief_title": "Refine Phase 3C",
  "brief_line_count": 240,
  "brief_excerpt": "first ~1–2k chars of brief markdown",
  "design_outcome": "phase outcome line"
}
```

## 3. Unit complete — needs review?

**Type:** Choice `needs_review` + Score `review_confidence`

```json
{
  "question_id": "unit-needs-review",
  "slug": "…",
  "phase": 2,
  "unit_id": "u2-auth",
  "closing_headings": ["Verification", "Carried"],
  "closing_body_excerpt": "verification paragraph only",
  "trailer": "slug:2",
  "verifier_exit_code": 0
}
```

Shape mirrors `jev_state_slice` headings/body/trailer but **unit-scoped** and smaller excerpts.

## 4. Phase complete — alignment sanity

**Type:** Score `alignment_sanity` only (separate from `outcome_evidence`)

```json
{
  "question_id": "phase-alignment-sanity",
  "slug": "…",
  "phase": 2,
  "design_outcome": "…",
  "closing_headings": ["Verification", "Carried"],
  "closing_body_excerpt": "…",
  "workflow_report": {"status": "closed", "phase": 2},
  "trailer": "slug:2"
}
```

**Dry-run:** `python3 -c "from jev_signal_schemas import BUILDERS, example_states; import json; print(json.dumps(BUILDERS['phase_alignment'](example_states()['phase_alignment']), indent=2))"` from `proofs/`.
