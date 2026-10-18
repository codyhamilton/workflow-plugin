# Design Intent 5: Distribution

How the `yakka` binary and the hook configs reach each machine and harness. Part of
[system-architecture.md](system-architecture.md).

## Targets

linux and darwin, amd64 and arm64. WSL is linux. No Windows-native support: hooks and the wrapper
need bash, and a Windows-native harness opening a WSL repo is out of scope.

## Layout

The monorepo separates **`packages/`** (libraries and the Go binary), **`tools/`** (maintainer automation), and **`plugins/yakka`** (the installable yakka plugin: skills, hooks, `script/`, `bin/`).

| Path | Holds |
|---|---|
| `packages/yakka/` | Go module: `cmd/yakka`, `internal/`, and embedded analytics site |
| `packages/yakka/catalogue/` | Jev criteria and check JSON shipped with the binary |
| `packages/hooklog/` | Hook capture edge: `spool.sh`, drain helpers, harness examples |
| `plugins/yakka/` | Yakka plugin install root: skills, harness manifests, `hooks/`, `script/`, `bin/` |
| `plugins/yakka/bin/yakka` | bash wrapper, committed |
| `plugins/yakka/bin/VERSION` | the release version the wrapper fetches |
| `plugins/yakka/bin/SHA256SUMS` | checksums for that version's four binaries, committed |
| `plugins/yakka/bin/RELEASE_URL` | release download base, `https://github.com/codyhamilton/yakka/releases/download` |
| `tools/release/build.sh` | builds the four binaries and writes `SHA256SUMS` |

Binaries are never committed.

## Wrapper

`plugins/yakka/bin/yakka` resolves a binary, then `exec`s it with all arguments. In order:

1. `YAKKA_BIN`, if set (development).
2. `~/.cache/yakka/<version>/yakka-<os>-<arch>`, if present.
3. Download `<RELEASE_URL>/v<version>/yakka-<os>-<arch>` with `curl` (falling back to `wget`) into a
   temp file, verify it against `SHA256SUMS` (`sha256sum`, falling back to `shasum -a 256`), refuse
   a mismatch, and `mv` it into the cache.
4. If no release asset exists and a Go toolchain and the module source are present, build into the
   cache (development, unverified by checksum). Builds are serialised with a `mkdir` lock in the
   cache directory; a second caller waits for it.
5. Otherwise print why on stderr and exit non-zero.

`yakka --version` prints `yakka <version> <commit>`.

Constraints: bash 3.2 compatible (macOS), no `flock`, concurrent first runs safe because the final
step is an atomic rename.

The first download never happens in a hook's foreground: the spool kick starts the drain detached,
and the shim's first start pays it once. A source build can take tens of seconds, longer than a
harness waits for an MCP server, so every harness's `SessionStart` hook also runs
`bin/yakka --version` detached, which fills the cache before the agent needs the shim.

## Local bootstrap

There is no install command. Local setup varies too much by system (systemd, launchd, a terminal)
for the plugin to presume one, and local mode needs no generated state:

- On loopback, `yakka serve` runs keyless on `127.0.0.1:8770` and stores under tenant `local`,
  whether or not the GitHub OAuth env vars are set (they are ignored). Setting `YAKKA_SERVE_KEYS`
  to anything but empty makes the process exit before it listens. How loopback serve is kept running
  is the user's choice.
- With no `~/.config/yakka/client.toml`, the drain and the shim use `http://127.0.0.1:8770`
  with no key.
- A non-loopback bind with `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET`, and
  `YAKKA_PUBLIC_URL` set is a remote collector. `YAKKA_SERVE_KEYS` is not a credential there:
  any non-empty value makes the process exit before it listens, on loopback or not. The collector
  is the API. Production Pages (`https://yakka.build`) holds the site, including GitHub's callback
  `https://yakka.build/oauth/callback`, which asks the API to set a host-only `workflow_session`
  cookie and return JSON. Local and release binaries still embed the site on the same origin.
  Clients and agents use issued bearer tokens (not the session cookie). **`yakka login`**
  (`--endpoint` optional) opens the Pages `/device` page when the endpoint is
  `https://api.yakka.build`, and that server's `/device` otherwise, then writes `endpoint` and
  `key` into `client.toml`. Hand-edit the file,
  or set **`YAKKA_ENDPOINT`** and **`YAKKA_KEY`** in the agent environment, when there is no
  browser. There is no `yakka init`.

With no `serve` running and no remote configured, the drain finds the endpoint unreachable and the
queue grows; `yakka status` reports it as a failure, not as idle.

## Release

`tools/release/build.sh` cross-compiles with `CGO_ENABLED=0` and writes `plugins/yakka/bin/SHA256SUMS`. Publishing
the release (GitHub release assets for `bin/VERSION`) is a publish action and happens only with the
maintainer's agreement. Until a release exists, the wrapper's step 4 is the working path.

## Per-harness configs

| Harness | File | Registers |
|---|---|---|
| Claude Code | `plugins/yakka/hooks/hooks.json`, `plugins/yakka/.mcp.json` | `plugins/yakka/script/spool.sh --harness claude`; shim as stdio |
| Cursor | `plugins/yakka/hooks/cursor.json`, `packages/hooklog/cursor-hooks.example.json` | `./script/spool.sh --harness cursor` |
| Codex | `plugins/yakka/hooks/codex.json` | `plugins/yakka/script/spool.sh --harness codex` |
| OpenCode | `packages/opencode-yakka-hooks` | writes spool files with the design 2 name; kicks `plugins/yakka/bin/yakka drain` |

All four drop the `artifact_submit.py` registration.

## Retired

- The systemd drain timer and service, and `install-drain.sh`.
- `packages/hooklog/drain.py`, once `yakka drain` replaces it.
- The HTTP MCP registration of the legacy service.

The legacy `workflow-quality.service` keeps running for the lab until the maintainer stops it.

## Not in this round

- Updating pinned plugin copies (the Codex copy at `451e009`); each picks up the new configs when
  the maintainer updates it.
- Registration and key issue (design 3).

## Layout rules

`plugins/yakka` may depend on packages. Packages may depend on packages. Tools may depend on either. A package's runtime code and config do not resolve a path into `tools/`. `tools/release/test_layout.py` fails the build when that direction breaks, when a marketplace lists anything but the one plugin at `plugins/yakka`, or when a Cursor hook command is not `./script/...`. Each package README states Consumers, Build, Test, and Release.

Shipped environment variables use the `YAKKA_` prefix with the same suffix as before. The legacy quality service keeps its original prefix; the 3.0.0 changelog lists that exception. Phase-trailer readers accept the pre-rename trailer and `Yakka-Phase`, and both report fences, through `tools/driver/trailer_keys.py`. Writers emit the `Yakka-*` forms. The dual-read rule is stated in `docs/design/system-architecture.md`.

`docs/lab/bootstrap/session-start.sh` and `docs/lab/CONSUMING_REPO.md` still fetch the pre-rename GitHub repository and the old cloud bootstrap script name. `install.sh` and `tools/cloud-env/bootstrap-yakka-skills.sh` do not. `packages/hooklog` tests set `YAKKA_QUALITY_URL`, which the hook edge does not read. `tools/driver/README.md` still shows only the legacy trailer and report fence; the driver accepts both.
