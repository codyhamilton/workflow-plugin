# yakka (Go binary)

**Consumers** — `tools/release` and `tools/quality` (catalogue). The plugin client is `plugins/yakka/client/yakka.py`, not this binary.

**Build** — `go build` in this module.

**Test** — `go test ./...` in `packages/yakka`.

**Release** — `tools/release/build.sh` (four `yakka-<os>-<arch>` binaries and `SHA256SUMS`).

Go module for the `yakka` CLI, embedded analytics site, and Jev catalogue under `catalogue/`.
