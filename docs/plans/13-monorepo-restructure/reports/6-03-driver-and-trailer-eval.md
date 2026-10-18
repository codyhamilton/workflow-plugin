# Unit report: 6-03 — Driver dual-read and trailer-completeness eval

**Status:** done with concerns

## What changed (against brief)

- Added `tools/driver/trailer_keys.py` with shared `PHASE_TRAILER_KEYS`, `PLAN_TRAILER_KEYS`, and `REPORT_FENCE_TAGS`.
- `resolve.py` `git_trailer_lines` merges values from every phase trailer key; dual-key unittest (`Workflow-Phase: t:1` then `Yakka-Phase: t:2` → open phase 3).
- `report.py` accepts `workflow-report` and `yakka-report` fences; unittest covers `yakka-report`.
- `jev_signal_log.py`: `YAKKA_JEV_SIGNAL_LOG`, default `~/.local/state/yakka/jev-signal-log.jsonl`.
- `check_skills.py`: `YAKKA_*` install env names, `WORKSPACE_SKILLS_NAME` default `yakka`, `MAINTAINER_SKILLS` includes `yakka-tuning`.
- `trigger.py` skip message names both phase trailer keys.
- `evals/scenarios/trailer-completeness/verify.py` runs checks 1–4 per key; `source.md` names both keys.
- Driver tests repointed to `YAKKA_*`, `bootstrap-yakka-skills.sh`, `.cursor/skills/yakka/`, `plugins/local/yakka`.

## Checks

| Check | Before | After |
|-------|--------|-------|
| `python3 -m unittest tools/driver/tests/test_jev_signal_log.py` | OK; default `…/state/workflow/jev-signal-log.jsonl` | OK; default `…/state/yakka/jev-signal-log.jsonl` |
| `python3 evals/scenarios/trailer-completeness/verify.py` | exit 0; `Workflow-Phase` only | exit 0; `trailer_keys_exercised`: `Workflow-Phase`, `Yakka-Phase` |
| `python3 -m unittest discover -s tools/driver/tests -p 'test_*.py'` | (not run pre-change in this session) | 74 tests OK (2 skipped) |
| `parse_workflow_report` on both fences | N/A | `workflow-report` phase 1, `yakka-report` phase 2 |

**Skipped tests:** `test_cursor_setup_*` in `test_install_route.py` — `docs/lab/bootstrap/cursor-cloud-setup.sh` still execs removed `bootstrap-workflow-skills.sh` (outside this brief’s owned paths).

## Deviations

- Install-route tests skip thin `cursor-cloud-setup.sh` wrapper checks until that script is repointed (not owned by 6-03).
- `test_outcome_scenario.py` compares baseline fields except `once.skip_reason` wording (expanded for dual-read).

## Unfinished work

- Repoint `docs/lab/bootstrap/cursor-cloud-setup.sh` to `bootstrap-yakka-skills.sh` and un-skip the two install-route tests.

## Known problems

- None blocking driver dual-read or trailer-completeness eval.
