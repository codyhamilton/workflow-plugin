# Review — Python local client

## Verdict

PASS

No blocker or high remains. Reviewed starting at `b9c2a42`. The post-fix tree is the commit that adds this file.

## Phase outcomes

- Phase 1, the hook starts the Python drain: met after the fix below. At `b9c2a42` it was partial: spool and OpenCode start `python3 plugins/yakka/client/yakka.py drain`, and the ported suite passed, but an unreadable HTTP 200 aborted the process instead of retrying. Design 2 names that drain.
- Phase 2, MCP is the Python stdio server: met. Harness registrations are `python3` on `plugins/yakka/client/yakka.py mcp`. Feedback order is queued, rejected, bad config, not delivered, stale, delivered. A down service is a tool result. Design 4 names this process.
- Phase 3, the plugin entry is the Python client: met. `plugins/yakka/bin/yakka` execs that script for the five commands; `serve` and `ledger` exit 1 with no download or build. SessionStart prefetch is gone, including the Cursor example and the OpenCode load spawn. `version` prints `yakka <version> <commit>`. Designs 3 and 5 keep `serve` on the Go binary and name the Python client.

## Findings

### high — unreadable ingest 200 aborts the drain

At `b9c2a42`, `HTTPSink.Send` treated only `JSONDecodeError` and `TypeError` from `json.loads` as an unreadable 200. A body of `null`, `[]`, or a non-object made `.get` raise `AttributeError`. `{"results": null}` stored `None`, and `apply` then called `len(None)`. `Run` does not catch that, so the drain died and left no retry. Go unmarshals into a results slice and sets status 502 when that fails, which the sender retries (`packages/yakka/internal/drain/http.go`).

Resolved in review. A fixer that did not review this change made `Send` match that rule: non-objects, non-list `results`, and non-object elements become status 502; a missing or null `results` stays 200 with an empty list. `test_200_null_body_keeps_files` keeps the queue file. Re-checked: `null`, `[]`, and `{"results":[1]}` return 502; `{"results": null}` and a normal results object do not raise. `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'` is 51 tests, exit 0.

### medium — package READMEs still described the binary client

`packages/hooklog/README.md` still described a cache, a checksummed download, a source build, a SessionStart `--version` warm, `bin/yakka serve`, and `bin/yakka mcp`. `packages/opencode-yakka-hooks/README.md` still described a `bin/yakka drain` kick and a load-time `--version` cache warm. Operators following those pages would miss the Python client and call a wrapper `serve` that exits 1.

Resolved in review. Both READMEs now name `python3 plugins/yakka/client/yakka.py` and the Go collector for `serve`.

### medium — MCP drain child was not reaped

`_mcp_start_drain` used `Popen` and did not wait. Go's `startDrain` starts `cmd.Wait` in the background. A long-lived `mcp` process would leave a zombie each time that drain exited.

Resolved in review. The spawn now waits on a daemon thread, the same non-blocking reap.

### low — durable docs lagged the kick path

Design 5 said the spool and OpenCode still start `plugins/yakka/bin/yakka drain`. Design 4 still said phase 3 would route `bin/yakka mcp`. Design 2's start sentence omitted the `YAKKA_BIN` override the hook still implements. `packages/yakka/README.md` still offered the wrapper's step-4 source build.

Resolved in review. Those sentences match the script the hook starts, the wrapper dispatch, and `go build` in `packages/yakka`.

### low — lock fd not closed on unexpected flock errors

`Running` and `_try_lock` closed the lock file on `BlockingIOError` and on success, and not on any other `OSError` from `flock`.

Resolved in review. Both paths close the file before returning.

## Intent and ledger

The verbatim request was a stdlib Python plugin client instead of a downloaded binary, with `serve` left in Go. The tree does that. Assumptions 2 through 13 still hold: one script under `plugins/yakka/client/`, Go drain kept for hosted `serve`, wrapper does not download, `YAKKA_BIN` still overrides, prefetch is gone, ported tests are the parity lock, version does not call git, the five commands moved, the spool stays bash, MCP stays local stdio, config and ingest bodies are unchanged, Windows stays out of scope.

Assumption 1 (Python 3.10 floor) was not re-run on a 3.10 interpreter in this review. The implementation record says the suite passed on 3.10.22. The client uses `from __future__ import annotations` and no 3.11-only standard library. This review ran the suite on 3.12.3.

## Plan sufficiency

The design was enough to judge the three outcomes, to place the 200-body miss against the Go drain it names as the lock, and to treat the ported unittest suite as the gate. It did not spell that particular 200 shape; the Go `Send` did.

## Residual risks

Two drain implementations remain, Go inside `serve` and Python on the plugin path, with no shared source. `packages/hooklog/spool.sh` still starts the wrapper rather than the script; the wrapper execs the Python client and does not download. Login and one drain test still emit a `ResourceWarning` for an unclosed socket; the suite exits 0. Speed and Windows were out of scope.
