# Design Intent 5: Distribution

How the `workflow` binary and the hook configs reach each machine and harness. Part of
[system-architecture.md](system-architecture.md).

## Targets

linux and darwin, amd64 and arm64. WSL is linux. No Windows-native support: hooks and the wrapper
need bash, and a Windows-native harness opening a WSL repo is out of scope.

## Layout

| Path | Holds |
|---|---|
| `tools/workflow/` | Go module: `cmd/workflow` and `internal/` packages |
| `bin/workflow` | bash wrapper, committed |
| `bin/VERSION` | the release version the wrapper fetches |
| `bin/SHA256SUMS` | checksums for that version's four binaries, committed |
| `bin/RELEASE_URL` | release download base, `https://github.com/codyhamilton/workflow-plugin/releases/download` |
| `tools/release/build.sh` | builds the four binaries and writes `SHA256SUMS` |

Binaries are never committed.

## Wrapper

`bin/workflow` resolves a binary, then `exec`s it with all arguments. In order:

1. `WORKFLOW_BIN`, if set (development).
2. `~/.cache/workflow/<version>/workflow-<os>-<arch>`, if present.
3. Download `<RELEASE_URL>/v<version>/workflow-<os>-<arch>` with `curl` (falling back to `wget`) into a
   temp file, verify it against `SHA256SUMS` (`sha256sum`, falling back to `shasum -a 256`), refuse
   a mismatch, and `mv` it into the cache.
4. If no release asset exists and a Go toolchain and the module source are present, build into the
   cache (development, unverified by checksum). Builds are serialised with a `mkdir` lock in the
   cache directory; a second caller waits for it.
5. Otherwise print why on stderr and exit non-zero.

`workflow --version` prints `workflow <version> <commit>`.

Constraints: bash 3.2 compatible (macOS), no `flock`, concurrent first runs safe because the final
step is an atomic rename.

The first download never happens in a hook's foreground: the spool kick starts the drain detached,
and the shim's first start pays it once. A source build can take tens of seconds, longer than a
harness waits for an MCP server, so every harness's `SessionStart` hook also runs
`bin/workflow --version` detached, which fills the cache before the agent needs the shim.

## Local bootstrap

There is no install command. Local setup varies too much by system (systemd, launchd, a terminal)
for the plugin to presume one, and local mode needs no generated state:

- `workflow serve` with no `WORKFLOW_SERVE_KEYS` runs keyless on `127.0.0.1:8770` and stores under
  tenant `local`. How it is kept running is the user's choice.
- With no `~/.config/workflow/client.toml`, the drain and the shim use `http://127.0.0.1:8770`
  with no key.
- Remote mode is opted into with `workflow login` (not built yet), which ensures a tenant and key
  exist and writes `client.toml`.

With no `serve` running and no remote configured, the drain finds the endpoint unreachable and the
queue grows; `workflow status` reports it as a failure, not as idle.

## Release

`tools/release/build.sh` cross-compiles with `CGO_ENABLED=0` and writes `bin/SHA256SUMS`. Publishing
the release (GitHub release assets for `bin/VERSION`) is a publish action and happens only with the
maintainer's agreement. Until a release exists, the wrapper's step 4 is the working path.

## Per-harness configs

| Harness | File | Registers |
|---|---|---|
| Claude Code | `hooks/hooks.json`, `.mcp.json` | `spool.sh --harness claude`; shim as stdio |
| Cursor | `hooks/cursor.json`, `tools/hooklog/cursor-hooks.example.json` | `spool.sh --harness cursor` |
| Codex | `tools/hooklog/codex-hooks.example.json` | `spool.sh --harness codex` |
| OpenCode | `packages/opencode-workflow-hooks` | writes spool files with the design 2 name; kicks `bin/workflow drain` |

All four drop the `artifact_submit.py` registration.

## Retired

- The systemd drain timer and service, and `install-drain.sh`.
- `tools/hooklog/drain.py`, once `workflow drain` replaces it.
- The HTTP MCP registration of the legacy service.

The legacy `workflow-quality.service` keeps running for the lab until the maintainer stops it.

## Not in this round

- The monorepo reorganisation.
- Updating pinned plugin copies (the Codex copy at `451e009`); each picks up the new configs when
  the maintainer updates it.
- Registration and key issue (design 3).
