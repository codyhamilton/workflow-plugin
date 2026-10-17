# Unit report: 1-01 — Lab collapse

**Status:** `done`

## What changed

- Moved six maintainer skills with `git mv` from `plugins/workflow-lab/skills/` to `.claude/skills/` (`iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, `workflow-tuning`). Deleted `lab-proposal` and removed the entire `plugins/` tree.
- Marketplaces (`.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`) list only `workflow`. Plugin manifests bumped `2.9.2` → `2.10.0` (Claude, Cursor, Codex); `bin/VERSION` unchanged.
- `install.sh` and `tools/cloud-env/bootstrap-workflow-skills.sh` install core skills only; removed lab copy/symlink paths. `WORKFLOW_INSTALL_LAB=1` is a no-op (still accepted).
- `tools/driver/check_skills.py`: `LAB_SKILLS` → `MAINTAINER_SKILLS` (six names). Tests set `WORKFLOW_INSTALL_LAB=1` and assert maintainer skills are not installed; added interactive Cursor test that `workflow-lab` local plugin is not created.
- Docs/README/CHANGELOG/lab live files updated for one plugin plus maintainer skills at `.claude/skills/`.

## Done evidence

**Before**

```
['workflow', 'workflow-lab']
plugins/workflow-lab exists
True   # LAB_SKILLS in check_skills.py
```

**After**

```
plugins absent OK
marketplace plugins: ['workflow'] only
python3 tools/transcript/find.py --help → exit 0
LAB_SKILLS in check_skills.py → False
plugin manifests 2.10.0; bin/VERSION 0.1.0
python3 -m unittest tools/driver/tests/test_check_skills.py tools/driver/tests/test_install_route.py → 32 tests OK
live-file git grep (brief exclusions) → no output
CHANGELOG 2.10.0 section → no forbidden strings
git diff shows six skill dirs as renames (R); lab-proposal deleted
```

## Deviations

None.

## Contradictions

None between this brief and cited DESIGN.md Phase 1 contracts.

## Problems outside done evidence

None observed.
