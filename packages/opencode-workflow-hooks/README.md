# @codyhamilton/opencode-workflow-hooks

OpenCode plugin that **approximates** Claude `PostToolBatch` soft signals:

1. Buffer each `tool.execute.after` per session.
2. Flush one batch per model step on `message.updated` or `session.idle`.
3. Spawn `python/batch_flush_cli.py` → shared `gate_thresholds` / `post_tool_batch_signal` → append `tools/driver/.jev-signal-log.jsonl` (or `WORKFLOW_JEV_SIGNAL_LOG`).
4. Optional analytics dual-write when `WORKFLOW_ANALYTICS_URL` is set (`host_kind: opencode` when `WORKFLOW_INSTALL_MODE=opencode`).

**Advisory only** — never blocks tools or changes exit codes. Does not call `assert_phase --deterministic` or enforce Flash review guidance.

Threshold constants for documentation: `workflow-signals.json` (source of truth remains `gate_thresholds.py` in the workflow-plugin lab).

## Install (workflow-plugin checkout)

From a clone of [workflow-plugin](https://github.com/codyhamilton/workflow-plugin):

```bash
# Skills (separate from this plugin)
./install.sh --opencode-skills
```

Register the plugin in **project** or **global** `opencode.json` (restart OpenCode after edits):

```json
{
  "plugin": [
    "file:///absolute/path/to/workflow-plugin/packages/opencode-workflow-hooks/src/index.ts"
  ]
}
```

Relative `file://` from repo root (when OpenCode cwd is the checkout):

```json
{
  "plugin": [
    "file://packages/opencode-workflow-hooks/src/index.ts"
  ]
}
```

See [`opencode.json.example`](opencode.json.example).

### codyh-ubuntu (Coding Harness Manager)

```bash
cd ~/workspace/workflow-plugin   # or your clone path
git pull origin master
./install.sh --opencode-skills

# ~/.config/opencode/opencode.json (or project opencode.json)
# Add plugin entry with absolute file:// URL to packages/opencode-workflow-hooks/src/index.ts
```

## Environment

| Variable | Default | Role |
|----------|---------|------|
| `WORKFLOW_OPENCODE_SIGNALS` | on | Set `0` to disable plugin hooks |
| `WORKFLOW_REPO_ROOT` | auto (package → repo root) | Python gate imports |
| `WORKFLOW_JEV_SIGNAL_LOG` | `tools/driver/.jev-signal-log.jsonl` | Signal JSONL path |
| `WORKFLOW_INSTALL_MODE` | `opencode` (set by plugin spawn) | Analytics `host_kind` |
| `WORKFLOW_ANALYTICS_URL` | unset | Remote dual-write when set |
| `WORKFLOW_ANALYTICS_TOKEN` | unset | Bearer token for analytics POST |
| `WORKFLOW_BATCH_FLUSH_CLI` | package `python/batch_flush_cli.py` | Override flush helper |
| `PYTHON` / `WORKFLOW_PYTHON` | `python3` | Interpreter for flush |

## Tests

```bash
# Package unit tests
python3 -m unittest discover -s packages/opencode-workflow-hooks/tests -v

# Lab proofs (shim to this package)
./docs/lab/RESEARCH/2026-09-30-opencode-hooks-plugin/proofs/run_proofs.sh
```

## npm link (optional)

```bash
cd packages/opencode-workflow-hooks
npm link
# In opencode.json: "@codyhamilton/opencode-workflow-hooks@0.1.0"
```

Publishing to npm is optional; `file://` from the monorepo checkout is the supported path for Coding Harness Manager.
