# Plan 13 review

Terminal review of client registration against `DESIGN.md`, read at `34b8669` (phase 4 closed). One reviewer. No fixer pass: there is no blocker and no in-scope high finding.

## Verdict

**PASS_WITH_FOLLOWUPS.**

## Reviewed SHA

`34b86695cad091679a41654fe80a12e8a8390bd2`

The hosting sentence that said the fly app already lists a Pages origin was wrong. There is no Cloudflare Pages site, and `WORKFLOW_SERVE_CORS_ORIGINS` is unset. That sentence in design 7 was corrected in the review commit. It is mechanical and matches the hosting contract's "if still used".

## Phase outcome assessment

| Phase | Assessment |
|---|---|
| 1. GitHub login and admission | Met. Remote serve refuses `WORKFLOW_SERVE_KEYS` and a missing OAuth env. Session, denial, policy, and bearer-only ingest are covered by `serve_test.go` and the phase 1 verification record. |
| 2. Issued tokens are the remote credential | Met. Profile issue, `wk_` scrub, read vs read_write, revoke, expiry, and registry reload are in the phase 2 verification record and the serve tests. |
| 3. Devices and remote agents present a token | Met. Env-pair resolution, device authorize/exchange, the device page, and `workflow login` are in the phase 3 verification record. The GitHub round trip was not driven against github.com; the session was seeded. That matches the record and does not miss the outcome's observable steps. |
| 4. The collector runs on fly.io | Met. App `yakka` serves `https://yakka.build`: health 200, `/oauth/login` redirects to GitHub with callback `https://yakka.build/oauth/callback`, `WORKFLOW_SERVE_KEYS` unset, and a `read_write` token ingested after a machine restart while a token revoked before it stayed 401. There is no Pages site, so the browser-origin CORS check is not applicable and `WORKFLOW_SERVE_CORS_ORIGINS` stays unset. `https://yakka.fly.dev` was not the close condition. |

## Findings by severity

### Blocker

None.

### High

None.

### Medium

1. **A device code keeps the token plaintext in `registry.json` until exchange.** The tenancy contract says the registry stores the SHA-256, not the plaintext. Phase 3 kept the plaintext so a restart can still redeem the code, then deletes it on exchange. Follow-up. Fixing it needs a restart story, not a local edit.
2. **`/oauth/login?return=` allows a path that starts with `/` and does not reject `\`. The callback trusts the cookie without checking again.** A `/\` return can become an open redirect in browsers that normalize the backslash. The session cookie is host-only, so this does not hand the cookie to the other site. Follow-up.

### Low

3. Collector-mode `?tenant=` is still only on `/` and `/profile`. Design 7 already says so. The phase outcomes proved the overview, not every report route.
4. `Server.New` panics if the registry cannot be opened or persisted.
5. Analytics e2e seeds `registry.json` instead of logging in and calling `POST /v1/tokens`.
6. The profile expiry field is prefilled in the browser. The device page is not, and the server has no default.

These four were carried on purpose through phases 2–4. They are follow-ups, recorded as open issue 13 in design 7.

## Intent and ledger

The implementation matches the request: GitHub login, issued tokens, `workflow login` into `client.toml`, and one fly.io collector at `https://yakka.build`. The product, CLI, and packages stay `workflow`. The Fly app is `yakka`.

The assumption ledger is empty. The hosting contract's "Pages, if still used" still holds: it is not used, and the CORS secret is unset.

## Plan sufficiency

The design was enough to place the work and to judge the outcomes. The Pages CORS sentence assumed an origin the operator later said does not exist. The "if still used" clause made that a non-event rather than a redesign. QA for phases 1–3 is the recorded tests; phase 4's QA is the live origin transcript. No separate QA script was required to see that the origin answers.

## Residual risks

- The collector is one machine and one volume. A lost volume loses the registry and the ledgers. There is no second replica, by design.
- Cloudflare sits in front of `yakka.build`. SSL must stay Full (strict). Flexible loops because port 80 redirects to HTTPS.
- `artifact_feedback` never scored the briefs or reports. The quality service was not running.
