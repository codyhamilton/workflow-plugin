---
cursor:
  subagentId: "bc-88807259-84db-5de5-935e-f6344b0e49a5"
---

# Report: 4-02 — Fly collector deploy

**Status:** blocked

## What changed

Destroyed the empty app `workflow-collector` in org `ctzns` (no machines, no release). It is gone.

Created app `yakka` in org `ctzns`:

- Volume `workflow_serve_data` id `vol_v3gppxdm66k9gmw4`, region `iad`, 1 GB, encrypted, not attached.
- Dedicated IPv4 `137.66.6.45` (Fly bills this at $2/mo).
- Dedicated IPv6 `2a09:8280:1::1bb:db4d:0`.
- Certificate for `yakka.build`. Status: Not verified. Records to set: `A yakka.build → 137.66.6.45` and `AAAA yakka.build → 2a09:8280:1::1bb:db4d:0`.

`fly.toml` `app` is `yakka`. `fly config validate` passed. No release, no machines, no secrets. `fly deploy` was not run.

The product, CLI, and packages were not renamed. Public origin stays `https://yakka.build`.

## Checks

**Before** (wrong app existed; OAuth env absent; `yakka.build` did not resolve):

```
flyctl apps list -o ctzns
→ workflow-collector

GITHUB_OAUTH_CLIENT_ID
→ absent

GITHUB_OAUTH_CLIENT_SECRET
→ absent

curl -sS -o /dev/null -w '%{http_code}' https://yakka.build/v1/health
→ curl: (6) Could not resolve host: yakka.build
→ 000
```

**After** (`workflow-collector` destroyed; `yakka` created; still no release):

```
flyctl apps list -o ctzns
→ yakka only

flyctl status -a workflow-collector
→ Could not find App "workflow-collector"

flyctl status -a yakka
→ Name yakka, Owner ctzns, Hostname yakka.fly.dev, Image -

flyctl ips list -a yakka
→ v4 137.66.6.45 public ingress (dedicated)
→ v6 2a09:8280:1::1bb:db4d:0 public ingress (dedicated)

flyctl certs show yakka.build -a yakka
→ Status Not verified
→ No AAAA records were found

flyctl secrets list -a yakka
→ empty (no WORKFLOW_SERVE_KEYS)

flyctl machines list -a yakka
→ No machines are available on this app

flyctl config validate -c fly.toml
→ Configuration is valid
→ app = "yakka"

curl -sS -o /dev/null -w '%{http_code}' https://yakka.build/v1/health
→ curl: (6) Could not resolve host: yakka.build
→ 000

curl -sS -D - -o /dev/null https://yakka.build/oauth/login
→ curl: (6) Could not resolve host: yakka.build
```

## Handoff for 4-03

| Item | Value |
|---|---|
| Public origin to prove | `https://yakka.build` (does not resolve; not proven) |
| Fly app | `yakka` in org `ctzns` |
| Volume | `vol_v3gppxdm66k9gmw4` (`workflow_serve_data`, `iad`, unattached) |
| DNS Cody must set | `A yakka.build → 137.66.6.45`; `AAAA yakka.build → 2a09:8280:1::1bb:db4d:0` |
| Pages CORS origin | still unknown; `WORKFLOW_SERVE_CORS_ORIGINS` stays unset |
| GitHub OAuth | Callback is already `https://yakka.build/oauth/callback`. `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` are absent. Set both with `fly secrets set -a yakka`. Do not deploy until both are set. |

The addresses from the destroyed `workflow-collector` app (`109.105.218.231`, `2a09:8280:1::1bb:d911:0`) are not the records to set.

## Deviations

Deploy was not run. The brief says not to deploy when either OAuth value is missing, and this run says to stop and name that blocker rather than invent values. Cody corrected the Fly app name from `workflow-collector` to `yakka` after the first create; that app was destroyed and `yakka` was created. Briefs 4-01, 4-02, and 4-03 and the phase 4 contract now name app `yakka`.

## Contract notes

The public origin is `https://yakka.build`. It is not live: DNS has no records, and the app has no release. `https://yakka.fly.dev` is not the close condition.

## Bugs

None in the product. The collector process is not running.
