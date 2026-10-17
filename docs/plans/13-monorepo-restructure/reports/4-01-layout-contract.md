# Unit report: 4-01 — Layout contract

**Status:** `done with concerns`

## What changed

- Added `tools/release/test_layout.py` (`scan_layout` + repo pass test + six fixture fail tests).
- Repointed `tools/release/test_release.py` to `plugins/yakka/bin/workflow` and `PLUGIN_ROOT` for `test_10`.
- Signal log default: `packages/opencode-workflow-hooks/python/batch_flush_cli.py` → XDG state path; `tools/driver/jev_signal_log.py` + tests; OpenCode README env table updated.
- Package README field blocks: `packages/{workflow,hooklog,workflow-analytics,opencode-workflow-hooks}/README.md`; new `tools/README.md` and `packages/README.md`.
- Docs: `docs/ARCHITECTURE.md` component map; `docs/design/05-distribution.md` Layout intro sentence.

## Check output

**Before** (`test_repo_passes_layout_check`, with `batch_flush_cli` still on `tools/driver`):

```
layout violations:
packages/opencode-workflow-hooks/python/batch_flush_cli.py: tools/
packages/hooklog/README.md: missing **Consumers**
packages/opencode-workflow-hooks/README.md: missing **Consumers**
packages/workflow: missing README.md
packages/workflow-analytics: missing README.md
```

**After**

```
python3 -m unittest tools/release/test_layout.py → OK (7)
python3 -m unittest packages/opencode-workflow-hooks/tests/test_batch.py tools/driver/tests/test_jev_signal_log.py → OK (9)
python3 -m unittest discover -s tools/release -p 'test_*.py' -v → lists all `test_layout` cases; `test_release` wrapper/build tests ERROR (no Go at ~/.local/go/bin/go in this environment; path repoint is in diff)
```

## Deviations

- Package `tools/` scan skips `**/internal/serve/site/**` so the committed analytics placeholder HTML (`tools/release/build.sh` prose) does not fail the check; that file is outside owned paths.
- Path resolution is duplicated in `batch_flush_cli.py` and `tools/driver/jev_signal_log.py` (brief owns both; importing OpenCode modules from driver would pull `docs/lab` proofs).

## Contradictions

- Phase 4 outcome wording mentions `tools/driver` “readers” of the signal log; Assumption 11 and this brief add a resolver only (no tail/append feature). Implemented resolver-only; no silent merge.

## Problems outside done evidence

- Root `README.md` still documents `tools/driver/.jev-signal-log.jsonl` (not owned; unchanged per brief).
