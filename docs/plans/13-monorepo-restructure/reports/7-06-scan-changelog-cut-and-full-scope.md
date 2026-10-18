---
cursor:
  subagentId: "bc-3e0579a0-e82c-5ea8-ac5c-7c2f54ad19ff"
---

# Unit report: 7-06 — CHANGELOG scan cut and full-repo residual scan

**Status:** done

## What changed (against brief)

- `tools/release/scan_residual_names.py`: added `changelog_sections_to_skip()` (first `## … rename …` heading through EOF, `re.M`); wired into `scan_file` when `rename_changelog_cutoff()`; removed whole-file `CHANGELOG.md` skip from `globally_excluded`; line iteration now tracks byte offsets for design and changelog skip spans.
- `tools/release/test_scan_residual_names.py`: added `test_all_clean_in_repo` (`--scope all` subprocess).

## Done evidence

**Before (branch tip at unit start — whole-file CHANGELOG skip still active):**

```
$ python3 tools/release/scan_residual_names.py --scope phase5; echo exit:$?
→ exit:0, no output

$ python3 tools/release/scan_residual_names.py --scope phase6; echo exit:$?
→ exit:0, no output

$ python3 tools/release/scan_residual_names.py --scope all; echo exit:$?
→ exit:0, no output
```

(Brief’s intended pre-cut signal: once whole-file skip is removed without line-level cut, `--scope all` fails on `CHANGELOG.md` legacy tokens; observed during implementation before fixing `RENAME_CHANGELOG_HEADING` multiline.)

**After:**

```
$ python3 tools/release/scan_residual_names.py --scope phase5; echo exit:$?
→ exit:0, no output

$ python3 tools/release/scan_residual_names.py --scope phase6; echo exit:$?
→ exit:0, no output

$ python3 tools/release/scan_residual_names.py --scope all; echo exit:$?
→ exit:0, no output

$ python3 -m unittest tools/release/test_scan_residual_names.py
→ Ran 4 tests … OK
```

## Deviations

None.

## Contradictions

None between brief `5-05` contract, Phase 7 design outcome, and implementation.

## Unfinished work

None for this brief.

## Known problems

None.
