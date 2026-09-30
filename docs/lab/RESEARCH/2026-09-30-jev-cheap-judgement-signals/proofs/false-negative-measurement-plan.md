# False-negative / skip-rate measurement (closed)

Operational plan for weekly Grok Bot skim — **not** `classify.py`.

## Log locations (gitignored, outside plan folder)

| File | Env override | Contents |
|------|----------------|----------|
| `tools/driver/.jev-signal-log.jsonl` | `WORKFLOW_JEV_SIGNAL_LOG` | Hook/driver soft signals (`post_tool_batch`, `subagent_stop`, future `refine_complete`, `jev_shadow`) |
| `tools/driver/.assert-log.jsonl` | (assert CLI) | Phase `outcome-evidence` Jev rows |
| `tools/driver/.run-record.jsonl` | `DRIVER_RUN_RECORD` | Trigger cost/turns, dispatch |

**Invariant:** No `docs/plans/**` paths in log rows (same as run record).

## Row shapes to expect

**PostToolBatch (probe):** `kind`, `session_id`, `agent_id`, `api_turns_proxy`, `gate.{band_exit,handoff_signal,escalate,jev_eligible}`, `transcript_bytes`.

**Future Jev shadow:** add `jev.{question_id,score|choice,skipped_follow_up}` without blocking.

## Weekly Grok Bot skim (concrete)

1. `wc -l tools/driver/.jev-signal-log.jsonl` — volume trend.
2. `jq -s` aggregates (copy/paste recipe in `validated/weekly_skim_recipe.sh`):
   - **Skip rate (unit review):** `needs_review=skip` / all `unit-needs-review` rows once shadow lands.
   - **Escalate rate (session):** share of `post_tool_batch` rows with `gate.escalate=true` vs total worker sessions (unique `agent_id`).
   - **Unnoticed oversize:** join `agent_id` from logs to transcript stats (`tools/transcript/stats.py`) — flag workers with `api_turns>100` and **zero** `band_exit` rows before turn 100.
3. **False negatives (sampled):**
   - **Mechanical:** rows where `needs_review=skip` but later `assert_phase --deterministic` failed for same `slug:phase` (join on slug+phase within 7d).
   - **Human:** 5 random `skip` rows/week → `human_label` in `tools/transcript/.classify-log.jsonl` **not** used; instead append to `tools/driver/.jev-signal-audit.jsonl` with `{signal_row_id, verdict: should_have_reviewed|ok_skip}`.
4. **Disagreement:** `jq 'select(.jev.disagreed_with_deterministic==true)' tools/driver/.assert-log.jsonl` — must stay audit-only for phase kill line.

## Break-even check

From white paper: **~30%** skip rate on expensive follow-ups is economic floor. Report `(skips / (skips + spawns))` for `comprehensive-review` spawns tagged in run record when driver adds `review_spawn` field (future). Until then, use **manual spawn count** from FINDINGS table.

## Validated this pass

- Probe writes append-only JSONL: `run_proofs.sh` → `$TMPDIR/jev-signal-probe.jsonl` non-zero size.
- Unit test asserts `band_exit` at turn **76** via PostToolBatch counter.
