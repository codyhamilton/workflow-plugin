# 7-07 — CHANGELOG rows for identifiers 7-01 missed

Status: done.

## Done against the brief
Added six rows to the `### Environment variables` table in the `## 3.0.0` section of `CHANGELOG.md`, in alphabetical position:

| Was | Becomes |
|---|---|
| `WORKFLOW_ALIGNMENT_CRITERIA` | `YAKKA_ALIGNMENT_CRITERIA` |
| `WORKFLOW_ALIGNMENT_INSTRUCTIONS` | `YAKKA_ALIGNMENT_INSTRUCTIONS` |
| `WORKFLOW_ARTIFACT_SUBMIT_CLI` | removed (retired-pattern token; no `YAKKA_` successor) |
| `WORKFLOW_LEGACY` | `YAKKA_LEGACY` |
| `WORKFLOW_REPORT_FENCE` | `REPORT_FENCE` (no `YAKKA_` prefix; Python constant in `tools/driver/report.py`) |
| `WORKFLOW_SIGNAL_STATE_DIR` | removed (unused test assignments; no successor) |

Evidence: `python3 tools/release/scan_residual_names.py --scope all` exits 0. Commit SHA is in the final message.

## Departures
None.

## Unfinished work
None.

## Known problems
None.
