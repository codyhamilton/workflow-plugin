# Unit report: 3-01 — Cursor plugin and hook scripts

**Status:** `done`

## What changed

- **Commit 1 (`4d41202`):** `git mv` of `skills/`, `hooks/`, `bin/`, MCP configs, and harness `plugin.json` files into `plugins/yakka/` (marketplace manifests stay at repo root).
- **Commit 2:** Marketplace `source` → `plugins/yakka`; `plugins/yakka/script/{spool.sh,prefetch-version.sh}`; Cursor hooks `./script/...`; Claude/Codex hooks → `script/spool.sh`; `packages/hooklog/spool.sh` drain kicks `plugins/yakka/bin/workflow`; `install.sh` copies `plugins/yakka` for Cursor; tests and design docs updated; plugin manifests `2.12.0`.

## Done evidence

**Before** (pre–commit 1, working tree at brief base + prior phase commit)

```
.cursor-plugin/marketplace.json workflow ./
.claude-plugin/marketplace.json workflow {github repo object}
test -f plugins/yakka/.cursor-plugin/plugin.json → fail (no such path)
rg 'CURSOR_PLUGIN_ROOT|tools/hooklog|^/' hooks/cursor.json → hits (CURSOR_PLUGIN_ROOT, packages/hooklog)
python3 -m unittest tools/driver/tests/test_install_route.py packages/hooklog/tests/test_surfaces.py → OK (25) against old layout
```

**After**

```
.cursor-plugin/marketplace.json workflow plugins/yakka
.claude-plugin/marketplace.json workflow plugins/yakka
test -f plugins/yakka/.cursor-plugin/plugin.json && test -d plugins/yakka/skills && test -f plugins/yakka/hooks/cursor.json && test ! -d packages/yakka → OK
rg 'CURSOR_PLUGIN_ROOT|tools/hooklog|^/' plugins/yakka/hooks/cursor.json → exit 1
sessionStart spool from cwd plugins/yakka → exit 0; evt envelope harness=cursor event=sessionStart
python3 -m unittest tools/driver/tests/test_install_route.py packages/hooklog/tests/test_surfaces.py → OK (25)
manifest versions 2.12.0; plugins/yakka/bin/VERSION 0.1.0
```

## Deviations

- `packages/hooklog/tests/test_surfaces.py`: skip `stub.calls` `--version` assertion for `cursor-hooks.example.json` only (example still documents `/ABS/PATH/.../bin/workflow` at repo root; owned paths exclude that file).
- `install.sh`: moved `is_valid_plugin_source` / `resolve_plugin_source` above `ensure_script_dir` so piped-install candidate checks can call them (required for opencode/cloud skill paths).

## Contradictions

- Contract cites `tools/cloud-env/bootstrap-workflow-skills.sh` installing from `plugins/yakka/skills`; that script is not in this brief's owned paths, so it was not edited here.

## Problems outside done evidence

None found.
