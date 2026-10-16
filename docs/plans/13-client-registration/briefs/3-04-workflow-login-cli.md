# Brief: 3-04 — workflow login CLI

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 3.
Owned paths: `tools/workflow/internal/login/login.go` (new package), `tools/workflow/internal/login/login_test.go`, `tools/workflow/cmd/workflow/main.go` (`login` subcommand only), `tools/workflow/cmd/workflow/login_test.go` (new), `docs/plans/13-client-registration/reports/3-04-workflow-login-cli.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/3-04-workflow-login-cli.md` and include it in the commit.
Depends on: 3-02.
Runs alongside: 3-03 (after 3-02 lands).
Budget: 12 files to read, about 700 lines to change including tests, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Client presentation (`workflow login` flags, loopback listener, browser, exchange, `client.toml` write).
2. `docs/plans/13-client-registration/reports/3-02-device-auth-server.md` — exchange request/response (read after 3-02 lands).
3. `tools/workflow/internal/clientconfig/clientconfig.go` — `Path`, file format, mode 0600 expectation.
4. `tools/workflow/cmd/workflow/drain_test.go` — building binary, temp config path via `WORKFLOW_CLIENT_CONFIG`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Implement `workflow login` so a person at a device opens the collector device page, completes the flow in the browser, and the CLI exchanges the one-time code for the token and writes `endpoint` and `key` into `client.toml` without printing the secret.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Client presentation**

- "`workflow login` is how a person at a device points a client at the collector."
- "`workflow login` takes an optional `--endpoint` (the collector origin, no path). When the flag is omitted, the `endpoint` already in `client.toml` is used. When the flag is omitted and there is no endpoint, the command exits without writing a key."
- "The command listens on loopback and opens the system browser to the collector's device page, carrying `state` and that loopback redirect. If the browser has no session, the collector sends it through GitHub login and back to the device page, not to `/`."
- "The CLI checks `state`. Its exchange is not a session … The exchange returns the plaintext once … The command writes `endpoint` and `key` into `client.toml` and does not print the token. The code and the token are not logged. Writing the file does not revoke the previous token; that token stays valid until it expires or is revoked."

**Phase 3 outcome (this unit)**

- "`workflow login --endpoint <collector>` opens the browser and, after GitHub auth, returns to the device page."
- "The CLI exchange … writes `endpoint` and `key` into `client.toml` and prints no token."
- "A drain using a `read_write` token from that file delivers. A `read` token from that file leaves ingest 403 … The previous token still authorizes until it expires or is revoked. Quitting the page writes nothing."

## Changes

- Add `workflow login [--endpoint URL]` to `main.go` usage and dispatch.
- Start loopback HTTP server on an ephemeral port; callback path receives `code` and `state`; validate `state` matches generated value; `POST` exchange to collector (3-02); write `client.toml` at `clientconfig.Path()` with `endpoint` = collector origin and `key` = plaintext; file mode 0600; stderr may say success without token body.
- Open browser to device page URL with query params agreed with 3-02/3-03 (`state`, `redirect_uri`, optional `return` for OAuth).
- Missing endpoint when flag omitted and no endpoint in existing file: exit non-zero, no write.
- Tests: httptest collector implementing exchange; simulate callback GET; assert file contents and no stdout token; optional integration with `serve_test` remote server + manual browser skip.
- Do not implement `workflow init`.

### Keep untouched

- `clientconfig` env resolution (3-01) except using `Path()` and write helper.
- Device page Svelte (3-03).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/login/ ./cmd/workflow/ -run Login -count=1` → pass.
- Scripted: after login test writes config, `workflow drain` (or `ConfigSink` test) with `read_write` token ingests against remote fixture; `read` token gets 403 on ingest (may reuse 3-01 patterns).
- `grep` of login package and command: no `fmt.Print` of `wk_` substring in success paths.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
