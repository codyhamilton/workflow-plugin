# Unit report: 5-07 — Residual runtime names outside release

**Status:** done

## What changed (against brief)

- `packages/hooklog`: README, example JSON/TOML, `hooklog.py` comment, `test_surfaces.py` / `test_write_surfaces.py` path templates → `packages/opencode-yakka-hooks`, `plugins/yakka/bin/yakka`, `~/.config/yakka/client.toml`, `/ABS/PATH/yakka`, MCP key `yakka`.
- `packages/opencode-yakka-hooks/package.json` and `packages/yakka-analytics/package.json`: repository URL `https://github.com/codyhamilton/yakka.git`.
- `test_hooks.mjs`: spool env `YAKKA_QUEUE`, `YAKKA_HOOKLOG_KICK`. `test_batch.py`: removed unused `WORKFLOW_SIGNAL_STATE_DIR` / `WORKFLOW_ANALYTICS_URL` lines.
- `workflow-analytics-placeholder` → `yakka-analytics-placeholder` in `site.go`, `site/index.html`, `site_test.go`, `hosted.spec.ts`.
- `compact_test.go`: fixture `repo_id` → `github.com/codyhamilton/yakka`.
- `plugins/yakka/bin/RELEASE_URL` → `https://github.com/codyhamilton/yakka/releases/download`.

## Residual scan (owned paths, READMEs excluded, `secrets_test.go` excluded)

Patterns: Phase 5 contract in `briefs/5-05-release-scan-and-index.md` (same Python matcher as future `scan_residual_names.py`).

| | Count |
|---|------:|
| Before | 46 |
| After | 0 |

**After command:** Phase 5 matcher over `git ls-files` limited to `packages/hooklog`, `packages/yakka`, `packages/yakka-analytics`, `packages/opencode-yakka-hooks`, `plugins/yakka/bin`, skipping `*/README.md` and `packages/yakka/internal/secrets/secrets_test.go` → `hit_count=0` (same matcher used for before count on pre-change `HEAD`: 46).

## Tests

```
cd packages/yakka && PATH="$HOME/.local/go/bin:$PATH" go test ./internal/serve/ ./internal/compact/
→ ok serve (4.99s), ok compact (0.34s)

python3 -m unittest packages/opencode-yakka-hooks/tests/test_batch.py
→ Ran 6 tests — OK

python3 -m unittest discover -s packages/hooklog/tests -p 'test_*.py'
→ Ran 36 tests — OK
```

## Deviations

None.

## Unfinished work

- `tools/release/build.sh` placeholder marker: `5-05` (brief explicitly out of scope here).
- Package README residual names (`packages/yakka`, `packages/yakka-analytics`, `packages/opencode-yakka-hooks`): untouched per brief; `5-05` owns those files.

## Known problems

None for this unit’s contract.
