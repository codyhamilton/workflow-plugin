# workflow (Go binary)

**Consumers** — harnesses via `plugins/yakka/bin/workflow`, `tools/release`, and `tools/quality` (catalogue).

**Build** — `go build` in this module, or the wrapper's step-4 source build from `plugins/yakka/bin/workflow`.

**Test** — `go test ./...` in `packages/workflow`.

**Release** — `tools/release/build.sh` (four `workflow-<os>-<arch>` binaries and `SHA256SUMS`).

Go module for the `workflow` CLI, embedded analytics site, and Jev catalogue under `catalogue/`.
