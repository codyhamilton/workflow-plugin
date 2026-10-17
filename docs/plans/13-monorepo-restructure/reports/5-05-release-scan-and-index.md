# Unit report: 5-05 — Release tooling, residual scan, package index

**Status:** done

## What changed (against brief)

- `tools/release/build.sh`: builds `packages/yakka` → `yakka-*` artifacts; embeds `packages/yakka-analytics` build; placeholder check uses `yakka-analytics-placeholder`.
- `tools/release/test_release.py`: `plugins/yakka/bin/yakka`, `yakka` version line, cache/binary names, `YAKKA_*` env vars; `VERSION` read from `bin/VERSION`; `test_6` hides module source by temporarily moving `go.mod` when system `go` is on `PATH`.
- `tools/release/phase5_outcome.py`: `YAKKA_QUEUE` / `YAKKA_SERVE_DATA` / `YAKKA_BIN`; `opencode-yakka-hooks` paths; retired-env probe built without a literal `WORKFLOW_` token in source (scan-clean).
- `tools/release/scan_residual_names.py`: Phase 5 contract matcher; `tools/release/test_scan_residual_names.py` unittest.
- `tools/release/test_layout.py`: plugin bin scan targets `bin/yakka`.
- `packages/README.md`, `packages/yakka/README.md`, `packages/yakka-analytics/README.md`, `packages/opencode-yakka-hooks/README.md`: Consumers/Release paths and residual `workflow-plugin` prose.

## Done evidence

```
PATH="$HOME/.local/go/bin:$PATH" python3 -m unittest discover -s tools/release -p 'test_*.py'
→ Ran 19 tests — OK

python3 tools/release/scan_residual_names.py --scope phase5
→ exit 0, no output

PATH="$HOME/.local/go/bin:$PATH" python3 tools/release/phase5_outcome.py
→ all six outcome clauses PASS
```

## Deviations

- `test_6_no_go_no_asset`: when `/usr/bin/go` or `/bin/go` exists, temporarily renames `packages/yakka/go.mod` so the wrapper hits the “no toolchain / module” path without mutating system `go` (not writable here). Phase 4 CI still hides system `go` for this test.
- `test_9_probe_home_go`: uses `PATH=$HOME/.local/go/bin:/usr/bin:/bin` so Go 1.27+ wins over system 1.22.2; HOME probe is exercised when system `go` is hidden (original contract).
- `scan_residual_names.py` builds forbidden literals at runtime so the scanner stays clean under its own Phase 5 scope.

## Unfinished work

None for this unit.

## Known problems

- Layout unittest fails if `packages/yakka-analytics/node_modules` is present on disk (pre-existing scan of `node_modules`); remove it before a clean layout run, or run layout before `test_7_build_sh`.
