---
cursor:
  subagentId: "bc-0691b0b1-8c6c-5308-acb1-4e50c99868cf"
---

# Unit 1-04 — Hook kick and design 2

**Status:** done

## What changed

- `plugins/yakka/script/spool.sh`: `start_drain` uses `python3 "$root/client/yakka.py" drain` when `YAKKA_BIN` is unset; header kick comment updated.
- `packages/opencode-yakka-hooks/src/index.ts`: `spawnBin` routes unset `YAKKA_BIN` + `["drain"]` to `python3` on `plugins/yakka/client/yakka.py`; other unset args still use `bin/yakka` (keeps load-time `--version` prefetch). Comment on drain ingest path updated.
- `docs/design/02-edge-capture.md`: Drain section and **Changes from what exists** describe the Python plugin drain and Go `yakka serve` split behind `.drain.lock`.
- `plugins/yakka/script/test_kick.py`: new unittest coverage for kick paths and design-2 text.
- `packages/opencode-yakka-hooks/tests/test_hooks.mjs`: new unset-`YAKKA_BIN` drain spawn case.

## Checks (before → after)

**Before** (tests added, production unchanged):

```
python3 -m unittest discover -s plugins/yakka/script -p 'test_kick.py'
→ FAILED (failures=2): Design2 python drain string; UnsetBin no python3 log (still bash bin/yakka)

node --experimental-strip-types --test tests/test_hooks.mjs
→ fail 2 (new unset test empty py log; kick test flaky when ordered after unset — module lastKick)
```

**After:**

```
python3 -m unittest discover -s plugins/yakka/script -p 'test_kick.py' → OK (6 tests)
bash -n plugins/yakka/script/spool.sh → exit 0
node --experimental-strip-types --test tests/test_hooks.mjs → pass 9 / fail 0 (~10.6 s with cooldown sleep)
```

## Departures

- **10 s `sleep` before the unset-`YAKKA_BIN` mjs test:** `kickDrain` keeps a module-level 10 s cooldown; without waiting, an earlier kick test suppresses the drain spawn this case asserts. Sleep is only in that test, placed last in the file so existing kick assertions stay first.

## Contradictions

None between this brief and cited `DESIGN.md` contracts.

## Problems

None found outside done evidence.
