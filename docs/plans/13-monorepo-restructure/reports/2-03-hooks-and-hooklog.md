# Unit report: 2-03 — Hook configs and hooklog package

**Status:** `done`

## What changed

- `hooks/hooks.json`, `hooks/codex.json`, `hooks/cursor.json`: spool commands now use `packages/hooklog/spool.sh` (Cursor shape unchanged aside from path segment).
- `packages/hooklog/{README.md,cursor-hooks.example.json}`: docs and example paths updated.
- `packages/hooklog/tests/{test_surfaces.py,test_write_surfaces.py,test_spool_queue.py}`: fixture paths, spool copy tree, opencode command string, and `go build` cwd (`packages/workflow`).

## Done evidence

**Before**

```
python3 -m unittest discover -s packages/hooklog/tests -v
→ Ran 35 tests in ~9.6s — FAILED (failures=3, errors=2)
  (surface tests: spool.sh missing at tools/hooklog; example path tools/hooklog/cursor-hooks.example.json)

rg 'tools/hooklog' hooks packages/hooklog
→ many hits across hooks/*.json and packages/hooklog/**
```

**After** (commit `f434a1b`)

```
python3 -m unittest discover -s packages/hooklog/tests -v
→ Ran 36 tests in ~61s — OK

rg 'tools/hooklog' hooks packages/hooklog
→ exit 1 (no matches)
```

## Deviations

- Updated `test_write_surfaces.py` `go build` cwd from `tools/workflow` to `packages/workflow` so write-surface integration tests align with 2-01; required for unittest OK and within owned `packages/hooklog/tests/`.

## Contradictions

None between this brief and cited DESIGN.md Phase 2 hook-config contract.

## Problems outside done evidence

- `test_write_surfaces` still expects Go at `$HOME/.local/go/bin/go` (pre-existing); local run used a symlink to `/usr/bin/go` when that path was absent.
