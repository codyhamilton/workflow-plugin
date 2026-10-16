# Brief: 4-03 — Fly collector outcome verify

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 4.
Owned paths: `docs/plans/13-client-registration/reports/4-03-fly-collector-outcome-verify.md` only. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title (report-only commit is fine).
Report: before committing, write `docs/plans/13-client-registration/reports/4-03-fly-collector-outcome-verify.md` and include it in the commit.
Depends on: 4-02 (live public origin and deploy handoff).
Runs alongside: 4-04 (disjoint paths).
Budget: 10 files to read, about 20 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Phase 4 outcome; Domain: Collector hosting (restart and CORS); Domain: Request authorization (`WORKFLOW_SERVE_CORS_ORIGINS`, no credentialed CORS).
2. `docs/plans/13-client-registration/reports/4-02-fly-collector-deploy.md` — public origin, CORS Pages origin, app name.
3. `tools/workflow/internal/serve/serve_test.go` — `TestCORSKeyedMode` / `assertCORS` / `assertNoCORS` (expected CORS header shape on allowed vs disallowed origins).
4. `docs/plans/13-client-registration/IMPLEMENTATION.md` — Phase 2 verification notes on registry restart (local precedent).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Prove the phase 4 runtime outcome on the deployed fly collector: health and OAuth entry, token persistence across a machine restart, revocation persistence, and bearer CORS for the Pages origin without credentials.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Phase 4 outcome**

- "A `read_write` token that ingested before a machine restart ingests into the same tenant after it, and a token revoked before the restart does not."
- "With `WORKFLOW_SERVE_CORS_ORIGINS` set to the Pages origin, a browser on that origin can `GET /v1/analytics/summary` with a bearer, a browser on any other origin cannot, and the response has no `Access-Control-Allow-Credentials`."

**Domain: Collector hosting**

- "After a restart, a token that was valid before the restart still authorizes, and a token revoked before the restart still does not."

**Domain: Request authorization**

- "Remote mode still honors `WORKFLOW_SERVE_CORS_ORIGINS` for bearer reads: the exact origins listed, no wildcard, and no `Access-Control-Allow-Credentials`."

## Changes

- On the **live** collector origin from 4-02, obtain two issued tokens for the same tenant (or one `read_write` and one revoked) using **session APIs** (`POST /v1/tenants`, `POST /v1/tokens` with a future `expires_at`) or an existing admin session — not by committing plaintext to the repo. Redact tokens in the report except last four characters.
- **Ingest** once with a live `read_write` bearer (`POST /v1/ingest`); record tenant and a distinguishing fact id or path.
- **Revoke** a second token (or the same token after a separate ingest check) before restart; confirm next ingest with that bearer is `401` and stores nothing.
- **Restart** the fly machine (`fly machines restart` or `fly apps restart` per fly docs); wait until health is `200` again.
- After restart: the **non-revoked** `read_write` token still ingests into the **same tenant**; the **revoked** token still returns `401` on ingest.
- **CORS**: against the live host, issue `GET /v1/analytics/summary?tenant=<t>` with `Origin: <Pages origin>` and `Authorization: Bearer <read token>` → `200` with `Access-Control-Allow-Origin` equal to that exact origin and **no** `Access-Control-Allow-Credentials`. Repeat with a different origin (e.g. `https://evil.example`) → no `Access-Control-Allow-*` headers on the response (or no CORS allowance per `assertNoCORS` semantics).
- Do not change fly env except toggling `WORKFLOW_SERVE_CORS_ORIGINS` if 4-02 left it unset — set it to the real Pages origin for the CORS checks and note the value in the report.

### Keep untouched

- Repo product code and `fly.toml` unless CORS env must be set on fly to satisfy outcome (then only via `fly secrets set` / `fly config` and document in report; prefer manifest update in a follow-up only if orchestrator directs).
- **Carried items 1–4**: out of scope.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- Scripted or logged HTTP transcript (curl) showing: pre-restart ingest `200`/`201` or accepted duplicate; revoked bearer ingest `401`; post-restart live bearer ingest succeeds for same tenant; post-restart revoked bearer `401`.
- CORS transcript: allowed Pages origin shows `Access-Control-Allow-Origin: <Pages origin>` and empty/missing `Access-Control-Allow-Credentials`; disallowed origin shows no ACAO header.
- `curl -sS -o /dev/null -w '%{http_code}' https://<origin>/v1/health` after restart → `200`.

If 4-02 left the app `blocked`, status `blocked` and do not invent local substitutes for fly restart outcome.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
