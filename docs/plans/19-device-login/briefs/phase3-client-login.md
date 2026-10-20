# Brief: phase3-client-login — Two-step client login

Consumer: a worker on the Python client (`plugins/yakka/client`) and the Go binary (`packages/yakka`). Phase 3, the only unit.
Owned paths: `plugins/yakka/client/yakka.py` (login section and `cmd_login`/dispatch only), `plugins/yakka/client/test_login.py` (rewrite), `plugins/yakka/bin/yakka` (usage string), `tools/release/test_release.py` (pinned usage), `packages/yakka/cmd/yakka/main.go`, `packages/yakka/cmd/yakka/login_test.go`, `packages/yakka/internal/login/` (delete). Touch nothing else. `internal/clientconfig` stays: `serve/host.go` and `drain` use it.
Commits: one commit on `feat/device-login`; include the report in it.
Report: write `docs/plans/19-device-login/reports/phase3-client-login.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: Phase 1 (closed, `2dc4811`). Read `reports/phase1-grant-flow.md` for the server's real responses. Tests use a fake server; no real server runs.
Runs alongside: nothing.
Budget: read 8 files, about 450 lines changed (mostly deletion), 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/19-device-login/IMPLEMENTATION.md` and report `over budget`.

## Required reading, in order

1. `docs/plans/19-device-login/DESIGN.md`: Phase 3, "Domain: Login client (Python)", and the `/v1/device/code` and `/v1/device/token` contracts under "Domain: Device grant (server)".
2. `plugins/yakka/client/yakka.py` from `# --- login ---` (about line 2496) to `run_login`'s end, plus `cmd_login` and `main`. Find `write_client_config`, `_request_base`, the client config path function and `_line_re` before reusing them.
3. `plugins/yakka/client/test_login.py`: the fake-server and `LoginEnv` setup to reuse.
4. `packages/yakka/cmd/yakka/main.go` and `login_test.go`.
5. `plugins/yakka/bin/yakka` and `tools/release/test_release.py` around the usage string.

## Goal

`yakka login start` and `yakka login wait` are two commands an agent can drive without blocking, `yakka login` composes them, the endpoint defaults to `https://api.yakka.build`, and the loopback login exists nowhere in the repo's client or Go binary.

## Contract

The design's Login client contract wins over this brief on any conflict. Summary of what is built:
- Endpoint: `--endpoint`, else `endpoint` in `client.toml`, else `https://api.yakka.build`. `--endpoint` still goes through `normalize_origin`.
- `start`: POST `/v1/device/code` (anonymous, empty `{}` body). Stdout is exactly `url: <verification_uri_complete>`, `code: <user_code>`, `expires: <RFC 3339 UTC>` (from `expires_in`). Writes `<client config path>.pending`, mode 0600, JSON `{endpoint, device_code, user_code, interval, expires_at}`; a new `start` replaces it. Exits 0 at once. Any failure: exit 1, one stderr line; a 404 says "this endpoint has no device login".
- `wait`: reads the pending file, polls `/v1/device/token` every `interval` seconds. `authorization_pending` continues; `slow_down` adds 5 s to the interval; 200 writes `client.toml` via `write_client_config` (endpoint from the response; 0600), deletes the pending file, prints `wrote <path>` and `tenant: <tenant>` to stderr, exit 0. `access_denied`, `expired_token`, or passing the pending `expires_at`: exit 1, one stderr line, pending file deleted. No pending file: exit 1, nothing to delete. Network errors are retried until expiry.
- `login` (no subcommand): `start`, then opens `verification_uri_complete` best-effort (`YAKKA_LOGIN_BROWSER` overrides the opener command, as the current code does; an opener failure is not an error), then `wait`.
- Neither command prints the token or `device_code`, on stdout or stderr.
- Make `wait`'s sleep and clock injectable so tests do not really sleep.

## Changes

- `yakka.py`: remove `device_page_url`, `_login_exchange`, `_login_random_state`, the callback server and the old `run_login`. Add `login_start`, `login_wait`, and a new `run_login`. `cmd_login` takes the optional `start|wait` subcommand and `--endpoint` (`wait` ignores it; the pending file holds the endpoint). Replace the "no collector endpoint" failure for login with the default. `resolve_endpoint` is also reached from other callers; check before changing its error path and leave other callers' behaviour alone.
- Go: delete `internal/login`. In `main.go` remove the import and flag parsing; `yakka login` (any args) prints one stderr line naming the plugin wrapper (for example "yakka login moved to the plugin wrapper (plugins/yakka/bin/yakka)") and exits 1. Keep the word `login` in the usage string only if the Go binary still accepts the command; the wrapper's usage string and the release test's pinned copy must stay equal to each other, and say `login [start|wait] [--endpoint URL]`.
- `login_test.go`: replace with a test that `login` exits 1 and the message names the plugin wrapper. Delete the loopback tests.
- `test_login.py`: rewrite. Required tests, each against a fake HTTP server:
  1. `start` prints exactly the three lines, writes a 0600 pending file, exits 0 without polling.
  2. `wait` through `authorization_pending`, `slow_down` (next sleep is longer by 5 s), then 200: `client.toml` is 0600 with the response endpoint, pending file gone, exit 0, stderr has `wrote` and `tenant:`.
  3. `access_denied` and `expired_token` each exit 1 and delete the pending file.
  4. `wait` with no pending file exits 1.
  5. No stdout or stderr from either command contains the token or `device_code`.
  6. No flag and no config: `start` requests `https://api.yakka.build/v1/device/code` (inject the opener or transport; do not hit the network). With `client.toml` naming an endpoint, that is used.
  7. `login` with `YAKKA_LOGIN_BROWSER` set to a recorder script prints the three lines, the recorder receives `verification_uri_complete`, and the command completes; with a failing opener it still completes.
  8. A 404 from `/v1/device/code` gives exit 1 and the "no device login" line. A second `start` replaces the pending file.
  9. Keep the surviving tests that still apply (`normalize_origin` userinfo stripping, re-login tightening the config mode). Drop the exchange and `device_page_url` tests.

### Keep untouched

`write_client_config` and the config reading used by drain/ingest, `run_status` (Phase 4 changes it), `packages/yakka/internal/clientconfig`, the server, the Pages package, `DESIGN.md`.

## Done evidence

- `python3 -m unittest plugins/yakka/client/test_login.py` (use the invocation the repo already uses for this file) passes with all nine groups above.
- The other Python client tests still pass (find them next to `test_login.py`), and `python3 tools/release/test_release.py` (or its documented runner) passes.
- `cd packages/yakka && go build ./... && go vet ./cmd/... && go test -count=1 ./cmd/... ./internal/...` passes. Go is at `/home/codyh/.local/go/bin/go`.
- `grep -rn "device_page_url\|_login_exchange\|internal/login" plugins packages tools` finds nothing.
- `./plugins/yakka/bin/yakka login wait` with `YAKKA_CLIENT_CONFIG` pointing at an empty temp dir exits 1 with one stderr line.

## Report back

`docs/plans/19-device-login/reports/phase3-client-login.md`: what was done against the brief with test results; every departure and why; unfinished or deferred work; known problems. Phase 1's carried note applies: do not add a combined slow_down sequence against the real server. Final message: commit hash, test results, departures, under 200 words. If the brief contradicts the code or the design, record it in the report; do not work around it silently.
