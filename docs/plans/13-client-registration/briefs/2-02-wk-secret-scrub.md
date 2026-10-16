# Brief: 2-02 — `wk_` workflow token secret scrub

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 2.
Owned paths: `tools/workflow/internal/secrets/secrets.go`, `tools/workflow/internal/secrets/secrets_test.go`, `docs/plans/13-client-registration/reports/2-02-wk-secret-scrub.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/2-02-wk-secret-scrub.md` and include it in the commit.
Depends on: 2-01 (ingest with issued bearer must work for the phase outcome; this unit only adds the pattern).
Runs alongside: 2-03, 2-04 (disjoint paths).
Budget: 6 files to read, about 80 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Tenancy and tokens (scrub bullet), Phase 2 outcome (`wk_` in submitted fact text).
2. `tools/workflow/internal/secrets/secrets.go` — pattern list and `Patterns()`.
3. `tools/workflow/internal/secrets/secrets_test.go` — `samples()`, `TestScanPatterns`.
4. `tools/workflow/internal/ingest/ingest.go` — grep `secrets.Scan` / `Redact` usage (read only).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Treat issued workflow API tokens (`wk_` prefix) as secrets in the shared scrub and precheck pattern set, matching how other credential prefixes are handled.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

- "The client scrub and the server precheck treat the `wk_` prefix as a secret, the same way they treat the other prefixes."

**Phase 2 outcome (this unit)**

- "A submitted fact whose text contains a `wk_` token is stored without that secret."

Decisions for this unit:

- **Pattern name**: `workflow_api_token` (or `wk_token` — pick one stable name listed in `Patterns()`).
- **Regex**: match `wk_` followed by sufficient unguessable body (align with minimum length you expect from 2-01; do not log matches).
- **Redact**: same `[REDACTED:<pattern>]` behavior as existing patterns.

## Changes

- Add one `pattern` entry to `patterns` in `secrets.go`.
- Extend `samples()` in `secrets_test.go` with a representative `wk_` sample; assert `Scan` hits and `Redact` removes the secret substring.
- Optional: one ingest-level test only if it already exists nearby and is a one-liner extension — prefer keeping tests in `secrets_test.go` unless phase outcome needs ingest proof here; phase verification can use ingest from 2-01.

### Keep untouched

- Token issuance and registry (2-01).
- Analytics site (2-03).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/secrets/ -count=1` → pass, including new `wk_` sample in `TestScanPatterns`.
- Observable: `Redact` on a string containing `wk_` + 32+ alnum chars replaces the token segment with `[REDACTED:…]`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
