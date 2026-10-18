# Unit report: 6-04 — Install routes and cloud bootstrap

**Status:** done

## What changed (against brief)

- `git mv` `tools/cloud-env/bootstrap-workflow-skills.sh` → `bootstrap-yakka-skills.sh`; script uses `YAKKA_*` env vars, default repo `https://github.com/codyhamilton/yakka`, cache `~/.cache/yakka/src`.
- `install.sh`: default repo URL, `~/.cursor/plugins/local/yakka`, workspace skills name `yakka`, install cache `~/.cache/yakka/src`, all install env vars `WORKFLOW_*` → `YAKKA_*` (same suffixes).
- `.gitignore`: `.cursor/skills/yakka/`.
- `tools/cloud-env/README.md` and `environment.json.example`: new bootstrap filename, yakka URLs/paths.

## Checks

| Check | Before | After |
|-------|--------|-------|
| `bash -n install.sh` | exit 0 | exit 0 |
| `bash -n tools/cloud-env/bootstrap-yakka-skills.sh` | N/A (old name) | exit 0 |
| `test -f bootstrap-yakka-skills.sh && ! -f bootstrap-workflow-skills.sh` | fail | exit 0 |
| `rg '\.cursor/skills/workflow' install.sh .gitignore tools/cloud-env` | hits in all three | no hits (exit 1) |

**Pre-change unittest:** `python3 -m unittest tools/driver/tests/test_install_route.py` → 21 tests OK (brief expected a pre-change failure on path/env; this tree still matched legacy `WORKFLOW_*` / `workflow` paths).

**Post-change unittest:** FAILED — 9 failures, 1 error (e.g. `bootstrap-workflow-skills.sh: No such file`, skills under `.cursor/skills/workflow` missing). Expected until **6-03** updates `test_install_route.py`.

**`install.sh --print-route` (after):** `YAKKA_INSTALL_MODE=cloud YAKKA_WORKSPACE=<repo>` → `dest` `/…/.cursor/skills/yakka`, `reason` `YAKKA_INSTALL_MODE=cloud`. Equivalent skip-refresh probe: `YAKKA_INSTALL_SKIP_REFRESH=1` (with cloud routing env as needed). `WORKFLOW_INSTALL_LAB=1` still accepted and ignored (no install branches read it).

## Deviations

- Updated `tools/cloud-env/environment.json.example` (owned under `tools/cloud-env/**`) so README examples and `rg` stay consistent; brief change list named only README + bootstrap rename explicitly.

## Unfinished work

- **6-03:** repoint `tools/driver/tests/test_install_route.py` to `YAKKA_*`, `bootstrap-yakka-skills.sh`, and `.cursor/skills/yakka/`.

## Known problems

- Install-route driver suite red until 6-03; no driver edits in this unit per brief.
