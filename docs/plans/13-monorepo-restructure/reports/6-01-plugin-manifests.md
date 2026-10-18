---
cursor:
  subagentId: "bc-1eefda5f-d5d0-5253-8e7e-36aa360c284a"
---

# Unit report: 6-01 — Plugin and marketplace manifests

**Status:** done

## What changed (against brief)

- `.cursor-plugin/marketplace.json` and `.claude-plugin/marketplace.json`: `name` → `yakka`; sole listed plugin `name` → `yakka`; `source` unchanged `plugins/yakka`.
- `plugins/yakka/.cursor-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`: `name` → `yakka`; `version` → `3.0.0`.
- Descriptions left as-is (they use “workflow” as the method noun, not the plugin identifier).

## Manifest assertion (owned five files)

**Before:**

```
AssertionError: .cursor-plugin/marketplace.json marketplace name
```

**After:**

```
PASS
```

## Tests

```
python3 -m unittest tools/release/test_layout.py
→ Ran 7 tests in 0.065s — OK
```

## Deviations

None.

## Unfinished work

None for this unit (CHANGELOG migration entry is Phase 7 per brief).

## Known problems

None for this unit’s contract.
