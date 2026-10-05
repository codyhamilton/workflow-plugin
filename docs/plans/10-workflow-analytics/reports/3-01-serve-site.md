# Report: 3-01 — Serve the embedded site

Status: done.

## What was done

- `tools/workflow/internal/serve/site.go` (new): `//go:embed all:site`, package variable `siteFS` (the embedded `site/` subtree; tests override it), and `siteHandler(fs.FS)`. Mode is decided once at build: not embedded when `index.html` is missing or contains `workflow-analytics-placeholder`.
- `serve.go`: only the catch-all registration changed, to `mux.HandleFunc("/", siteHandler(siteFS))`. `cors`, `localGuard`, `auth`, `method` and the `/v1` routes are untouched and still wrap it.
- `site/index.html`: the placeholder, the only file in `site/`.
- `site_test.go`: placeholder FS, missing index, the real embedded placeholder through `Handler()`, built FS in local and keyed mode, and `localGuard` still returning 403 for a non-loopback Host.

## Evidence

- Before: `go test ./internal/serve/ -run Site` failed to build (`undefined: siteFS`).
- After: `go test ./internal/serve/ -run Site -v` passes all 5 tests. `go vet ./...` and `go test ./...` pass. `gofmt -l .` prints nothing.
- Existing serve tests pass unchanged.

## Departures from the brief

- None in behavior. One note for 3-02 and the phase verifier: in local mode `localGuard` answers a `POST` that is not `application/json` with 415 before the site handler runs. The 405 `Allow: GET, HEAD` response is therefore reached by a local-mode `POST /` only when the request is JSON. The test sets that header. This follows from "keep `localGuard` wrapping" and I did not change it.

## Unfinished

Nothing. 3-02 can copy the build output into `site/`. It must delete or overwrite the placeholder `index.html` so the marker is absent.

## Known problems

None. `/v1` paths that match no route return `{"error":"not found"}` in both modes, as before.
