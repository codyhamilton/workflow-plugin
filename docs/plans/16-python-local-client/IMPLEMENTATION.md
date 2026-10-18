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

### 1-02-facts

- Built: `File`, `Output`, `Build`, and `WritePaths` on `plugins/yakka/client/yakka.py`. `test_facts.py` ports the Go `facts` tests and reads `packages/hooklog/tests/fixtures/`. `drain` still exits 2.
- Commit: `a23e3cd`. Report: `docs/plans/16-python-local-client/reports/1-02-facts.md`.
- Deviations: none named. Ingest assertions call Go `ingest.Ingest` through a test-only file the suite deletes; no Go file is committed. No contradiction with the brief.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.

### 1-03-drain

- Built: `cmd_drain` runs `RunStandalone`. The script posts `POST /v1/ingest`, applies the delivery table, and takes the flock on `.drain.lock`. `test_drain.py` ports the Go drain tests except `TestHostedRetriesLockAndWakes`, plus the drain half of `TestHalfSetEnvRefusal`.
- Commit: `f7e6c86`. Report: `docs/plans/16-python-local-client/reports/1-03-drain.md`.
- Deviations: none named. No contradiction with the brief. Python 3.10.22 was installed on the machine from the deadsnakes PPA and was not committed.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.

`artifact_feedback` on the four reports: unreachable. A search of the Yakka namespace for `artifact_feedback` returned no tools; the namespace is still in error.

### Phase 1 verification

Checked from `f7e6c86`, not from the reports.

- `python3` (3.12.3) `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'`: 42 tests, exit 0.
- `python3.10` (3.10.22), the same command: 42 tests, exit 0.
- `python3 -m unittest discover -s plugins/yakka/script -p 'test_kick.py'`: 6 tests, exit 0. `bash -n plugins/yakka/script/spool.sh`: exit 0.
- `node --experimental-strip-types --test tests/test_hooks.mjs` in `packages/opencode-yakka-hooks`: 9 pass, 0 fail, including the unset-`YAKKA_BIN` drain spawn.
- `go test` of `internal/clientconfig`, `keys`, `secrets`, `facts`, and `drain`: exit 0. `go test ./cmd/yakka` with the brief's `-run` list: exit 0 (57s). `TestHostedRetriesLockAndWakes` is not in `test_drain.py`.
- With `YAKKA_BIN` unset, `plugins/yakka/script/spool.sh --harness claude --event Stop` exited 0 and started `python3 /home/ubuntu/yakka/plugins/yakka/client/yakka.py drain`. That process `POST`ed `/v1/ingest` with `Authorization: Bearer`, one fact, and an `AKIA…` value replaced by `[REDACTED:aws_access_key]`. The queue file was deleted after `accepted`. A rejected result moved the file to `rejected/` with a `.reason`. Exactly one of `YAKKA_ENDPOINT` and `YAKKA_KEY` exited 1 before any request; stderr contained `YAKKA_ENDPOINT`, and a listener on `127.0.0.1:8770` accepted nothing.
- `docs/design/02-edge-capture.md` names `python3 plugins/yakka/client/yakka.py drain`.

Outcome holds.

### Carried

1. `Running()` in `plugins/yakka/client/yakka.py` returns true when `flock` is busy and does not close the lock file. Phase 2's lock check should close it.
2. `plugins/yakka/client/test_drain.py` leaves the fake HTTP server socket open (`ResourceWarning`). Test-only.

## Phase 2 — MCP is the Python stdio server

Tool: Cursor (Grok 4.7 orchestrator, Composer 2.5 workers).
Run: https://cursor.com/agents/bc-75c9930f-d6d2-5704-b3c0-550b4e9d222f
Started: 2026-10-18T17:28:00Z.
Starting HEAD: `feb1b90` on `cursor/python-local-client`.

`artifact_feedback`: the Yakka MCP namespace failed during live tool discovery (`namespaceStatus: error`, no tools). The service is unreachable. Each due call is recorded as unreachable and the run continues.

Refined in `ca5bbb7` into two units. 2-01 owns the Python `mcp` command and its tests. 2-02 owns harness registrations and design 4. They run alongside each other on disjoint paths. Phase 1 carried items are placed in 2-01.

`artifact_feedback` on `briefs/2-01-mcp-command.md` and `briefs/2-02-mcp-registrations.md`: unreachable. A search of the Yakka namespace for `artifact_feedback` returned no tools. The namespace was checked again and is still in error.

2-01 and 2-02 commit in local worktrees (`work/2-01`, `work/2-02`) and do not push those refs. The orchestrator merges them onto `cursor/python-local-client` and pushes that ref only.

### 2-02-mcp-registrations

- Built: the four harness MCP configs start `python3` on `client/yakka.py` with argument `mcp`. Design 4 Shape and Registration name `python3 plugins/yakka/client/yakka.py mcp`.
- Commit: `61b8b58`, fast-forwarded onto the branch. Report: `docs/plans/16-python-local-client/reports/2-02-mcp-registrations.md`.
- Deviations: none named. The report's frontmatter names the worker; the brief template has no identity frontmatter. Not a contract contradiction; the brief is unchanged.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.

### 2-01-mcp-command

- Built: `python3 plugins/yakka/client/yakka.py mcp` is a stdio JSON-RPC server with `artifact_feedback`, `list_checks`, and `search_artifacts`. `test_mcp.py` ports `TestShim`. `Running()` closes the lock file when `flock` is busy. `test_drain.py` closes the fake HTTP server after shutdown.
- Commit: `b24f344`, merged in `0c909e3`. Report: `docs/plans/16-python-local-client/reports/2-01-mcp-command.md`.
- Deviations: none named. No contradiction with the brief. The worker did not run the 3.10 unittest gate (`python3.10` was absent). `test_half_set_env_refusal_drain` can fail with `Address already in use` on `127.0.0.1:8770` when that port is held; a rerun passed when it was free.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.

`artifact_feedback` on `reports/2-01-mcp-command.md` and `reports/2-02-mcp-registrations.md`: unreachable. The Yakka namespace is still in error and has no tools.

### Phase 2 verification

Checked from `8755dd9`, not from the reports.

- `python3` (3.12.3) `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'`: 43 tests, exit 0.
- `python3.10` (3.10.22), the same command: 43 tests, exit 0. Python 3.10.22 was installed on the machine from the deadsnakes PPA and was not committed.
- `go test ./internal/mcp -count=1` in `packages/yakka`: exit 0.
- `python3 plugins/yakka/client/yakka.py mcp` with stdin closed: exit 0.
- A live stdio session of that process: `tools/list` returned `artifact_feedback`, `list_checks`, and `search_artifacts`. `list_checks` and `search_artifacts` against `http://127.0.0.1:1` returned `service unreachable at http://127.0.0.1:1` with `isError` false.
- A queued `docs/plans/x/DESIGN.md` returned `state: queued` and was not an MCP error. `YAKKA_BIN` set and executable was spawned with argument `drain`. Unset, the spawn was `python3 /workspace/plugins/yakka/client/yakka.py drain`. With `.drain.lock` held, no process was spawned.
- The four harness registrations use `command` `python3` and args ending in the client script plus `mcp`. `python3 -m json.tool` on `plugins/yakka/.mcp.json` and `packages/hooklog/cursor-mcp.example.json`: exit 0.
- `docs/design/04-advisory-surface.md` names `python3 plugins/yakka/client/yakka.py mcp`. The remaining `bin/yakka mcp` line is the Phase 3 forward reference.

Outcome holds.

### Carried

1. `plugins/yakka/client/test_drain.py` `test_half_set_env_refusal_drain` binds `127.0.0.1:8770` and fails with `Address already in use` when that port is held. A rerun passes when the port is free.
2. `docs/plans/16-python-local-client/reports/2-02-mcp-registrations.md` has identity frontmatter. The brief template does not. The brief is unchanged.

## Phase 3 — The plugin entry is the Python client

Tool: Cursor (Grok 4.7 orchestrator, Composer 2.5 workers).
Run: https://cursor.com/agents/bc-73d9504b-60a7-5a37-b678-4a22bef6d789
Started: 2026-10-18T18:10:02Z.
Starting HEAD: `d14c82d` on `cursor/python-local-client`.

`artifact_feedback`: the Yakka MCP namespace failed during live tool discovery (`namespaceStatus: error`, no tools). The service is unreachable. Each due call is recorded as unreachable and the run continues.

Phase 3 has no Units list. `refine` is dispatched as a separate context before any implementation unit.

Refined in `d3beccc` into four units. 3-01 owns the Python login, status, and version commands. 3-02 owns `plugins/yakka/bin/yakka`. 3-03 owns SessionStart prefetch removal. 3-04 owns design 3 and design 5. They run alongside each other on disjoint paths. Phase 2 carried item 1 (port 8770) is placed in 3-01. Carried item 2 is informational and is not a unit.

`artifact_feedback` on `briefs/3-01-login-status-version.md`, `briefs/3-02-bin-yakka-wrapper.md`, `briefs/3-03-sessionstart-prefetch.md`, and `briefs/3-04-design-03-05.md`: unreachable. The Yakka namespace was checked again after the briefs landed and is still in error with no tools.

3-01 through 3-04 commit in local worktrees (`work/3-01`, `work/3-02`, `work/3-03`, `work/3-04`) and do not push those refs. The orchestrator merges them onto `cursor/python-local-client` and pushes that ref only.

### 3-04-design-03-05

- Built: design 3 splits the Go collector (`serve`, hosted drain, `ledger`) from the plugin client `python3 plugins/yakka/client/yakka.py`. Design 5's wrapper is Python dispatch only; SessionStart prefetch prose is gone; `SHA256SUMS` and `tools/release/build.sh` stay the collector release.
- Commit: `a9f8bc8`, fast-forwarded onto the branch. Report: `docs/plans/16-python-local-client/reports/3-04-design-03-05.md`.
- Deviations: committed on `work/3-04` because the four units ran alongside; the brief names `cursor/python-local-client`. Not a contract contradiction; the brief is unchanged.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.

### 3-03-sessionstart-prefetch

- Built: Claude, Codex, and Cursor SessionStart no longer run `--version` or `prefetch-version.sh`. The script is deleted. The hooklog example SessionStart is spool only. OpenCode no longer spawns `--version` on load. `test_surfaces.py` expects `prefetch_seen == 0` and does not wait on a `--version` stub. The drain kick is unchanged.
- Commit: `2d4de0a`, merged in `4ec3c82`. Report: `docs/plans/16-python-local-client/reports/3-03-sessionstart-prefetch.md`.
- Deviations: committed on `work/3-03` for the alongside run. Not a contract contradiction; the brief is unchanged.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.

### 3-02-bin-yakka-wrapper

- Built: `plugins/yakka/bin/yakka` execs `python3` on `client/yakka.py` for `drain`, `mcp`, `login`, `status`, `version`, and `--version`. `YAKKA_BIN` still overrides. `serve` and `ledger` exit 1 with a collector message and do not download or build. `WrapperTests` cover that dispatch. `BuildTests.test_7_build_sh` still passes.
- Commit: `bc8548f`, merged in `956096e`. Report: `docs/plans/16-python-local-client/reports/3-02-bin-yakka-wrapper.md`.
- Deviations: committed on `work/3-02` for the alongside run. `Base.env()` calls `goenv` only when `go=True`, so wrapper tests do not need a Go toolchain. Not a contract contradiction; the brief is unchanged.
- Agent: Composer 2.5. Turns and final context were not reported by the harness.
