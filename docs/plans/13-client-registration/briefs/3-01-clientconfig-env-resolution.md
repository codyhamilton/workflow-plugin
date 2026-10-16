# Brief: 3-01 — Client config and env resolution

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 3.
Owned paths: `tools/workflow/internal/clientconfig/clientconfig.go`, `tools/workflow/internal/clientconfig/clientconfig_test.go`, `tools/workflow/internal/drain/cli.go` (only if `RunStandalone` / `RunStatus` need an explicit preflight), `tools/workflow/internal/drain/drain.go` (only if `Run` must fail before the first sink build when env is half-set), `tools/workflow/internal/mcp/mcp.go` or `tools/workflow/internal/mcp/feedback.go` (only if MCP must reject half-set env before any HTTP), `tools/workflow/cmd/workflow/drain_test.go` (env-only remote ingest test), `tools/workflow/cmd/workflow/reads_wiring_test.go` (only if env resolution changes break it), `tools/workflow/internal/mcp/mcp_test.go` (env-only GET test), `docs/plans/13-client-registration/reports/3-01-clientconfig-env-resolution.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/3-01-clientconfig-env-resolution.md` and include it in the commit.
Depends on: phase 2 (closed).
Runs alongside: 3-02.
Budget: 12 files to read, about 350 lines to change including tests, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Client presentation (resolution bullets), Phase 3 outcome (env, file, local mode, half-set env).
2. `docs/plans/13-client-registration/reports/2-01-registry-tenancy-bearer.md` — remote serve and bearer ingest as built.
3. `tools/workflow/internal/clientconfig/clientconfig.go` — current `Load` / `parse`.
4. `tools/workflow/internal/drain/http.go` — `ConfigSink` and bearer header.
5. `tools/workflow/cmd/workflow/drain_test.go` — `newEnv`, `writeConfig`, remote serve pattern.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Implement design 13 client resolution so `WORKFLOW_ENDPOINT` + `WORKFLOW_KEY` override `client.toml`, half-set env is a hard error before any HTTP, and drain / MCP / status use the resolved remote or local mode per the phase 3 outcome.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Client presentation**

- "`WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` both set: remote mode, those values. They win over `client.toml`."
- "Exactly one of them set: bad config. `workflow drain`, `workflow mcp`, and `workflow status` fail before any request. They do not use `client.toml` and they do not contact loopback."
- "Neither set, and `client.toml` present: `endpoint` and `key` as today."
- "Neither set, and no file: local mode, `http://127.0.0.1:8770`, no bearer."
- "`WORKFLOW_CLIENT_CONFIG` still overrides only the file path."
- "The drain's ingest request stays `POST <endpoint>/v1/ingest` with `Authorization: Bearer <key>` when the resolved key is non-empty. The MCP shim's GETs use the same resolution."
- "A hand-written `client.toml` (`endpoint`, `key`) still works."

**Phase 3 outcome (this unit)**

- "With `WORKFLOW_ENDPOINT` set to the collector and `WORKFLOW_KEY` set to a live `read_write` token, and with no `client.toml`, `workflow drain` delivers a spooled fact (`POST /v1/ingest` succeeds) and `workflow mcp` reads with that bearer."
- "A `client.toml` of `endpoint` and `key`, with those two env vars unset, does the same."
- "Neither file nor env is local mode and sends no bearer."
- "Setting exactly one of `WORKFLOW_ENDPOINT` or `WORKFLOW_KEY` makes `workflow drain`, `workflow mcp`, and `workflow status` fail before any request; they do not use the file and they do not contact loopback."

## Changes

- Extend `clientconfig.Load` (or a single exported helper it calls) to apply env precedence: both env vars → remote with those values and ignore file contents; exactly one env var → return a distinct error that does not mention the key value; neither → existing file / missing-file behavior.
- Ensure `workflow drain` and `workflow status` surface half-set env as a non-zero exit before opening the queue to the network (drain) or before `GET /v1/health` (status). MCP may fail on first tool that needs HTTP, but must not contact loopback when env is half-set.
- Add integration tests: remote OAuth serve (pattern from `serve_test.go` / phase 2 e2e) with a registry-seeded `wk_` token; drain with env only (no `client.toml`) ingests; MCP `list_checks` or similar GET sends bearer; half-set env exits drain/status without HTTP to 127.0.0.1:8770.
- **Carried item 1 (tenant on other analytics routes)**: out of scope — do not change `packages/workflow-analytics` routes other than what other units own.
- **Carried item 2 (`Server.New` panic)**: out of scope — do not change registry open/persist failure behavior.

### Keep untouched

- `workflow login` command (unit 3-04). Device page and device-code routes (unit 3-02).
- OAuth, session, token issue handlers except what tests need to seed tokens.
- `LocalEndpoint` constant and local-mode semantics when no file and no env.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/clientconfig/ -count=1` → pass, including new env precedence and half-set cases.
- `cd tools/workflow && GOTOOLCHAIN=auto go test ./cmd/workflow/ -run 'Drain|Env|Client' -count=1` (or the specific new test names you add) → pass, including env-only drain ingest and half-set env refusal.
- `cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/mcp/ -count=1` → pass, including env-only bearer GET when applicable.
- Observable: with only `WORKFLOW_ENDPOINT` set, `workflow status` prints a config error and does not print `endpoint: http://127.0.0.1:8770`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
