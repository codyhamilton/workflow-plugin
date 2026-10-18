# Python local client

## Intent

User request, verbatim:

> So what's the feeling. Some python (all runtimes will have python3) avoiding external deps, over a compiled binary.
>
> Python will be slower (immaterial due to async running), but avoid need for a build and binary download, and be more transparent to end users. Thoughts?

> Ok use the design, execute workflows to build a design and implement this change and create a PR. when ready mark PR ready for review. Coordinate the agents for design and phase execution

> open the PR as draft but only mark ready when fully complete

## Problem

The plugin-local client is a compiled Go binary. The hook and the MCP shim reach it through `plugins/yakka/bin/yakka`, which uses a cached binary, a checksummed download, or a local `go build`. That costs a release pipeline, a first-run download, and a blob the end user cannot read. The hook itself only writes the queue; the drain it starts is off the hook's return path, so the client's runtime is not on the hook's latency budget. The collector (`yakka serve`, sqlite, the site) is a different program and stays where it is.

## Solution Shape

The processes the plugin and the hook actually start — `drain`, `mcp`, `login`, `status`, and `version` — are one stdlib-only Python program shipped as source in the plugin tree. `spool.sh` still only writes the queue, then starts that program's `drain` instead of resolving a binary. The registered MCP server is that program's `mcp` on local stdio. `serve` and `ledger` stay the Go binary; a local `serve` still hosts its own in-process drain. `/v1/ingest` and the advisory GETs do not change. Parity with today's client is the existing Go client tests, ported, not a second behavior.

### Domain: Plugin client

- Owns: one program, `plugins/yakka/client/yakka.py`, run as `python3 plugins/yakka/client/yakka.py <command>`, for `drain`, `mcp`, `login`, `status`, and `version` / `--version`, and the hand-rolled reading and writing of client config. No third-party packages, including no TOML library and no third-party test runner. The hook, the MCP registrations, and `plugins/yakka/bin/yakka` all exec that path.
- Contract:
  - **Config.** Unchanged resolution. Both `YAKKA_ENDPOINT` and `YAKKA_KEY` set: those values, over the file. Exactly one set: `drain`, `mcp`, and `status` exit before any request and do not read the file. Neither set and `~/.config/yakka/client.toml` present (`YAKKA_CLIENT_CONFIG` overrides the path): `endpoint` and `key` from that file. Neither set and no file: `http://127.0.0.1:8770` with no bearer. The file format stays `name = "string"` lines, `#` and blanks skipped, unknown keys ignored. `login` writes `endpoint` and `key` at mode 0600.
  - **Python floor.** 3.10. The program runs on Linux and macOS. Windows is out of scope.
  - **`drain`.** Same queue (`$YAKKA_QUEUE` or `~/.local/share/yakka/queue`), same `.drain.lock` flock, same fact building and client scrub, same `POST <endpoint>/v1/ingest` body `{"facts":[...]}` with `Authorization: Bearer <key>` when a key is set. Delivery follows [design 2](../../design/02-edge-capture.md): delete on `accepted` or `duplicate`; `rejected/` plus a `.reason` on a rejected fact; retry on 5xx, network error, 401, 403, 408; `Retry-After` on 429; split on 400 or 413; idle exit with rescan. Fact kinds, `repo_id`, content hash, and the secret scrub follow [design 1](../../design/01-event-model-and-ingest.md). The lock is the ported Go tests in `internal/clientconfig`, `keys`, `secrets`, `facts`, and `drain`, excluding `TestHostedRetriesLockAndWakes`, plus the drain half of `TestHalfSetEnvRefusal`. Cases in `cmd/yakka/drain_test.go` that boot `yakka serve` stay Go. Strings the ported tests assert are part of the contract.
  - **`mcp`.** Local stdio JSON-RPC, not a remote URL. Tools remain `artifact_feedback`, `list_checks`, `search_artifacts`. `artifact_feedback` resolves `path`, accepts only `docs/plans/<plan>/DESIGN.md`, `docs/plans/<plan>/briefs/<name>.md`, and `docs/plans/<plan>/reports/<name>.md`, hashes the raw file with SHA-256, computes `repo_id` (normalised git remote, else `root:` plus the root commit), scans `queue/` and `rejected/`, may start `drain` and wait, then joins `GET /v1/artifacts` and compares hashes. The drain it starts is the same rule as the hook: `YAKKA_BIN` when that is set and executable, otherwise `python3` on this program's own script path, with argument `drain`. It does not start `python3` with no script, and it does not use `sys.executable` as the client. States, in the order the Go shim decides them: `queued`, `rejected`, `bad config`, `not delivered`, `stale`, `delivered`. A delivered result includes the screen, the scores, and the baseline comparison from `GET /v1/baselines`. `list_checks` and `search_artifacts` stay GETs of `/v1/checks` and `/v1/search`. A down service is a tool result, not an MCP error. The lock is the ported Go `internal/mcp` tests. Their `serve()` helper is an in-process httptest, not `yakka serve`, and those tests are part of this port.
  - **`login`.** Loopback `127.0.0.1:0/callback`. Device page is `https://yakka.build/device` when the collector host is `api.yakka.build`, otherwise `{collector}/device`. Then `POST {collector}/v1/device/exchange`, then the config file. No browser: the env pair, unchanged.
  - **`status`.** The existing stdout lines (queue path, queued count, oldest age, rejected count, drain running or not, config mode, endpoint reachable or not) after `GET <endpoint>/v1/health`. Exit non-zero when the endpoint is unreachable and the queue is non-empty.
  - **`version` / `--version`.** Stdout `yakka <version> <commit>\n`, exit 0. `<version>` is the text of `plugins/yakka/bin/VERSION`. `<commit>` is `YAKKA_COMMIT` when that is set, otherwise `unknown`.
- Non-goals: `serve`, `ledger`, ingest storage, screening, the site, sqlite, a faster drain, Windows, a remote MCP transport, publishing the client on pip.

### Domain: Hook spool

- Owns: `plugins/yakka/script/spool.sh`. It stays bash, does no parsing and no network, and holds no bearer.
- Contract: the write path is unchanged (envelope line, raw payload, tmp-then-rename, conversation id required, exit 0). After a successful spool, unless `YAKKA_HOOKLOG_KICK=0`, it starts one detached drain. `YAKKA_BIN` set and executable: that program, with `drain`, as today. `YAKKA_BIN` unset: `python3 plugins/yakka/client/yakka.py drain`. No cache lookup, no download, no `go build` on this path. The flock probe (and the mkdir lock where `flock(1)` is absent) is unchanged, so the kick still returns without waiting for delivery.
- Non-goals: fact building, HTTP, reading client config, becoming Python.

### Domain: Collector

- Owns: `yakka serve`, the in-process drain it hosts when the client endpoint is its own address, sqlite, the site, and `ledger`.
- Contract: `POST /v1/ingest` and `GET /v1/artifacts`, `/v1/checks`, `/v1/baselines`, `/v1/search`, `/v1/health` stay as [design 3](../../design/03-remote-service.md) and [design 4](../../design/04-advisory-surface.md) define them. The Go packages those commands use stay. The hosted drain and the Python drain exclude each other with the same `.drain.lock` flock.
- Non-goals: being the process the plugin downloads; reimplementing ingest in Python.

### Domain: Distribution

- Owns: how the plugin client and the hook configs reach a machine.
- Contract: the client is `plugins/yakka/client/yakka.py`. `plugins/yakka/bin/yakka` no longer resolves a cached binary, downloads a release asset, or builds with Go. It execs `python3` on that script for `drain`, `mcp`, `login`, `status`, and `version` / `--version`. `serve` and `ledger` through that entry exit non-zero and do not download; operators run the Go binary from `packages/yakka`. `tools/release/build.sh` still builds that collector binary. SessionStart no longer runs the client to fill a binary cache: the Claude and Codex SessionStart `--version` commands, Cursor's `prefetch-version.sh` kick, the Cursor example at `packages/hooklog/cursor-hooks.example.json`, and the OpenCode `--version` spawn go away. `version` remains a command a person can run. The gates that require the prefetch flip with it: `packages/hooklog/tests/test_surfaces.py` no longer expects a prefetch or a `--version` stub call, and `packages/opencode-yakka-hooks/tests/test_hooks.mjs` no longer expects `--version` on load. The OpenCode drain kick stays.
- Non-goals: a new installer, a venv, dropping the collector release, changing harness hook trust.

## Architectural Implications

- `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` do not describe the client binary. They stay as they are.
- [Design 2](../../design/02-edge-capture.md) says the drain is `yakka drain` in the Go binary, and its "changes from what exists" section says the old Python `drain.py` is removed in favour of Go. [Design 5](../../design/05-distribution.md) says the wrapper downloads or builds that binary, and that SessionStart prefetches it. [Design 4](../../design/04-advisory-surface.md) says `yakka mcp` is that binary, registered through the wrapper. [Design 3](../../design/03-remote-service.md) says one Go binary owns `serve`, `drain`, `mcp`, and `status`, chosen over Python so client and server are one implementation. Those four docs are in scope. After this change, design 3's "one implementation" rationale covers the collector only; the plugin client is the Python program; design 2, 4, and 5 describe that split. Design 4's prose is not a license to change shim behavior: where it and the Go shim differ, the ported tests win (see the ledger).
- Two drain implementations will exist: Go inside `serve`, Python on the plugin path. This design does not add a shared source or a generated client. A later delivery change is two edits. The ported tests lock the Python client at the port; the Go tests keep locking the hosted drain.
- The OpenCode plugin kicks `plugins/yakka/bin/yakka drain` and a version prefetch. The kick moves with the hook. The prefetch goes away with SessionStart.

## Decisions

Headless. Each scope-shaping choice is an Assumption Ledger entry. No `PROVENANCE.md`. The checkpoint is waved.

## Assumption Ledger

### Assumption 1

- Question: Which minor version of Python is the floor, given that every target runtime has `python3` and the client may not take a TOML library?
- Answer chosen: 3.10.
- Rationale: Plugin-adjacent Python already in this repo (`tools/cursor`, the driver) is 3.10+ with no third-party packages. The hand-rolled config parser does not need 3.11's `tomllib`. 3.10 is the oldest minor those docs still claim, and it is Ubuntu 22.04's `python3`. This cloud image has 3.12; the floor stays at the older documented minor.
- If wrong: A supported machine whose `python3` is 3.9 cannot run 3.10 syntax. Lower the floor and drop 3.10-only syntax. Do not raise it to gain `tomllib`. The floor is checked by running the suite under a 3.10 interpreter, not by a pass on a newer `python3`.

### Assumption 2

- Question: Where does the Python client live, and how is it invoked?
- Answer chosen: One script, `plugins/yakka/client/yakka.py`, run as `python3 plugins/yakka/client/yakka.py <command>`. Not a `packages/` module the plugin has to locate, and not an installed distribution.
- Rationale: The install root is already `plugins/yakka`. Shipping the source there is what removes the build and the download.
- If wrong: If a harness install copies only part of the plugin, the entry has to sit in the copied part. Ground shows the install root is the whole plugin directory.

### Assumption 3

- Question: Do the Go client packages get deleted once Python serves the plugin?
- Answer chosen: No. `serve` keeps hosting the drain in-process, so the Go drain, facts, secrets, keys, and MCP packages stay. The plugin path stops calling them.
- Rationale: `serve`, the collector, sqlite, and the site stay Go. Deleting the Go drain would either drop hosted mode or make `serve` depend on Python.
- If wrong: The hosted drain would have to shell out to the Python client, and `serve` would gain a Python dependency this design says it does not have.

### Assumption 4

- Question: What happens to `plugins/yakka/bin/yakka` and the four-arch release?
- Answer chosen: The wrapper stops downloading and building. It only dispatches the five Python commands. `serve` and `ledger` through it exit non-zero without network or `go build`. Operators run the Go binary themselves. `tools/release/build.sh` still produces the collector binary. `SHA256SUMS` stays a collector-release artifact, not a hook input.
- Rationale: Leaving a download behind `bin/yakka` keeps the mechanism this change removes on the entry the plugin already exposes. The collector release is a different consumer.
- If wrong: Anyone who starts a loopback collector by running the plugin wrapper loses that path and uses the Go binary directly.

### Assumption 5

- Question: Does `YAKKA_BIN` still override the drain the hook and the shim start?
- Answer chosen: Yes, for both the hook and the shim, one rule. Set and executable, that program is exec'd with `drain`. Unset, both start `python3 plugins/yakka/client/yakka.py drain`. Neither starts a bare `python3`, and the shim does not treat `sys.executable` as the client. No download and no build on the unset path.
- Rationale: Tests and local development already inject a drain through that variable. Today's Go shim starts `os.Executable()` plus `drain`, which is the client binary; once the client is this script, the matching path is the script, not the interpreter. The default path is what changes.
- If wrong: Production that pointed `YAKKA_BIN` at the Go client keeps doing so. Unset is the new default.

### Assumption 6

- Question: Does SessionStart still run `version` to warm a cache?
- Answer chosen: No. The prefetch commands go away, including the Cursor example and the OpenCode load spawn. `version` remains runnable by hand. `packages/hooklog/tests/test_surfaces.py` and `packages/opencode-yakka-hooks/tests/test_hooks.mjs` change with those commands: they currently require the prefetch and a `--version` call, and after this phase they must not.
- Rationale: Design 5's prefetch exists to fill the binary cache before MCP starts. Source in the plugin tree does not need that fill. Leaving the tests as they are would make "prefetch is gone" fail its own gate.
- If wrong: A harness that treated SessionStart `version` as a liveness probe loses that probe. The command still exists; nothing in the hook configs uses its stdout.

### Assumption 7

- Question: How is parity locked, and which disagreement between design 4 and the Go shim wins?
- Answer chosen: Port the existing Go client tests to stdlib `unittest`, run with `python3 -m unittest`. Tests that boot `serve` stay Go and are not the plugin client's gate. Where design 4's prose and the Go shim differ, the ported tests win. In particular the shim's states stay `queued`, `rejected`, `bad config`, `not delivered`, `stale`, and `delivered`, including baseline lines on `delivered`.
- Rationale: Parity is a port of the tests, not a second behavior and not a cleanup of the advisory prose. `unittest` keeps the no-third-party rule.
- If wrong: A brief that "corrects" the shim toward design 4's wording fails the ported tests and has left the contract.

### Assumption 8

- Question: What does `version` print for the commit, with no build embedding one?
- Answer chosen: `yakka <version> <commit>` where `<version>` is `plugins/yakka/bin/VERSION` and `<commit>` is `YAKKA_COMMIT` or else `unknown`. No `git` call.
- Rationale: The line shape is design 5's. A copied plugin has no repository metadata; guessing a commit from a surrounding checkout would change the line between installs.
- If wrong: Tooling that parsed a real sha out of the plugin client stops seeing one unless it sets `YAKKA_COMMIT`.

### Assumption 9

- Question: Which commands move, and what stays Go?
- Answer chosen: `drain`, `mcp`, `login`, `status`, and `version` move to stdlib Python. `serve`, the collector, sqlite, and the site stay Go. `ledger` stays the Go binary and is not a plugin command.
- Rationale: Settled with the request. Those five are the commands the plugin and the hook run.
- If wrong: The domain split is wrong and the design is re-signed. `ledger` does not grow a Python implementation inside this work.

### Assumption 10

- Question: What does the hook keep doing?
- Answer chosen: `spool.sh` stays the hook. It still only writes the queue. It starts the Python drain instead of a downloaded or locally built binary, and drops that fallback on this path.
- Rationale: Settled with the request. Capture stays bash so the hook does not pay a Python start.
- If wrong: Moving the spool itself into Python would put interpreter startup on the hook's return path, which this design refuses.

### Assumption 11

- Question: Does local MCP become a remote URL?
- Answer chosen: No. It stays a local stdio process, moved to Python, with the current `artifact_feedback` behavior: path resolution, the three plan paths only, content SHA-256, `repo_id`, a scan of `queue/` and `rejected/`, an optional drain start and wait, then `GET /v1/artifacts` and the hash comparison. `list_checks` and `search_artifacts` stay the two GETs.
- Rationale: Settled with the request. Harnesses spawn a command; the remote API is not this server's transport.
- If wrong: Pointing a harness at `https://api.yakka.build` as MCP would drop queue and rejected state, which the tool exists to report.

### Assumption 12

- Question: Do client config and the HTTP contracts change?
- Answer chosen: No. Existing `client.toml` and `YAKKA_ENDPOINT` / `YAKKA_KEY` keep working. `/v1/ingest` and the advisory GETs stay. There is no TOML library.
- Rationale: Settled with the request.
- If wrong: A new config file or a new ingest body would strand every installed client and is out of scope.

### Assumption 13

- Question: Which operating systems, and is speed a goal?
- Answer chosen: Linux and macOS only. Windows is out of scope. Speed is not a goal. The drain stays off the hook's return path.
- Rationale: Settled with the request. Design 5 already excludes Windows-native.
- If wrong: A Windows hook would need a non-bash spool this design does not contain.

## Open Questions

None.

## Phases

Three phases. The count and order are fixed. `refine` briefs each phase; none of this is a single unit a worker carries whole, so `refine` is not skipped.

### Phase 1 — The hook starts the Python drain

- Outcome: With `YAKKA_BIN` unset, `plugins/yakka/script/spool.sh` and the OpenCode drain kick start `python3 plugins/yakka/client/yakka.py drain` and do not download or `go build`. That process posts `POST <endpoint>/v1/ingest` and applies design 2's delivery table, including fact building, scrub, and client config. `python3 -m unittest` of the ported `clientconfig`, `keys`, `secrets`, `facts`, and `drain` cases exits 0, and the same command exits 0 under a Python 3.10 interpreter (the phase provides one when `python3` is newer). The port includes the drain half of `TestHalfSetEnvRefusal` and excludes `TestHostedRetriesLockAndWakes`. `go test` of `packages/yakka/internal/clientconfig`, `keys`, `secrets`, `facts`, and `drain`, and of the `packages/yakka/cmd/yakka` tests that boot `yakka serve`, still passes. `docs/design/02-edge-capture.md` describes this drain.
- Surfaces: `plugins/yakka/script/spool.sh`; `plugins/yakka/client/yakka.py`; `packages/opencode-yakka-hooks` drain spawn (`spawnBin(["drain"])`); `docs/design/02-edge-capture.md`; Go sources the port copies from: `packages/yakka/internal/clientconfig`, `keys`, `secrets`, `facts`, `drain` except `TestHostedRetriesLockAndWakes`, and `TestHalfSetEnvRefusal` in `packages/yakka/cmd/yakka/drain_test.go` (its drain half only).
- Approach: known
- Depends on: nothing

### Phase 2 — MCP is the Python stdio server

- Outcome: Each harness MCP registration starts `python3 plugins/yakka/client/yakka.py mcp` on stdio and does not resolve a binary. The ported `internal/mcp` tests pass, including the httptest `serve()` helper: `tools/list` is the three tools; `artifact_feedback` returns `queued`, `rejected`, `bad config`, `not delivered`, `stale`, and `delivered`, with baseline lines on `delivered`; `list_checks` and `search_artifacts` are the existing GETs; a queued path starts `YAKKA_BIN` with `drain` when that is set and executable, otherwise `python3 plugins/yakka/client/yakka.py drain`, and only when the lock is free; a down service is not an MCP error. `docs/design/04-advisory-surface.md` names this process.
- Surfaces: `plugins/yakka/client/yakka.py`; `plugins/yakka/.mcp.json`; `plugins/yakka/.codex-mcp.json`; `packages/hooklog/cursor-mcp.example.json`; `packages/hooklog/codex-mcp.example.toml`; `docs/design/04-advisory-surface.md`; `packages/yakka/internal/mcp` tests.
- Approach: known
- Depends on: Phase 1

### Phase 3 — The plugin entry is the Python client

- Outcome: `plugins/yakka/bin/yakka login`, `status`, and `version` / `--version` exec `python3 plugins/yakka/client/yakka.py` with that command. `login` writes `client.toml` at mode 0600 from the device exchange. `status` prints the existing lines and probes `GET /v1/health`. `version` prints `yakka <version> <commit>`. The same entry's `drain` and `mcp` dispatch to that script, and `serve` or `ledger` exits non-zero without a download or a build. SessionStart no longer prefetches: `packages/hooklog/tests/test_surfaces.py` reports `prefetch_seen == 0` and does not require a `--version` stub call, `packages/hooklog/cursor-hooks.example.json` SessionStart is only the spool, and `packages/opencode-yakka-hooks/tests/test_hooks.mjs` no longer expects `--version` on load. The ported tests that do not boot `yakka serve` pass: `packages/yakka/internal/login`, `TestLoginCommandMissingEndpoint`, `TestStatus`, and the status half of `TestHalfSetEnvRefusal`. `TestLoginDrainReadWriteAndReadOnly` stays a Go test and still passes. `docs/design/03-remote-service.md` and `docs/design/05-distribution.md` state that the plugin client is this program and that `serve` remains the Go binary, whose release build still exists.
- Surfaces: `plugins/yakka/bin/yakka`; `plugins/yakka/client/yakka.py`; `plugins/yakka/bin/SHA256SUMS` as a collector artifact only; `plugins/yakka/script/prefetch-version.sh`; `plugins/yakka/hooks/hooks.json`; `plugins/yakka/hooks/codex.json`; `plugins/yakka/hooks/cursor.json`; `packages/hooklog/cursor-hooks.example.json`; `packages/hooklog/tests/test_surfaces.py`; `packages/opencode-yakka-hooks` version spawn and `packages/opencode-yakka-hooks/tests/test_hooks.mjs`; `tools/release/build.sh`; `tools/release/test_release.py`; `docs/design/03-remote-service.md`; `docs/design/05-distribution.md`; `packages/yakka/internal/login`; `TestLoginCommandMissingEndpoint`; `TestStatus` and the status half of `TestHalfSetEnvRefusal` in `packages/yakka/cmd/yakka/drain_test.go`.
- Approach: known
- Depends on: Phase 1 and Phase 2

## Provenance Notes

The checkpoint is waved. Downstream review challenges the ledger.

Rejected: keeping the Go client and only skipping the download (a build remains); a remote MCP URL (drops queue state); a third-party HTTP or TOML package; deleting the Go drain (breaks hosted `serve`); `pytest` (a third-party runner); calling `git` from `version` to invent a commit.

The fact builder, the scrubber, and config parsing are not their own phases. Their observable result is the drain and the shim that use them.

The Python suite is a copy of the client behavior. It does not replace `go test` for the hosted drain. `cmd/yakka/drain_test.go` cases that call `startServe` or `startRemoteServe` stay on the Go side; they are not the plugin client's parity suite.

`docs/design/system-architecture.md` states principles and points at designs 2–5. It does not name the Go binary as the plugin client, so it is not a surface. Design 3 carries the "one Go binary" sentence that has to change.
