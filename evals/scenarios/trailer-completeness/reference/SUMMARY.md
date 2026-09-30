# Reference: trailer-completeness

A successful run of this scenario is trailer-complete and assert-clean.

Accepted `Workflow-Phase:` values, oldest commit first:

- `trailer-completeness:1`
- `trailer-completeness:2`
- `trailer-completeness:done`

`other-slug:1` may appear on the branch and must not close a phase. `tools/driver/status.py` then reports `open: done`, `done: true`, and `closed: ["trailer-completeness:1", "trailer-completeness:2"]`.

The phase-2 closing record in `assert_state.json` passes `assert_phase.py --deterministic` (Verification and Carried headings, report `closed`, trailer `trailer-completeness:2`). That check does not call classify.
