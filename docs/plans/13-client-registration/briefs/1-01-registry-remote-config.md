# Brief: 1-01 — Registry and remote mode config

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 1.
Owned paths: `tools/workflow/internal/serve/registry.go`, `tools/workflow/internal/serve/registry_test.go`, `tools/workflow/internal/serve/serve.go` (only `Config`, `ConfigFromEnv`, `ParseKeys`, `Server` fields needed for the registry, `New`, and `Local`/`Remote` helpers — do not register OAuth routes or change `auth` yet), `tools/workflow/internal/serve/serve_test.go` (config and registry tests only), `tools/workflow/cmd/workflow/main.go` (startup refusal when `WORKFLOW_SERVE_KEYS` is non-empty), `docs/plans/13-client-registration/reports/1-01-registry-remote-config.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/1-01-registry-remote-config.md` and include it in the commit.
Depends on: nothing.
Runs alongside: nothing.
Budget: 8 files to read, about 450 lines to change including tests, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Identity and admission (contract bullets), Domain: Request authorization (first two bullets on loopback and `WORKFLOW_SERVE_KEYS`), Phase 1 outcome (first two sentences on startup).
2. `tools/workflow/internal/serve/serve.go` — `Config`, `ConfigFromEnv`, `ParseKeys`, `Local`, `Handler` (read only how `Local()` gates `localGuard`).
3. `tools/workflow/cmd/workflow/main.go` — `runServe`.
4. `tools/workflow/internal/serve/serve_test.go` — `TestLocalModeConfig`, `TestParseKeys`.
5. `tools/workflow/cmd/workflow/main_test.go` — `TestServeOutcome` (keys vs loopback).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Persist the collector registry (policy and session records) under `WORKFLOW_SERVE_DATA`, and make `ConfigFromEnv` distinguish local loopback mode from remote collector mode with the OAuth env required on non-loopback binds. Refuse to start when `WORKFLOW_SERVE_KEYS` is set.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

- Identity and admission: "The collector is registered as one GitHub OAuth app. The process reads `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET`, and `WORKFLOW_PUBLIC_URL` (https origin, no path). Those three are required when the bind is not loopback … A loopback bind is always local mode, including when all three are set: they are ignored, and the process still serves tenant `local` with no keys."
- Identity and admission: "Domain policy is one collector-wide record: `everyone`, or `allow_list` plus a set of domains. Default when no record exists: `everyone`."
- Tenancy and tokens (registry placement only): "The registry (owners, token hashes, policy, sessions' github id, github login, and verified emails) lives under `WORKFLOW_SERVE_DATA`, outside any tenant directory. … Restart loads the registry from that directory."
- Request authorization: "Loopback is always local mode, whether or not the OAuth env is set. … `WORKFLOW_SERVE_KEYS` set to anything but empty makes the process exit before it listens, on loopback or not, and the error names that variable."

Decisions for this unit (settled; later units build on them):

- **`Config.Remote()`** is true when the bind is not loopback and all three OAuth env vars are non-empty after trim. **`Config.Local()`** is true on any loopback bind (OAuth env ignored) or when remote prerequisites are missing (non-loopback without full OAuth env is a `ConfigFromEnv` error, not local mode).
- **`WORKFLOW_SERVE_KEYS`**: any non-empty value after trim makes `workflow serve` exit before listen with an error whose text includes `WORKFLOW_SERVE_KEYS`. Do not load keys into `Config.Keys` in remote mode; keyed mode via env is removed. Keep `ParseKeys` and existing keyed tests only where they still document parsing errors, but production startup must not accept keys.
- **Registry files** live directly under `cfg.Data` (not inside `<tenant>/`). Use a stable on-disk layout you document in the `registry` package comment. Phase 1 needs load/save of: domain policy (`everyone` | `allow_list` + domains), and session records keyed by opaque session id (github id, login, verified emails, expiry). Token hashes and tenant owners may be empty structures until phase 2 but the registry type should reserve them.
- **`Server`** holds a `*Registry` opened in `New` from `cfg.Data`; close or flush on `Server.Close` if needed.

## Changes

- Add `registry.go` with load/create, policy get/set, and session CRUD sufficient for later OAuth work.
- Extend `Config` with `PublicURL`, OAuth client id/secret fields populated only when `Remote()` would be true.
- Replace `ConfigFromEnv` rules: loopback → local, no OAuth required; non-loopback → require OAuth trio; non-empty `WORKFLOW_SERVE_KEYS` → error from `ConfigFromEnv` or `runServe` before listen (error must name `WORKFLOW_SERVE_KEYS`).
- Wire registry into `New`.
- Do not add routes, change `auth`, or alter `localGuard` behavior yet beyond what `Local()` already implies.

### Keep untouched

- Ingest, analytics handlers, CORS, `tenantForKey`, and keyed-mode HTTP tests that still use `New(Config{Keys: …})` in test constructors (tests may construct keyed servers without `ConfigFromEnv` until phase 2 removes keyed remote mode entirely).
- `tools/workflow/internal/serve/site.go` and the embedded site tree.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && go test ./internal/serve/ -run 'TestLocalModeConfig|TestRegistry|TestRemoteConfig' -count=1` → pass (add `TestRegistry` and extend config tests for OAuth-required non-loopback, loopback+OAuth ignored, and `WORKFLOW_SERVE_KEYS` refusal).
- `cd tools/workflow/cmd/workflow && go test -run TestServeOutcome -count=1` → pass after updating expectations: non-empty `WORKFLOW_SERVE_KEYS` must refuse start even on loopback; document any change to the wildcard-bind no-keys case per the new contract.
- Observable: creating a server with `Remote()` config on a temp data dir leaves a registry file under the data dir; policy defaults to `everyone` when absent.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
