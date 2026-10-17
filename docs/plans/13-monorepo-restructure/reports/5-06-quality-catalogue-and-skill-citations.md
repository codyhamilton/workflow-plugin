# Unit report: 5-06 — Quality catalogue path and skill citations

**Status:** `done with concerns`

## What changed (against brief)

- `tools/quality/quality.py`: `CATALOGUE` ROOT join `packages/workflow/catalogue` → `packages/yakka/catalogue` (only catalogue path literal in owned `tools/quality` modules).
- `plugins/yakka/skills/execute/SKILL.md`: execution-report rubric citation repointed to `packages/yakka/catalogue/checks/execution-report.json`.
- `plugins/yakka/skills/refine/templates/brief.md`: same rubric path in the Report line.
- No edits to `server.py`, `hookevents.py`, `interventions.py`, `thresholds.py`, or `executor_reports.py` (no `packages/workflow/catalogue` references there).

## Done evidence

**Grep (after):**

```
grep -r 'packages/workflow/catalogue' tools/quality plugins/yakka/skills/execute plugins/yakka/skills/refine
→ no hits
```

**Tests — brief command (before/after, unchanged behaviour):**

```
python3 -m unittest discover -s tools/quality -p 'test_*.py' -v
→ Ran 0 tests; exit 5 (NO TESTS RAN)
```

**Tests — same suite via `tools/quality/tests` (after changes):**

```
python3 -m unittest discover -s tools/quality/tests -p 'test_*.py' -v
→ Ran 26 tests in ~10.5s — OK
```

## Deviations

- Prescribed discover start dir `tools/quality` does not load `tools/quality/tests/` (0 tests); validation used `-s tools/quality/tests` instead. Not introduced by this unit; no owned-path fix per brief scope.

## Unfinished work

None for this unit.

## Known problems

- Done-evidence unittest invocation as written in the brief still reports NO TESTS RAN until discover start dir is fixed elsewhere.
