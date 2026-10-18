# Python local client implementation

Tool: Cursor (Grok 4.7 orchestrator, subagent workers).
Run: https://cursor.com/agents/bc-27b13b9d-6b01-5282-9f4e-1ca8e3e1b786
Started: 2026-10-18T16:48:00Z.
Starting HEAD: `e1f01b4` on `cursor/python-local-client`.

`artifact_feedback`: the Yakka MCP namespace failed during live tool discovery (`namespaceStatus: error`, no tools). The service is unreachable. Each due call is recorded as unreachable and the run continues.

## Phase 1 — The hook starts the Python drain

Refined in `df7e427` into four units. 1-01, then 1-02, then 1-03 share `plugins/yakka/client/yakka.py`. 1-04 runs alongside that chain. Briefs say not to push; the orchestrator merges alongside worktrees onto `cursor/python-local-client` and pushes that ref only.

`artifact_feedback` on the four phase 1 briefs: unreachable. Refine reported the same. The namespace was checked again after the briefs landed and was still in error.

### 1-01-clientconfig-keys-secrets

- Built: `plugins/yakka/client/yakka.py` loads config, derives keys, and scrubs secrets. `drain` exits 2 with `yakka drain: not implemented`. Other commands exit 2 with `unknown command`. Ported tests live in `test_clientconfig.py`, `test_keys.py`, and `test_secrets.py`.
- Commit: `97b58d7`, on the branch via fast-forward. Report: `docs/plans/16-python-local-client/reports/1-01-clientconfig-keys-secrets.md`.
- Deviations: none. No contradiction with the brief.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.

### 1-04-hook-kick

- Built: `spool.sh` and the OpenCode `["drain"]` spawn start `python3 plugins/yakka/client/yakka.py drain` when `YAKKA_BIN` is unset. Design 2 names that process. `YAKKA_BIN` set still execs that program with `drain`.
- Commit: `a189949`, merged in `f04757e`. Report: `docs/plans/16-python-local-client/reports/1-04-hook-kick.md`.
- Deviations: the new OpenCode unset-bin test sleeps 10 seconds so it runs after `kickDrain`'s module-level cooldown. Not a contract contradiction; the brief is unchanged.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.
