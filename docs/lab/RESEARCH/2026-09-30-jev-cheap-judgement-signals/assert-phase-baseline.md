# Phase-boundary assert (landed baseline)

This pack assumes **`tools/driver/assert_phase.py`** and **`phase_assert.py`** remain the **phase kill line**. The white paper targets *additional* cheap judgements elsewhere; it does not redo this spike.

## Deterministic authority

`evaluate_assert()` in `tools/driver/phase_assert.py`:

- **Pass/fail is always** `deterministic_outcome_evidence(state)` — report `closed`, trailer/slug/phase alignment, Verification + Carried headings, substantive verification or outcome quoted in body.
- When Jev runs, its Score is logged; if Jev pass/fail **disagrees** with deterministic, `decision_source` stays **`deterministic`** and `jev.disagreed_with_deterministic` is set.
- Fail branch: `stop_and_escalate` (bot escalates even if report said `closed`).

Proposal rule carried forward: **if assert disagrees with a deterministic check available in the same state, drop reliance on Jev for that gate** (kill line from [`../../PROPOSALS/2026-09-30-jev-hook-assertion-spike.md`](../../PROPOSALS/2026-09-30-jev-hook-assertion-spike.md)).

## CLI modes (`assert_phase.py`)

| Mode | Behaviour |
|------|-----------|
| **`--deterministic`** | Jev not called. Prints result JSON; exit 0 pass / 2 fail. Used by eval verifier (`trailer-completeness`). |
| **`--dry-run`** | Prints Jev request JSON only. |
| **No flag, no `TYPESAFE_API_KEY`** | Same as dry-run (prints request, exit 0). |
| **`--live`** | POST TypeSafe (`jev-1.13.0`), append `.assert-log.jsonl`, pass/fail still from deterministic. |
| **`--fixture-jev`** | Offline merge of fixture response; logs disagreement without API. |

Compact `state` fields sent to Jev (`jev_state_slice`): slug, phase, design_outcome, closing headings/body, workflow_report, trailer — **not** full transcript.

## Implication for new judgements

- Phase complete **alignment sanity** (use case 4) should mirror this split: mechanical checks first; Jev Score/Choice for “dig deeper?” only when state is bounded and wrong steer is recoverable.
- In-session hooks (use case 1) have **no** git trailer yet — deterministic pre-gates are turn count, context estimate, tool-batch size; Jev is advisory signal for a human or supervisor.

## References

- `tools/driver/README.md` — bot loop step 3
- `docs/lab/FINDINGS.md` — assert vs classify distinction
- Fixtures: `tools/driver/fixtures/assert/`
