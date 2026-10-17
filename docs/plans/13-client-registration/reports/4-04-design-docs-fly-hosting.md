---
cursor:
  subagentId: "bc-c2485d50-f563-5fb2-9ba6-05cf56034e18"
---

# Report: 4-04 — Design docs for fly hosting

**Status:** done

**Correction:** The Fly app name is `yakka`, and design 7 Hosting names that app. The product name stays `workflow`. The public origin is `https://yakka.build`.

## What changed

- **`docs/design/07-analytics-site.md` — Hosting:** Added fly.io remote collector bullets (`fly.toml`, app `workflow-collector`, `WORKFLOW_SERVE_DATA` volume, OAuth on the collector origin, no `WORKFLOW_SERVE_KEYS`, `WORKFLOW_SERVE_CORS_ORIGINS` for Pages). Named `https://workflow-collector.fly.dev` from committed `fly.toml` / 4-01 (4-02 report not present). Clarified Cloudflare Pages as static pasted-token client via `/settings`, no session cookie, unchanged `pages_build_output_dir`. Noted carried item 1: `?tenant=` from `/v1/me` only on overview and `/profile`, not other report routes.

## Checks

**Before:**

```
rg fly.io|fly.toml|WORKFLOW_SERVE_DATA → (no matches)

rg Pages|/settings|pasted → matches in Shape, routes, Browser access, The site, Hosting (wrangler only)

rg 'no user identity' → (no matches)
```

**After:**

```
rg fly.io|fly.toml|WORKFLOW_SERVE_DATA → lines 226–230 (Fly.io remote collector bullet)

rg Pages|/settings|pasted → Hosting + existing Shape/Browser access/The site lines (Pages static client at 250–255)

rg 'no user identity' → (no matches)
```

## Deviations

- None.

## Contract notes

- Public URL taken from `fly.toml` and 4-01 report because `4-02-fly-collector-deploy.md` report is not on the branch yet; not invented beyond the manifest.
- Shape line 17 still says data routes carry `?tenant=` from `/v1/me`; Hosting now states the narrower wiring (carried item 1). Brief asked not to rewrite other sections; possible doc tension left for a later pass.
- No contradiction between brief and DESIGN Phase 4 / collector-hosting bullets.

## Known problems

- None in scope. Deploy verification remains 4-02 / 4-03.
