---
cursor:
  subagentId: "bc-0322fd8a-4871-56be-8244-b0aa3f955d93"
---

# Unit 3-03 — SessionStart prefetch removal

**Status:** done

## What changed

- `plugins/yakka/hooks/hooks.json`, `codex.json`: dropped SessionStart `nohup … bin/yakka --version`; spool-only.
- `plugins/yakka/hooks/cursor.json`: dropped `prefetch-version.sh` entry; `sessionStart` is spool only.
- Deleted `plugins/yakka/script/prefetch-version.sh`.
- `packages/hooklog/cursor-hooks.example.json`: removed second `sessionStart` `--version` command.
- `packages/hooklog/tests/test_surfaces.py`: `prefetch_seen == 0`; removed stub `--version` wait/assert; dropped unused `time` import.
- `packages/opencode-yakka-hooks/src/index.ts`: removed load-time `spawnBin(["--version"])`; drain kick unchanged.
- `packages/opencode-yakka-hooks/tests/test_hooks.mjs`: kick test no longer expects `--version` on load; renamed KICK=0 test.

## Checks (before → after)

**Before** (prefetch still wired; tests required it):

```
python3 -m unittest packages.hooklog.tests.test_surfaces → OK (4 tests)
node --experimental-strip-types --test tests/test_hooks.mjs → pass 9 / fail 0
```

After hook edits only (not committed), the same unittest would fail on `prefetch_seen == 1` for plugin hook files.

**After** (this commit):

```
python3 -m unittest packages.hooklog.tests.test_surfaces → OK (4 tests)
grep -r prefetch-version plugins/yakka packages/hooklog → only is_prefetch helper in test_surfaces.py (no hook commands; script deleted)
python3 -m json.tool plugins/yakka/hooks/cursor.json → sessionStart: one command, references spool.sh
node --experimental-strip-types --test tests/test_hooks.mjs → pass 9 / fail 0 (~10.7 s)
```

## Departures

- **Commit branch:** brief line 7 names `cursor/python-local-client`; orchestrator assigned `work/3-03` (committed there per assignment).

## Contradictions

- Brief commit branch vs orchestrator branch (above); resolved by following orchestrator.

## Unfinished work

None for this unit.

## Problems

None found outside done evidence.
