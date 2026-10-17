# 5-04 — npm runtime packages

## Status

**Complete.** Renamed both npm packages to yakka identifiers, updated runtime env defaults and analytics `localStorage` keys, and aligned analytics e2e/hosted setup with `packages/yakka` and `YAKKA_*` serve env.

## What was done

- `@codyhamilton/yakka-analytics`: package name, `localStorage` keys (`yakka-analytics-*`), e2e/hosted global setup (`go build` in `packages/yakka`, `YAKKA_CHECKS_DIR` → `packages/yakka/catalogue`, `YAKKA_SERVE_*`, `YAKKA_BIN` for hosted).
- `@codyhamilton/opencode-yakka-hooks`: package name, export `yakka-signals.json`, plugin export `YakkaSignalsPlugin`, `YAKKA_*` env reads, default queue under `~/.local/share/yakka/queue`, signal log `${XDG_STATE_HOME:-~/.local/state}/yakka/jev-signal-log.jsonl` via `YAKKA_JEV_SIGNAL_LOG`, README and `opencode.json.example` updated.

## Tests

```text
$ node --experimental-strip-types --test packages/opencode-yakka-hooks/tests/test_hooks.mjs
# 8 passed

$ python3 -m unittest packages/opencode-yakka-hooks/tests/test_batch.py
# Ran 6 tests — OK

$ grep -r 'WORKFLOW_' packages/yakka-analytics/src packages/opencode-yakka-hooks/src packages/opencode-yakka-hooks/python
# (no matches)

$ grep -r 'workflow-analytics-' packages/yakka-analytics/src
# (no matches)
```

Analytics Playwright e2e/hosted suites were **not** run (orchestrator may run at phase close).

## Departures

| Departure | Reason |
|-----------|--------|
| Node tests used `--experimental-strip-types` | Environment Node is v22.14.0; brief allows strip-types when required below v22.23.3+. |
| Default drain binary path is `plugins/yakka/bin/yakka` | Matches design; `5-03` adds that wrapper (still `workflow` on branch). |
| `test_hooks.mjs` passes `WORKFLOW_QUEUE` / `WORKFLOW_HOOKLOG_KICK` only when invoking `packages/hooklog/spool.sh` | Hooklog package still reads `WORKFLOW_*` until its rename unit runs; plugin runtime uses `YAKKA_*`. |
| `test_batch.py` still sets `WORKFLOW_SIGNAL_STATE_DIR` / `WORKFLOW_ANALYTICS_URL` for lab `post_tool_batch_signal` | Research proofs not in this brief’s owned paths. |
| `test_default_signal_log_path` asserts yakka paths directly | `tools/driver/jev_signal_log.py` still uses `WORKFLOW_*` (Phase 6); driver parity test removed. |
| Hosted spec keeps `workflow-analytics-placeholder` marker | Embedded site under `packages/yakka/internal/serve/site/` is explicitly out of scope. |

## Unfinished

None in this unit.

## Known problems

Until `5-03` lands, OpenCode’s default `YAKKA_BIN` kick target file may be missing unless `YAKKA_BIN` is set.
