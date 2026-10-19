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
| `plugins/yakka/bin/yakka` | bash wrapper that execs `python3` on `plugins/yakka/client/yakka.py` for plugin commands, committed |
| `plugins/yakka/bin/VERSION` | collector release version (maintainer metadata; not used by the wrapper) |
| `plugins/yakka/bin/SHA256SUMS` | checksums for the collector release's four binaries, committed; not hook input |
| `plugins/yakka/bin/RELEASE_URL` | collector release download base, `https://github.com/codyhamilton/yakka/releases/download` |
| `tools/release/build.sh` | builds the four binaries and writes `SHA256SUMS` |

Binaries are never committed.

## Wrapper

`plugins/yakka/bin/yakka` dispatches plugin commands to the Python client:

1. `YAKKA_BIN`, if set, overrides the wrapper script itself (development).
2. Otherwise `exec python3` on `plugins/yakka/client/yakka.py` with the subcommand for `drain`, `mcp`,
   `login`, `status`, and `version` / `--version`.
3. `serve` and `ledger` are not available through the wrapper: print why on stderr and exit non-zero
   (operators run the Go collector from `packages/yakka`).

`plugins/yakka/bin/yakka version` and `plugins/yakka/bin/yakka --version` print `yakka <version> <commit>`.

Constraints: bash 3.2 compatible (macOS). With `YAKKA_BIN` unset, the spool kick starts
`python3 plugins/yakka/client/yakka.py drain` detached; hooks do not wait on the drain or the shim.
`YAKKA_BIN` set and executable is that program with `drain`.

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

`tools/release/build.sh` cross-compiles the **collector** binary with `CGO_ENABLED=0` and writes
`plugins/yakka/bin/SHA256SUMS`. Publishing the release (GitHub release assets for `bin/VERSION`) is a
publish action and happens only with the maintainer's agreement. Operators who need `yakka serve` or
`yakka ledger` run the Go binary from a release asset or a local `go build`; the plugin wrapper does not
fetch or build it.

## Per-harness configs

| Harness | File | Registers |
|---|---|---|
| Claude Code | `plugins/yakka/hooks/hooks.json`, `plugins/yakka/.mcp.json` | `plugins/yakka/script/spool.sh --harness claude`; shim as stdio |
| Cursor | `plugins/yakka/hooks/cursor.json`, `packages/hooklog/cursor-hooks.example.json` | `./script/spool.sh --harness cursor` |
| Codex | `plugins/yakka/hooks/codex.json` | `plugins/yakka/script/spool.sh --harness codex` |
| OpenCode | `packages/opencode-yakka-hooks` | writes spool files with the design 2 name; kicks `python3 plugins/yakka/client/yakka.py drain` |

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

`plugins/yakka` may depend on packages. Packages may depend on packages. Tools may depend on either. A package's runtime code and config do not resolve a path into `tools/`. `tools/release/test_layout.py` fails the build when that direction breaks, when a marketplace lists anything but the one yakka plugin (Claude `source` stays the relative path `plugins/yakka`; the Cursor entry may be the git-subdir object for `https://github.com/codyhamilton/yakka` at path `plugins/yakka` on ref `master`), or when a Cursor hook command is not `./script/...`. Each package README states Consumers, Build, Test, and Release. A change to the plugin itself bumps its version in the same change.

Shipped environment variables use the `YAKKA_` prefix with the same suffix as before. The legacy quality service keeps its original prefix; the 3.0.0 changelog lists that exception. Phase-trailer readers accept the pre-rename trailer and `Yakka-Phase`, and both report fences, through `tools/driver/trailer_keys.py`. Writers emit the `Yakka-*` forms. The dual-read rule is stated in `docs/design/system-architecture.md`.

`docs/lab/bootstrap/session-start.sh` and `docs/lab/CONSUMING_REPO.md` still fetch the pre-rename GitHub repository and the old cloud bootstrap script name. `install.sh` and `tools/cloud-env/bootstrap-yakka-skills.sh` do not. `packages/hooklog` tests set `YAKKA_QUALITY_URL`, which the hook edge does not read. `tools/driver/README.md` still shows only the legacy trailer and report fence; the driver accepts both.
