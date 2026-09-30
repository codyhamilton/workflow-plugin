# Phase driver

Deterministic phase closure for the workflow loop (`docs/plans/06-phase-driver/DESIGN.md`).

## Status (read-only)

```bash
python3 tools/driver/status.py docs/plans/06-phase-driver/
python3 tools/driver/status.py docs/plans/06-phase-driver/ --default-branch master
```

Stdout is JSON only. Resolution uses:

- `### Phase` headings in `DESIGN.md` (phase count)
- `Workflow-Phase: <slug>:<n>` and `Workflow-Phase: <slug>:done` trailers on commits in `git log <default>..HEAD`

Malformed or wrong-slug trailers are ignored. Does not read `IMPLEMENTATION.md`.

## Tests

```bash
python3 -m unittest discover -s tools/driver/tests -p 'test_*.py'
```
