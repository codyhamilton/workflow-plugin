# Review — 10 workflow analytics

## Terminal review, 2026-10-06

Verdict: **PASS_WITH_FOLLOWUPS**

Reviewed: branch `worktree-wa-phase3` at d7d7b65 (diff `112b676..d7d7b65`), plus the in-review fixes committed with this file. Two independent reviewers who did not build the change, by lens: Go serve, store and release tooling (`tools/`); the site package (`packages/workflow-analytics/`).

### Phase outcomes

- **Phase 1 — Analytics reads: met.** `go vet`, `go test ./...` pass. All seven `/v1/analytics` routes sit behind `method(GET, auth(...))`; SQL is parameterised with group names from a fixed map; week buckets are ISO Mondays; cursors are bound to route, filter and the first page's resolved window; explore reads one past the cap to set `truncated`; errors are `{"error":...}`. CORS order `localGuard` → `cors` → mux refuses non-loopback `Host` before CORS, rejects `null` and `localhost.evil.com`-style origins.
- **Phase 2 — Report views: met.** `npm test` 11/11, `npm run test:e2e` 26/26 (with `check:bundle` against the live key and a dummy token), `npm run build` emits `build/index.html`. Each route calls the contract's endpoints; filters live in the URL and survive reload; `/settings` uses the two named `localStorage` keys and sends `Authorization` only when a token is set.
- **Phase 3 — Local serve hosts the site: met.** Orchestrator check: a `build.sh` binary on loopback serves the built `index.html` (`no-cache`, no marker) at `/` and `/quality`, `/v1/health` JSON, `/v1/not-a-route` JSON 404, immutable assets cached a year. Hosted Playwright spec 6/6 against a binary rebuilt after the in-review fixes. `BuildTests` pass; `site/` and `bin/` clean after every build. `wrangler.toml` declares `pages_build_output_dir = "./build"` with no `404.html`.

### Findings

**blocker** — none.

**high** — none.

**medium**

1. Keyed-mode auth was tested on `summary` only; nothing guarded "no tenant data without auth" on the other six analytics routes. `tools/workflow/internal/serve/analytics_test.go` (`access` subtest). — **Resolved in review**: the subtest now loops all seven routes with no key and a wrong key, expecting 401. `go test ./internal/serve/` ok.
2. `test_7_build_sh` did not prove release binaries embed the built site (the marker string is a Go constant in every binary, so it can't be the probe). `tools/release/test_release.py`. — **Resolved in review**: asserts each binary contains `site/_app/immutable` (false for a placeholder build, checked); file read moved into a `with` block. `BuildTests` ok.
3. Trend lines drew straight across days/weeks with no events, because the series API is sparse. `src/lib/charts/LineSeries.svelte`. — **Resolved in review**: new `src/lib/series.ts` `fillBuckets` zero-fills gaps between first and last bucket by day or week; `/trends` passes the bucket. Unit tests added; the table spec still reads absent cells. `npm test` 11/11, e2e 26/26.
4. On a Pages deployment with no base URL, `/v1/...` returns the site's HTML with 200 and the user saw a raw JSON parse error. `src/lib/api.ts`. — **Resolved in review**: non-JSON responses become a connection error naming the API base URL setting, so the layout shows its `/settings` hint. Unit test added.
5. `rejWhere` (`tools/workflow/internal/store/analytics.go`) drops precheck rejections to 0 under any `repo_id`/`harness` filter, misleading summary and explore. Carried since phase 1. — **Follow-up**: needs a contract decision on whether a rejection belongs to a repo.

**low**

6. `FilterBar.svelte` re-fetched facets on every filter change though facets depend only on the window. — **Resolved in review**: re-fetches on `from`/`to` only.
7. The hosted site sends no `X-Frame-Options`/`frame-ancestors`; a remote keyed serve's `/settings` could be clickjacked to redirect the stored token. — **Follow-up**.
8. `cors` adds `Vary: Origin` only for allowed origins; a shared cache could serve a header-less response to an allowed origin (breakage, not leakage). — **Follow-up**.
9. `WORKFLOW_SERVE_CORS_ORIGINS` entries are compared exactly and never validated; a trailing slash silently never matches. — **Follow-up**: warn at startup.
10. `build.sh` runs `npm ci` only without `node_modules/` (brief 3-02's choice), so a release may embed stale dependencies; it saves the working-tree `site/index.html`, so a SIGKILLed run leaves the next run restoring a built site. — **Follow-up**.
11. Cursor `From`/`To` use `UnixNano`, overflowing outside 1678–2262. — **Follow-up**.
12. `/quality` shows distributions as a percentile table, no LayerChart. — **Follow-up**.
13. `/repos` silently omits empty `repo_id`; one summary request per repo. — **Follow-up**.
14. `/settings` does not warn on an `http:` remote base URL (token in clear) and a base ending in `/v1` becomes `/v1/v1`. — **Follow-up**.
15. `format.ts` `num()` is unused and its comment overstates it. — **Follow-up**.
16. `/explore` keeps previous rows and banner beside the error panel when a re-fetch fails. — **Follow-up**.

### Intent and assumption ledger

Implementation matches the verbatim intent: a static Svelte site, same-origin on local serve, the same build declared as the Pages output, covering conversations, hooks, executions, repos, time and quality views, with URL filters standing in for saved reports. Ledger: assumptions 2 (no new fields), 3 (one row per brief), 4 (token only in `localStorage` and the header, never the bundle or URL), 5 (Pages project is an operator action; no deploy step), 6 (`ts` vs `at`), 7 (no saved reports) hold. Assumption 1 (posture) is not a code matter and is unchanged.

### Plan sufficiency

Sufficient. Contracts were exact on shapes, order, caps, errors, CORS and hosting, so every finding was placed against a stated rule. Gaps: whether a rejection belongs to a repo (finding 5); whether a report must come from the same conversation (built as "same conversation", consistent with assumption 3); no stance on framing or security headers for the hosted site (finding 7). Phase 2 named the series as sparse but its done evidence read only the table, which let finding 3 through.

### Residual risks

- Chart rendering is not visually checked; specs read tables. `svelte-check` is not installed.
- Paging and aggregation speed on a large tenant are unmeasured.
- Perspective's viewer bundle carries an opt-in LLM-chat feature that could send explore rows to a third-party provider if a user supplies a key.
- Any script on the Pages origin can read the token, as the design accepts.
- `build.sh`'s `no Node toolchain` branch and EXIT trap under SIGINT/SIGTERM are unexercised.
