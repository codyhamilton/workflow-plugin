# Unit report: 6-06 — Phase 6 residual-name scan

**Status:** done with concerns

## What changed (against brief)

- `tools/release/scan_residual_names.py`: `PHASE6_PREFIXES`, `PHASE6_FILES`, `in_phase6_scope()`, `--scope phase6` in `files_for_scope` and argparse (phase5 unchanged).
- `tools/release/test_scan_residual_names.py`: `test_phase6_clean_in_repo` subprocess check.
- `tools/README.md`: quality catalogue path `packages/workflow` → `packages/yakka`.

## Done evidence

**Before (detached HEAD, no phase6 scope):**

```
$ python3 tools/release/scan_residual_names.py --scope phase6
usage: scan_residual_names.py [-h] [--scope {phase5,all}]
scan_residual_names.py: error: argument --scope: invalid choice: 'phase6' (choose from 'phase5', 'all')
→ exit 2
```

**After:**

```
$ python3 tools/release/scan_residual_names.py --scope phase5
→ exit 0, no output

$ python3 tools/release/scan_residual_names.py --scope phase6
tools/cloud-env/README.md:53:WORKFLOW_(?!QUALITY_)
tools/cloud-env/README.md:64:WORKFLOW_(?!QUALITY_)
tools/cloud-env/bootstrap-yakka-skills.sh:13:WORKFLOW_(?!QUALITY_)
tools/driver/README.md:14:WORKFLOW_(?!QUALITY_)
tools/driver/README.md:154:.cursor/(plugins/local|skills)/workflow
tools/driver/README.md:160:.cursor/(plugins/local|skills)/workflow
tools/driver/README.md:164:WORKFLOW_(?!QUALITY_)
tools/driver/README.md:196:\bworkflow-(plugin|analytics|tuning|lab|signals|quality-placeholder)\b
tools/driver/README.md:204:WORKFLOW_(?!QUALITY_)
tools/driver/report.py:13:WORKFLOW_(?!QUALITY_)
tools/driver/report.py:38:WORKFLOW_(?!QUALITY_)
tools/jev-variants/case2/pair.py:5:\bworkflow-(plugin|analytics|tuning|lab|signals|quality-placeholder)\b
→ exit 1

$ python3 -m unittest tools/release/test_scan_residual_names.py
→ Ran 3 tests — FAILED (test_phase6_clean_in_repo; phase5 and fixture tests pass)
```

Phase 6 outcome paths outside `tools/` (`plugins/yakka/skills/`, `.claude/skills/`, manifests, `install.sh`, `.gitignore`) report no hits under `--scope phase6`.

## Deviations

None from brief intent; scope wiring matches the brief’s prefix/file list. Could not meet “exit 0, no output” for phase6 because residual literals remain in `tools/` trees owned by prior units (`6-03`, `6-04`, `6-05`), which this unit may not edit.

## Unfinished work

Rename or rephrase legacy `workflow` / `WORKFLOW_` tokens in:

| File | Lines (pattern labels from scan) |
|------|----------------------------------|
| `tools/cloud-env/README.md` | 53, 64 |
| `tools/cloud-env/bootstrap-yakka-skills.sh` | 13 |
| `tools/driver/README.md` | 14, 154, 160, 164, 196, 204 |
| `tools/driver/report.py` | 13, 38 |
| `tools/jev-variants/case2/pair.py` | 5 |

Follow-up belongs in the owning phase-6 units (or a small remediation pass), not in scan exclusions.

## Known problems

- `test_phase6_clean_in_repo` fails until the files above are clean; phase6 scan wiring is otherwise in place.
- Phase 7 still owns full-repo `--scope all` after CHANGELOG rename entry (unchanged).
