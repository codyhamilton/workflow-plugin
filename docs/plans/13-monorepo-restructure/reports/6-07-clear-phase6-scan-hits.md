---
cursor:
  subagentId: "bc-b93bed63-1cbf-53bb-ab8d-909844962f94"
---

# Unit report: 6-07 — Clear phase 6 residual scan hits

**Status:** done

## What changed (against brief)

- `tools/cloud-env/README.md`, `tools/cloud-env/bootstrap-yakka-skills.sh`: dropped legacy install-lab env identifier; core-only / no maintainer skills unchanged.
- `tools/driver/README.md`: `YAKKA_INSTALL_*` examples, `.cursor/skills/yakka` paths, CI kill line uses “yakka” not the old plugin slug.
- `tools/driver/report.py`: `WORKFLOW_REPORT_FENCE` → `REPORT_FENCE`; `parse_workflow_report` and dual fence tags unchanged.
- `tools/jev-variants/case2/pair.py`: corpus slug `yakka`.
- `docs/lab/bootstrap/cursor-cloud-setup.sh`: exec `bootstrap-yakka-skills.sh`; comments use `YAKKA_WORKSPACE`.
- `tools/driver/tests/test_install_route.py`: removed the two `test_cursor_setup_*` skip guards.

## Done evidence

**Before:**

```
$ python3 tools/release/scan_residual_names.py --scope phase6
tools/cloud-env/README.md:53:WORKFLOW_(?!QUALITY_)
… (12 hits total; see 6-06 report)
→ exit 1
```

**After:**

```
$ python3 tools/release/scan_residual_names.py --scope phase6
→ exit 0, no output

$ python3 tools/release/scan_residual_names.py --scope phase5
→ exit 0, no output

$ python3 -m unittest tools/release/test_scan_residual_names.py
→ Ran 3 tests — OK

$ python3 -m unittest tools/driver/tests/test_install_route.py
→ Ran 21 tests — OK (including test_cursor_setup_uses_local_installer_core_only and test_cursor_setup_delegates_to_cloud_bootstrap; not skipped)
```

## Deviations

None.

## Unfinished work

None for this brief.

## Known problems

None.
