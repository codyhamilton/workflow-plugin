# Unit report: 6-05 — Transcript and jev-variants identifiers

**Status:** `done`

## What changed

- `tools/transcript/lib/jev_client.py`: `WORKFLOW_ALIGNMENT_*` constants → `YAKKA_ALIGNMENT_*`; TypeSafe question id `workflow_alignment` → `yakka_alignment` (no tests asserted the old id; stored classify logs that key the old name are historical only).
- `tools/jev-variants/case4/build4.py`: maintainer fixture `sys.path` install root `.../workflow-plugin/tools/driver` → `.../yakka/tools/driver`.
- Left `tools/jev-variants/case2/pair.py` corpus token `workflow-plugin` unchanged (external repo slug in research pair list; not a `WORKFLOW_` identifier).
- Left `workflow_report` in `build4.py` state fixture unchanged (driver `phase_assert` contract; `tools/driver/` out of scope).

## Done evidence

**Before** (`WORKFLOW_` in owned `.py` trees)

```
rg 'WORKFLOW_' tools/transcript tools/jev-variants
tools/transcript/lib/jev_client.py:35:WORKFLOW_ALIGNMENT_INSTRUCTIONS
tools/transcript/lib/jev_client.py:40:WORKFLOW_ALIGNMENT_CRITERIA
tools/transcript/lib/jev_client.py:68-69 (references)
```

**After**

```
rg --pcre2 'WORKFLOW_(?!QUALITY_)' tools/transcript tools/jev-variants -g '*.py'
→ no hits

python3 -m unittest discover -s tools/transcript/tests -p 'test_*.py' -v
→ Ran 11 tests in 0.034s — OK

python3 -m unittest discover -s tools/jev-variants/tests -p 'test_*.py' -v
→ Ran 43 tests in 0.021s — OK
```

## Deviations

None.

## Contradictions

None.

## Known problems

- Re-running `classify.py` against prior `.classify-log.jsonl` exports will show `yakka_alignment` instead of `workflow_alignment`; downstream lab docs still mention the old question id until a separate docs pass updates them (out of brief scope).
