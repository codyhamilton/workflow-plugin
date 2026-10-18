# Review — client registration

## Verdict

`PASS_WITH_FOLLOWUPS` at reviewed SHA `1e3fb56`.

## Phase outcomes

| Phase | Assessment |
| --- | --- |
| 1 — GitHub login and admission | met |
| 2 — Issued tokens | met |
| 3 — Devices and remote agents | met |
| 4 — fly.io collector | met (live restart check recorded in plan; not re-run this review) |

## Findings

### Resolved in review

- **OAuth return open redirect (high)** — `oauthReturnPath` / `cookieOctets` on login and callback; `TestOAuthReturnStaysOnOrigin`. Commit `1e3fb56`.

### Follow-up (non-blocking)

- **medium** — Device codes hold plaintext until exchange; TTL follows API token expiry (design 7 issue 18).
- **low** — `Server.New` panics on registry open/persist failure (issue 18).
- **low** — Collector `?tenant=` only on overview and `/profile` (issue 18).
- **low** — Profile expiry `datetime-local` vs UTC label; profile prefilled expiry (issue 18).
- **low** — `ExchangeDeviceCode` without revoked check; login CLI trusting exchange endpoint origin.

## Intent and ledger

Implementation matches `docs/plans/13-client-registration.md` and design 3/7. Session is not a bearer; ingest is bearer-only; `WORKFLOW_SERVE_KEYS` refused on remote serve.

## Plan sufficiency

The plan and linked design docs were enough to place findings and judge phase outcomes.

## Residual risks

Single-machine collector and volume durability remain as documented in the plan close-out.

## Tests

`go test ./...` under `tools/workflow` (all packages pass, including `internal/serve` and `internal/login`).
