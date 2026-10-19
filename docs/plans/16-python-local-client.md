# Python local client

The plugin commands `drain`, `mcp`, `login`, `status`, and `version` moved from a cached Go binary into one stdlib Python program shipped in the plugin tree. The hook still only writes the queue, then starts that program's drain. `serve` and the collector stayed Go. The three phase outcomes held after review repaired one drain crash on an unreadable ingest 200.

## Intent

User request, verbatim:

> So what's the feeling. Some python (all runtimes will have python3) avoiding external deps, over a compiled binary.
>
> Python will be slower (immaterial due to async running), but avoid need for a build and binary download, and be more transparent to end users. Thoughts?
>
> Ok use the design, execute workflows to build a design and implement this change and create a PR. when ready mark PR ready for review. Coordinate the agents for design and phase execution
>
> open the PR as draft but only mark ready when fully complete

## Why This Existed

The plugin client was a compiled Go binary. The hook and the MCP shim reached it through `plugins/yakka/bin/yakka`, which used a cached binary, a checksummed download, or a local `go build`. That cost a release pipeline, a first-run download, and a blob the end user could not read. The drain was already off the hook's return path, so the client's runtime was not on the hook's latency budget.

## What Was Built

**Changed:** `plugins/yakka/client/yakka.py` and its stdlib unittest port; `plugins/yakka/script/spool.sh`; the OpenCode drain kick; harness MCP registrations; `plugins/yakka/bin/yakka`; SessionStart prefetch removal; designs 2, 3, 4, and 5.

The client is `python3 plugins/yakka/client/yakka.py <command>`. No third-party packages. Config resolution is unchanged: both `YAKKA_ENDPOINT` and `YAKKA_KEY`, or neither, with `~/.config/yakka/client.toml` or the loopback default. Exactly one of the pair set exits before a request. Python floor is 3.10.

### Phase 1 — The hook starts the Python drain

With `YAKKA_BIN` unset, `plugins/yakka/script/spool.sh` and the OpenCode drain kick start `python3 plugins/yakka/client/yakka.py drain`. Set and executable, `YAKKA_BIN` is still that program with `drain`. The process posts `POST <endpoint>/v1/ingest`, scrubs secrets, and applies the delivery table: delete on accepted or duplicate, `rejected/` plus a `.reason` on a rejected fact, retry on 5xx, network error, 401, 403, and 408, `Retry-After` on 429, split on 400 or 413. The Go packages those commands use stayed, because `yakka serve` still hosts a drain behind the same `.drain.lock`.

### Phase 2 — MCP is the Python stdio server

Claude, Codex, and the Cursor and Codex examples start `python3 plugins/yakka/client/yakka.py mcp` on stdio. Tools remain `artifact_feedback`, `list_checks`, and `search_artifacts`. States stay `queued`, `rejected`, `bad config`, `not delivered`, `stale`, and `delivered`. A queued path starts `YAKKA_BIN` with `drain` when that is set and executable, otherwise this script. A down service is a tool result, not an MCP error.

### Phase 3 — The plugin entry is the Python client

`plugins/yakka/bin/yakka` execs that script for `drain`, `mcp`, `login`, `status`, `version`, and `--version`. `serve` and `ledger` exit non-zero and do not download or build. `login` writes `client.toml` at mode 0600 from the device exchange. `status` prints the queue lines and probes `GET /v1/health`. `version` prints `yakka <version> <commit>`, with `<commit>` from `YAKKA_COMMIT` or else `unknown`. SessionStart no longer prefetches a binary: the Claude and Codex `--version` hooks, Cursor's `prefetch-version.sh`, the Cursor example's second command, and the OpenCode load-time `--version` spawn are gone. `tools/release/build.sh` still builds the collector.

## Deviations

The OpenCode test for an unset `YAKKA_BIN` waits out the module-level kick cooldown. `packages/hooklog/spool.sh` was left on the wrapper path; that wrapper now execs the Python client and does not download. Python 3.10 used during the build was installed on the machine and was not committed.

## Review

Independent review started at `b9c2a42` and the first pass finished on `74c82fa`. An HTTP 200 whose body was JSON but not a results object aborted the drain. Go retries that body. That fix matches the Go rule, and a ported test keeps the queue file. Stale README and design sentences that still described a downloaded binary were corrected in the same pass.

A later pass of the same SHA found a second high: `Build` and `HTTPSink.Send` turned `ts` through float64, so a spool timestamp such as `1729000000.123456789` changed and the row hash diverged from Go. `_fact_json` now keeps the digit text, and `Send` posts the fact bytes unchanged. `test_ts_nanosecond_literal_in_build_and_httpsink` locks that. No blocker or high remains after that fix.

## QA

There was no separate QA file. The build record ran the ported suite on Python 3.12 and 3.10, the Go client tests that still boot `yakka serve`, the hooklog surface tests, the OpenCode hook tests, and the wrapper tests. Review re-ran `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'` on 3.12.3: 52 tests, exit 0, including the unreadable-200 case and the nanosecond `ts` literal.

## Residual Risks

The plugin drain and the drain inside `yakka serve` are two implementations with no shared source. A later delivery change is two edits. This review did not re-run the suite under Python 3.10; the build record says 3.10.22 passed, and the client does not use a 3.11-only library. Login tests and one drain test still warn about an unclosed socket; the suite exits 0. Windows and speed were out of scope.

## Follow-ups

These stayed after the highs were fixed. They are parity gaps with the Go client, not a second behavior the design asked for.

- Queued age is printed as a whole number of seconds. Go prints a rounded duration (`3s`, `1m30s`), with halves away from zero.
- A 404 from artifact feedback adds `nothing queued or rejected locally`. Go uses that sentence only when the service is unreachable.
- Secret patterns treat `\b` as a Unicode boundary. Go's RE2 `\b` is ASCII, so a token after a non-ASCII letter is scrubbed there and not here.
- An invalid `client.toml` exits the standalone drain. Go keeps the file and retries inside the lock. The half-set env pair still exits before a request, in both.
- `HTTPSink.Send` maps `URLError` and `OSError` to a retry. A short read, or a key that is not a legal header, escapes that path. The header failure's text includes `Bearer` and the key. Go returns a fixed network error and does not return the key.
- Redirects copy `Authorization` onto the next request, including another host. Go drops the header unless the new host is the same host or a subdomain.
- A non-UTF-8 byte on MCP stdio raises `UnicodeDecodeError` and ends the process. Go returns a parse error and keeps reading.

The contracts that outlive this change are in [design 2](../design/02-edge-capture.md), [design 3](../design/03-remote-service.md), [design 4](../design/04-advisory-surface.md), and [design 5](../design/05-distribution.md).
