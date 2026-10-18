# yakka (Go binary)

**Consumers** — harnesses via `plugins/yakka/bin/yakka`, `tools/release`, and `tools/quality` (catalogue).

**Build** — `go build` in this module, or the wrapper's step-4 source build from `plugins/yakka/bin/yakka`.

**Test** — `go test ./...` in `packages/yakka`.

**Release** — `tools/release/build.sh` (four `yakka-<os>-<arch>` binaries and `SHA256SUMS`).

Go module for the `yakka` CLI, embedded analytics site, and Jev catalogue under `catalogue/`.
