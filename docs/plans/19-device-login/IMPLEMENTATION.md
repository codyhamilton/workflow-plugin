# Implementation: Device-code login

## Run

- Tool: Claude Code (Haiku 5.5 orchestrator)
- Session: https://claude.ai/code/session_01DNryxkjkbPeSkJztoo7ZHk
- Start: 2026-10-21T00:38:00+10:00
- Branch: feat/device-login (from master at 6576c04)
- Invocation: `/yakka:execute plan 19`, bare call, so one phase (Phase 1) and then stop.

## Phase 1 — Device grant on the server

Status: closed, 2026-10-21 (closing commit carries `Yakka-Phase: 19-device-login:1`).

Refine verdict: READY, two units, sequential (both edit `device.go`). Briefs in `briefs/`, committed at 231d7f4.

Units:
1. `phase1-grant-flow` (no dependencies). Worker: Sonnet.
2. `phase1-limits` (depends on 1). Worker: Sonnet.

### Unit `phase1-grant-flow`

Dispatched 2026-10-21T00:42+10:00. Outcome: landed at 2732955. Worker report: `reports/phase1-grant-flow.md`.

- Built: in-memory grant table (`device_grants.go`), `ValidateGrant`, the three device routes, removal of `/v1/device/exchange`, legacy `device_codes` revoke-on-load in `registry.go`.
- Surfaces: `device.go`, `device_grants.go` (new), `device_test.go` (new), `registry.go`, `serve.go`, `serve_test.go` (old flow test removed).
- Deviations, from the worker report: authorize returns 400 for `redirect_uri`/`state`; an unknown `action` returns 400; a non-JSON body on `/v1/device/code` returns 400. The brief's `TestDeviceGrantSlowDown` sequence conflicts with its own poll rule (a poll 6 s later is itself `slow_down`), so the two cases are tested on separate grants.
- Known: if `Persist` fails after a grant is dropped, the user gets 500 and must log in again.
- Agent: sonnet worker, turns and context not reported by the harness.

### Unit `phase1-limits`

Dispatched 2026-10-21T00:44+10:00, after `phase1-grant-flow`. Outcome: landed at bf974e5. Worker report: `reports/phase1-limits.md`.

- Built: per-IP code-request rate (10/min), per-IP live-grant cap (5), global pending cap (1,000), unknown-code attempt limit (10 per session per 10 min), client-IP rule (`Fly-Client-IP` only when `FLY_APP_NAME` is set), 429 and 503 paths. In `device_limits.go` and `device_limits_test.go`.
- Surfaces: `device.go` hook points, `device_limits.go` (new), `device_limits_test.go` (new).
- Deviations, from the worker report: no departures from the contract. Authorize checks the session limit before the lookup, so a valid code also gets 429 while the session is limited. The brief's "rejected attempts count" rule was read as every attempt counting.
- Agent: sonnet worker, turns and context not reported by the harness.

### Verification (Phase 1)

- Entry point: the served device routes through the `internal/serve` handler, exercised by `go test -count=1 ./internal/serve/...` (ok) and `go test -run TestDevice -v` (17 PASS, including `TestDeviceGrantFlow`, `TestDeviceGrantDeny`, `TestDeviceExchangeRemoved`, `TestDeviceNoPlaintextAtRest`, `TestDeviceCodeRateLimit`, `TestDeviceCodeLiveCapPerIP`, `TestDeviceClientIP`).
- `go build ./...` passes, so `internal/login` still builds (it is deleted in Phase 3).
- Result: the phase outcome holds on the server side. The mint-on-poll flow, slow_down, access_denied, expired_token, the 429/503 limits, the removed `/exchange` route and the no-plaintext-at-rest check all pass in the served handler.

### artifact_feedback

Called on both reports and both briefs at closing. Result for all four: "not delivered" (the service has no version of the files and nothing is queued). Recorded here and the run continues, per the execute contract.

### Phase 1 — Carried

1. The brief's `TestDeviceGrantSlowDown` sequence conflicts with its own poll rule (a poll 6 s after a `slow_down` is itself `slow_down`). The two cases are tested on separate grants. The Phase 1 outcome still holds. Phase 3 should keep the rule and not add a combined sequence.
2. `DESIGN.md` Surfaces names `serve.go (sweep)`, but no sweep exists in `serve.go`. The Contract says there is no background loop, so expired grants are swept inside the grant table. Amend the Surfaces line in the design when Phase 4's docs are written.
3. Persist failure after a grant is dropped returns 500, and the user has to log in again. Accepted; the design's restart cost already covers it. A later refine may choose to leave the grant in place on a failed persist.
4. Authorize's session limit runs before the code lookup, so a valid code gets 429 while the session is limited. The design does not state the order. Accepted for now.
5. `device_codes` revoke-on-load and the sweep are covered by tests, not by a real `registry.json` from the deployed service. Check against production state before the Phase 3 deploy.

## Phase 2 — User-code approval page

Status: closed, 2026-10-21 (closing commit carries `Yakka-Phase: 19-device-login:2`). Run: Claude Code (Sonnet 5.5 orchestrator), session https://claude.ai/code/session_01DNryxkjkbPeSkJztoo7ZHk, start 2026-10-21 (bare `/yakka:execute phase 2`, so this phase only).

The phase is one unit, so one brief was authored inline from the design's contracts: `briefs/phase2-approval-page.md`, committed before dispatch. Worker: Sonnet.

### Unit `phase2-approval-page`

Dispatched 2026-10-21T00:52+10:00 after the brief commit (`ddd8922`). Outcome: landed at 9408618. Worker report: `reports/phase2-approval-page.md`.

- Built: `/device` rewritten as a user-code page. `?user_code=` prefills; no parameter shows an entry field; signed out shows the sign-in link with `user_code` in its return URL; signed in shows the code in large type with the "check this matches" text, tenant/scope/expiry choices, Approve and Deny through a credentialed `fetch` (`approveDevice`, `denyDevice` via `apiPost`). `state` and `redirect_uri` are ignored. `isValidLoopbackRedirectUri` and `deviceAuthorizeAction` removed.
- Surfaces: `src/routes/device/+page.svelte`, `src/lib/api.ts`, `src/lib/api.test.ts`, `tests/e2e/device.spec.ts`.
- Deviations, from the worker report: `sessionRoute` in `api.ts` now includes `device/`, otherwise a stored bearer key would replace the cookie and the call would not send credentials. No separate `deviceAuthorizeUrl` helper; `apiPost` already resolves the host and base. Deny renders outside the tenant form when the user has no tenant.
- Known: Playwright cannot read the fetch `credentials` mode, so the e2e test seeds a cookie and checks the mocked request carries it.
- Agent: sonnet worker, turns and context not reported by the harness.

### Verification (Phase 2)

- Entry point: the `/device` page in the built dev server with a mocked API. `npx playwright test tests/e2e/device.spec.ts`: 8 passed (code shown and Approve gated; one credentialed authorize fetch and "Approved"; Deny; 404 error; entry field; sign-in return URL keeps `user_code`; `state`/`redirect_uri` ignored; no `wk_`). Run by the runner, not only the worker.
- `npm test` (vitest): 196 passed.
- `grep` for `redirect_uri`, `isValidLoopback`, `deviceAuthorizeAction` in `src`: no matches.
- Result: the phase outcomes hold against the mocked API. Not checked: the page against the real Phase 1 server.

### artifact_feedback (Phase 2)

- Report `phase2-approval-page`: "not delivered" (the service has no version of the file).
- Brief `phase2-approval-page`: delivered, screen pass. Below the baseline 25th percentile: `b.keep_untouched` 0.39, `b.goal_is_outcome` 0.42, `b.ac_why` 0.23. The brief was authored inline; the unit finished without trouble.

### Phase 2 — Carried

1. The page is only verified against a mocked API. Phase 4's outcome (a real `/yakka:login` against the deployed service) is the first check against the real server. Run one authorize call against a local `yakka serve` before the Phase 3 deploy if a cheaper early check is wanted.
2. `api.test.ts` has one `svelte-check` error (`err` is of type `unknown`) that exists on the unchanged tree. Not this plan's.
3. The deploy order in the design puts Pages after the Fly server; this phase only changes source. Carry the Pages deploy to Phase 4.
4. From Phase 1, still open: the `serve.go (sweep)` Surfaces line, and the check against a production `registry.json`.

## Phase 3 — Two-step client login

Status: closed, 2026-10-21 (closing commit carries `Yakka-Phase: 19-device-login:3`). Run: Claude Code (Sonnet 5.5 orchestrator), session https://claude.ai/code/session_01DNryxkjkbPeSkJztoo7ZHk, start 2026-10-21 (bare `/yakka:execute phase 3`, so this phase only).

The phase has no Units list. Python client rewrite plus Go login deletion is one worker's work, so one brief was authored inline: `briefs/phase3-client-login.md`, committed before dispatch. Worker: Sonnet.

### Unit `phase3-client-login`

Dispatched 2026-10-21 after the brief commit (`44cfecd`). Outcome: landed at 4842779. Worker report: `reports/phase3-client-login.md`.

- Built: `login start`, `login wait` and a composed `login` in `yakka.py`; default endpoint `https://api.yakka.build`; loopback code removed; `internal/login` deleted; Go `login` exits 1 naming the plugin wrapper.
- Deviations, from the worker report: the Go usage string drops `login`; `wait` sleeps one interval before the first poll; `resolve_endpoint` (login-only) now returns the default instead of an error; network errors, 429 and 5xx are retried until expiry.

### Verification (Phase 3)

- `test_login.py`: 17 passed (run by the runner, from `plugins/yakka/client`: `python3 -m unittest test_login`).
- Go `build`, `vet` and `./internal/...` pass. `./cmd/...` fails only `TestHalfSetEnvRefusal` (port 8770 held by an unrelated process); it fails the same way on master `6576c04`.
- grep for the loopback names finds nothing; `login wait` with an empty config exits 1 with one stderr line.
- `tools/release/test_release.py`: 9 of 10 pass. `test_7_build_sh` fails with `go: go.mod requires go >= 1.27.1 (running go 1.24.2; GOTOOLCHAIN=local)`. Read by running the test in a throwaway git worktree (build.sh deletes the tracked `site/` directory, so it is not run in the main tree). The only Go on this machine, `~/.local/go/bin/go`, is 1.24.2, and the test pins `GOTOOLCHAIN=local`. `go.mod`, `go.sum` and `build.sh` are unchanged since `6576c04`, so the failure is environmental and not from this phase. (The worker's report says 10 of 10 passed; it ran with a Go the test could use, so that claim is not reproduced here.)
- Result: the phase outcome holds. Client login is two commands against the fake server, the default endpoint is set, and the loopback login is gone from the client and the Go binary. Not checked: against the real Phase 1 server.

### artifact_feedback (Phase 3)

- Report `phase3-client-login`: "not delivered" (the service has no version of the file).
- Brief `phase3-client-login`: delivered, screen pass. Below the baseline 25th percentile: `b.fail_first` 0.42, `b.done_covers_goal` 0.34, `b.ac_why` 0.15, `b.ac_proven_required` 0.60. The brief was authored inline; the unit finished without trouble.

### Phase 3 — Carried

1. `test_release.py::test_7_build_sh` needs Go >= 1.27.1 with `GOTOOLCHAIN=local`; this machine has 1.24.2. Run it where that Go exists before the Phase 4 release.
2. `TestHalfSetEnvRefusal` needs port 8770 free; an unrelated process holds it here.
3. The Go usage string and the wrapper's differ by design (Go drops `login`). Phase 4's docs should say the wrapper owns login.
4. `wait` sleeps one interval before the first poll, so it needs a full interval after `start` even if the user approved at once. Accepted.
5. Not checked against the real server: the `start`/`wait` pair, and the Phase 2 page. Phase 4's real `/yakka:login` is the first such check.
6. From earlier phases, still open: the `serve.go (sweep)` Surfaces line, the check against a production `registry.json` for legacy `device_codes`, and the Pages deploy (Phase 4).

## Phase 4 — Login skill, docs and release

Status: closed, 2026-10-21 (closing commit carries `Yakka-Phase: 19-device-login:4`), with the live check carried to after merge by the user's decision. Run: Claude Code (Sonnet 5.5 orchestrator), session https://claude.ai/code/session_01DNryxkjkbPeSkJztoo7ZHk, start 2026-10-21 (`/yakka:execute phase 4 and complete`: this phase, then wrap-up).

One code unit, authored inline: `briefs/phase4-skill-docs-release.md`. Worker: Sonnet. The Fly deploy, the Pages deploy and the live `/yakka:login` check are outward-facing and are the runner's, after the user confirms.

### Unit `phase4-skill-docs-release`

Outcome: landed at 03b85a8. Worker report: `reports/phase4-skill-docs-release.md`. Worker: Sonnet.

- Built: `skills/login/SKILL.md`; `run_status` prints `config: env (remote mode)`; plugin `3.1.0` in the three `plugin.json` files; `bin/VERSION` `0.3.0`; marketplace and `install.sh` lists gain `login`; designs 03, 05, 07, the Phase 1 Surfaces line and `CHANGELOG.md` updated.
- Deviations: the marketplace entries have no version field, so only descriptions changed. Plugin and binary versions are separate series, so the "bump together" line was not followed literally. The worker ran the full `test_release.py` including `test_7_build_sh`, against the brief; the runner found no tracked file changed (`git status` clean, `site/index.html` present).

### Verification so far (Phase 4)

- Run by the runner: `test_status` + `test_login` 20 OK; the three `plugin.json` at 3.1.0, `VERSION` 0.3.0; the skill exists. `test_layout.py` 6 of 7: the failure lists `packages/yakka-analytics/node_modules/**` (git-ignored, local), not checked on master.
- Not done: the Fly deploy, the Pages deploy and the live `/yakka:login` outcome. These publish to production and wait for the user's go-ahead. The phase is therefore not closed and carries no trailer.

### Fly deploy (Phase 4)

Deployed by the runner on the user's instruction ("deploy the service"). One machine rolled and passed health checks. Against `https://api.yakka.build`: `/v1/health` 200; `POST /v1/device/code` returned a user code, `verification_uri` and timings; `POST /v1/device/exchange` 404. Startup logs show no error. The legacy `device_codes` revoke path was not exercised by a log line, so the production `registry.json` check stays carried.

### artifact_feedback (Phase 4)

- Report `phase4-skill-docs-release`: "not delivered" (the service has no version of the file).
- Brief `phase4-skill-docs-release`: delivered, screen pass. Below the baseline 25th percentile: `b.done_covers_goal` 0.30, `b.ac_why` 0.31, `b.ac_judgement_labelled` 0.32.

### Phase 4 — Carried

1. Pages deploys on merge to master (user's decision). Until then the live `/device` page is the old loopback form, and no login can finish end to end.
2. The live outcome is unverified: in Claude Code, `/yakka:login` against `api.yakka.build` after merge and the plugin update, with `config: …/client.toml (remote mode)`, `endpoint: https://api.yakka.build reachable` and no `wk_` in the transcript. The user chose to verify after merge; the plan folder is collapsed by `close-out` after that.
3. `test_layout.py::test_repo_passes_layout_check` fails on git-ignored `packages/yakka-analytics/node_modules/**`; not checked on master.
4. `test_7_build_sh` needs Go >= 1.27.1; `TestHalfSetEnvRefusal` needs port 8770.
5. The production `registry.json` check for legacy `device_codes`.
6. Plan 18 must be revised to the Python `start`/`wait` client before it is built.

## Pre-flight (pipeline posture)

Posture: pipeline, by the user's decision (PR now, verification and close-out after merge). No `REVIEW.md`.

- Builds: Go build and vet pass (Phase 3), Playwright 8 and vitest 196 pass (Phase 2), Python client tests pass (Phases 3 and 4).
- Phase outcomes 1 to 4 hold as recorded above; Phase 4's live outcome is carried.
- Folder: `DESIGN.md`, `IMPLEMENTATION.md`, `PROVENANCE.md`, briefs and reports for every phase are present.
