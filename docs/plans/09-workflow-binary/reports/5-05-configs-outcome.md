# 5-05 Harness configs, MCP registration and phase 5 outcome (exec 31)

Status: done with concerns (3 of 7 outcome clauses cannot pass on this host right now; environmental).

## Done
- `hooks/hooks.json`: `--harness auto` -> `--harness claude`; `artifact_submit.py` removed; second SessionStart prefetch (timeout 5). Worktree events stay `[]`.
- `hooks/cursor.json`, `cursor-hooks.example.json`: `artifact_submit.py` removed; sessionStart prefetch (5).
- `codex-hooks.example.json`: `artifact_submit` removed; all timeouts <= 3; SessionStart prefetch (3).
- `.mcp.json`: stdio `workflow` -> `${CLAUDE_PLUGIN_ROOT}/bin/workflow mcp`. New `cursor-mcp.example.json`, `codex-mcp.example.toml`.
- README rewritten (queue, `bin/workflow drain`, `workflow init`, MCP, `serve.secrets.env`).
- `test_surfaces.py` rewritten (queue files, stub `WORKFLOW_BIN` prefetch); `test_artifact_submit_surfaces.py` removed; `test_write_surfaces.py` and `tools/release/phase5_outcome.py` added.

## Fail first
Before the config edits, `write-replay` failed for the Claude fixtures (`--harness auto` spools nothing) and `no-retired-refs` listed hits in hooks.json, README and the examples.

## Outcome output (last run)
```
outcome version-clean-build FAIL
outcome concurrent-first-runs FAIL
outcome release-build FAIL
outcome init PASS
outcome write-replay PASS
outcome no-retired-refs PASS
outcome retired-files-gone PASS
```
The three FAILs are `go build ... write /tmp/go-build*/importcfg.link: disk quota exceeded`. /tmp is a tmpfs with a per-user quota that is nearly full from other data. 5-02's `test_release.py` drops TMPDIR, so it cannot be redirected from outside. Rerun `python3 tools/release/phase5_outcome.py` when /tmp has headroom (earlier runs showed init/write-replay failing only for the same reason, and they pass with TMPDIR on /home).

## Other checks
- `unittest discover -s tools/hooklog/tests`: 34 tests OK.
- `go test -count=1 ./...` (tools/workflow): ok. OpenCode `test_hooks.mjs`: 6 pass, 0 fail. JSON/TOML parse: ok. No leftover test processes.

## Departures and problems
- Codex configs pass no `--event`, so the envelope event is empty; the test accepts the payload `hook_event_name`.
- OpenCode fixtures replay through `spool.sh --harness opencode` (not the plugin), as 5-04 proved equivalent.
- 5-02 defect (not fixed): `test_release.py goenv()` runs `go env` without an explicit HOME, so under a temp HOME GOMODCACHE points at the temp dir and modules are downloaded.
- Under a temp HOME, `~` breaks; the tests resolve the real home via `pwd` and symlink `.local/go`.
- `hooklog.py` still has a stale `drain.py` docstring (left for the orchestrator).
- Commit trailer follows the session's attribution reminder (Claude Sonnet 5.5), not the brief's Opus 5.5 text.

## Live effects (not triggered)
On commit, Cursor `sessionStart` runs the prefetch, which builds into the real `~/.cache/workflow/0.1.0/`. New Claude Code sessions in this repo get the stdio `workflow` server instead of legacy `workflow-quality` HTTP tools.
