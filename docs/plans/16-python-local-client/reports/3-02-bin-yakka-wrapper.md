---
cursor:
  subagentId: "bc-2037ea6a-f9cf-5132-a001-8aef25a9d2b8"
---

# Execution report: 3-02 bin/yakka wrapper

**Status:** done

## What was done (brief mapping)

- Replaced `plugins/yakka/bin/yakka` cache/download/Go-build path with a thin dispatcher: `YAKKA_BIN` override unchanged; otherwise `exec python3` on `client/yakka.py` for `drain`, `mcp`, `login`, `status`, `version`, and `--version`; `serve` / `ledger` print a Go-collector message and exit 1 with no network or cache use; empty or unknown argv prints usage and exits 2. Preserved bash 3.2 style and `YAKKA_ROOT` export.
- Rewrote `tools/release/test_release.py` `WrapperTests` for the new contract (Python dispatch stubs, serve/ledger refusal, usage, `YAKKA_BIN`, bash32 lint). Skipped `goenv` when `go=False` so override-only tests run without a toolchain. `BuildTests.test_7_build_sh` unchanged and passing.
- Did not edit `build.sh`, `yakka.py`, hooks, or `SHA256SUMS`.

## Done evidence (before → after)

| Check | Before | After |
|-------|--------|-------|
| `bash -n plugins/yakka/bin/yakka` | exit 0 | exit 0 |
| `python3 tools/release/test_release.py WrapperTests` | ERROR (missing `~/.local/go/bin/go` on several tests; cache/build tests expected old wrapper) | exit 0, 9 tests OK |
| `python3 tools/release/test_release.py BuildTests.test_7_build_sh` | not run (no Go at `GOBIN` in env) | exit 0 (~65s) after installing Go 1.27.1 to `~/.local/go` |
| `bin/yakka serve` (no `YAKKA_BIN`) | attempted Go build, exit 1 | stderr mentions Go/collector; exit 1; no `~/.cache/yakka` created |
| `bin/yakka drain` vs Python client | N/A (built binary path) | `WrapperTests` assert `exec` via stub `python3` with `CLIENT … drain` |

## Departures

- **Commit branch:** Brief says `cursor/python-local-client`; orchestrator assigned `work/3-02` — committed on `work/3-02`.
- **`env()` in `Base`:** Only call `goenv` when `go=True` so wrapper tests with `go=False` do not require Go at `GOBIN` (behavior of `test_7_build_sh` unchanged when `go=True`).

## Contradictions

- Brief commit branch vs orchestrator branch (above); resolved per orchestrator.
- `docs/design/05-distribution.md` still describes download/cache prefetch; `DESIGN.md` Phase 3 supersedes for the plugin wrapper — intentional per brief (“do not reopen” contract).

## Unfinished work

- Parallel units (3-01, 3-03, 3-04) still own full `login` / `status` / `version` behavior inside `yakka.py`; wrapper already dispatches those commands.
- Design doc 05 / SessionStart prefetch narrative not updated in this unit (out of scope).

## Known problems

- None observed within done evidence. Real `python3 … drain` still blocks on queue I/O (unchanged client behavior); wrapper tests use a stub `python3`.

## Turns / context

Not reported by harness.
