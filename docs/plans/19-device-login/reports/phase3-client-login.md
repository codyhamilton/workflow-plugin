# Phase 3 report: two-step client login

## Done
- `plugins/yakka/client/yakka.py`: removed `device_page_url`, `_login_exchange`, `_login_random_state`, the callback server, `LoginOptions`, the old `run_login`, and the now-unused `http.server` import. Added `login_start`, `login_wait`, new `run_login`, pending-file helpers, and `cmd_login [start|wait] [--endpoint URL]`. `wait` ignores `--endpoint`. `sleep` and `clock` are injectable parameters of `login_wait` and `run_login`.
- Endpoint: `--endpoint` (through `normalize_origin`), else `client.toml`, else `https://api.yakka.build`. `resolve_endpoint` is called only by login, so its missing-config path now returns the default; the "no collector endpoint" error is gone.
- Wrapper usage string and the pinned copy in `tools/release/test_release.py` both say `login [start|wait] [--endpoint URL]`.
- Go: `internal/login` deleted; `main.go` `login` prints "yakka login moved to the plugin wrapper (plugins/yakka/bin/yakka)" and exits 1; `login_test.go` replaced with a test of that. `internal/clientconfig` untouched.
- `test_login.py` rewritten: all nine required groups, against a fake HTTP server.

## Results
- `test_login.py`: 17 tests OK. All other client tests OK (`test_facts` needs `go` on PATH). `tools/release/test_release.py`: 10 tests OK.
- `go build ./...`, `go vet ./cmd/...`: clean. `go test ./internal/...`: all ok. `go test ./cmd/...`: only `TestHalfSetEnvRefusal` fails (see problems).
- grep for `device_page_url|_login_exchange|internal/login` in plugins, packages, tools: nothing.
- `YAKKA_CLIENT_CONFIG=<empty tmp>/c.toml yakka login wait`: one stderr line, exit 1.

## Departures
- Go usage string drops `login` entirely (the binary only refuses it), so the Go and wrapper usage strings differ by design.
- `wait` sleeps one `interval` before each poll (including the first) so it never polls early and triggers `slow_down`. Expiry is checked after the sleep.
- A 200 whose token fails validation, or an unusable pending file, is treated as a failure and deletes the pending file.
- Network errors, 429, 5xx and unrecognised errors during `wait` are retried until expiry.

## Deferred / known problems
- `go test ./cmd/...`: `TestHalfSetEnvRefusal` fails because an unrelated process (`workflow-linux-`, pid 1199756) holds 127.0.0.1:8770 on this machine. Not caused by this change.
- No combined slow_down sequence was run against a real server (Phase 1 note).
- `run_status` unchanged (Phase 4).
