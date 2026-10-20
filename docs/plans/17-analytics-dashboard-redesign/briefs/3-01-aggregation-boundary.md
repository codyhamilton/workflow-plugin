# Brief: 3-01 — Aggregation boundary

Consumer: the phase 3 implementation worker.
Owned paths: `packages/yakka-analytics/src/lib/aggregate.ts` (new), `packages/yakka-analytics/src/lib/aggregate.test.ts` (new), `docs/design/07-analytics-site.md` (the Data layer bullet only). Touch nothing else. No other new files. Do not add a dependency.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to `origin` branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/3-01-aggregation-boundary.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit. Test results, not a file list, model, or cost.
Depends on: nothing.
Runs alongside: nothing.
Budget: 18 files to read, about 800 lines to change, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Aggregation boundary, and Phase 3 — Aggregation boundary. Those two sections are the contract.
2. `docs/design/07-analytics-site.md` — `### Shared filter` and `### Routes` (the reads this boundary may compose). Then the **Data layer** bullet under `## The site` (the paragraph this unit amends).
3. `packages/yakka-analytics/src/lib/params.ts` — `resolveWindow`, `apiParams` (exclude becomes the facet complement; `conversation_id` exclude is not sent).
4. `packages/yakka-analytics/src/lib/presets.ts` — `PRESETS`, `presetWindow`. `all` returns null.
5. `packages/yakka-analytics/src/lib/buckets.ts` — `bucketCount`. Cap is 400.
6. `packages/yakka-analytics/src/lib/types.ts` — `Facets`, `QueryResponse`, `Scores`, `Baselines`, `ScoreSeries`, `DistributionResponse`, `Executions`, `Conversations`, `ConversationDetail`. Grep the interface; do not re-read the file.
7. `packages/yakka-analytics/src/lib/query.ts` — `getJSON` only (about the last 5 lines). Paths are relative to `/v1`.
8. `packages/yakka-analytics/src/routes/quality/+page.svelte` — the `baselines` `getJSON` call only, so the all-time baseline path is the one the package already uses.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

One caller asks the package for a slice and gets one result back. The caller does not name `/v1/analytics/*` or `GET /v1/baselines`. Landing and analysis do not exist yet; this unit does not mount them.

## Contract

Cited from `DESIGN.md`, Domain: Aggregation boundary, and Phase 3. Settled.

> one request, one result. Callers do not name `/v1/analytics/*` or `GET /v1/baselines`.
>
> - The request carries `tenant` for a session read, from the `GET /v1/me` body. A bearer read uses the token's tenant and does not invent one.
> - `window`: `{ from, to }` as RFC3339, and `tz` as an IANA name. A preset may be passed instead of `from`/`to`. Preset names are the ones the package already has: Today, 24h, 7d, 30d, 90d, This month, YTD, All time (`src/lib/presets.ts`). Omitted range resolves as design 7 Shared filter: `to` now, `from` thirty days earlier. That thirty-day span is design 7's labelled judgement.
> - `filters.include` and `filters.exclude`: repeatable values of `repo_id`, `harness`, `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`. The server has no exclude parameter. The boundary applies an exclude. An unsupported `conversation_id` exclude is listed in `ignored_filters`.
> - `ask`, one of: `trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, `executions` (the shapes in that domain section).
>
> Measures and dims are the set design 7 already serves (`/v1/analytics/schema` for query measures; distribution measures `cost_usd` and the token measures; quality kinds as above). The boundary does not invent a measure the server cannot answer. It may call the existing reads, compose several of them, or aggregate in the client from data the package loaded. A library is allowed for that aggregation. No library is named here.
>
> Result: the slice the `ask` needs (points, rows, bins, score band and baseline, conversation rows, or one run), the resolved `window`, and `partial`, `ignored_filters`, and `truncated` when the read produced them. Every result includes the in-window values for the filter and breakdown controls. The result includes `clamp` when the resolved window is not the requested window (the 399-day client clamp, or the 400-bucket refusal). The boundary does not present a clamped window as complete. Field meanings for `partial`, `ignored_filters`, and `truncated` stay the ones design 7 gives the underlying read. A view does not branch on which URL answered.

Phase 3 outcome, same file:

> One caller receives the slice for each of `trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, and `executions`, with `partial`, `ignored_filters`, and `truncated` when the read produced them, and does not name `/v1/analytics/*` or `GET /v1/baselines`. `packages/yakka/internal/serve` gains no analytics route from this phase.

Non-goals, same domain: new or changed routes in `packages/yakka/internal/serve`, new tables in `packages/yakka/internal/store`, ingest changes, and a server-side store of saved analyses.

## Changes

Add `aggregate(request, options?)` in `src/lib/aggregate.ts`. One call returns one result. `options.fetcher`, when passed, replaces `getJSON` and is how tests avoid a server. The default fetcher is `getJSON`. The fetcher's path argument is relative to `/v1`, matching `getJSON`. Callers of `aggregate` pass the request below and no path.

The boundary module may name the existing reads. A caller of `aggregate` may not. Do not add a library. Compose the reads the package already has. Do not call `fetchMe`. Session routes stay on `src/lib/api.ts`. `apiGet` already attaches a stored bearer; do not invent a tenant when `request.tenant` is absent. When `request.tenant` is a non-empty string, send it as the `tenant` parameter on every read this call makes.

Request fields:

- `tenant?: string`
- `window?: { from?: string; to?: string; tz?: string; preset?: string }`
- `filters?: { include?: Partial<Record<Dim, string[]>>; exclude?: Partial<Record<Dim, string[]>> }` where `Dim` is the ten names in the contract.
- `ask`: the seven shapes in the contract. `trend`: measure, bucket `hour` | `day` | `week` | `month`, optional one breakdown dim. `breakdown`: measure and one dim, no time bucket. `distribution`: measure, grain `call` | `conversation`, optional dim `model`. `quality`: kind `design` | `brief` | `report`, bucket `day` | `week` | `month`. `conversations`: no extra fields. `conversation`: one id. `executions`: optional bucket `day` | `week` | `month`.

Preset values are `presets.ts` ids (`today`, `24h`, `7d`, `30d`, `90d`, `month`, `ytd`, `all`) and the labels `DESIGN.md` lists (`Today`, `24h`, `7d`, `30d`, `90d`, `This month`, `YTD`, `All time`). Resolve with `presetWindow`. A preset is instead of `from`/`to`, not as well as them: when `preset` is set, ignore `from`/`to`.

Omitted preset and omitted `from`/`to`: `to` is now, `from` is thirty days earlier. That is design 7 Shared filter, not the hour-rounded `30d` preset. Omitted `tz` is `UTC`.

Window rules, reusing `resolveWindow` rather than a second clamp:

- `trend` and `breakdown` are served by the query read. All time stays `all=1` and is not the 399-day clamp (`params.ts` route `query`).
- Every other ask uses route `rest`. When `resolveWindow` sets `clamped`, the result includes `clamp` and `window` is that clamped pair, as RFC3339. The slice is for that window.
- When a bucket is set and `bucketCount` for the resolved window is greater than 400, do not call the server for that series. The result includes `clamp`. The series, points, or bucketed rows for that bucket are absent. Do not pick a coarser bucket. `partial` is not `clamp`.
- `clamp` is included only in those cases. Shape: `{ reasons: ('rest-days' | 'bucket-cap')[] }`. Both reasons can apply together.

Exclude, reusing `apiParams` rather than a second complement:

- `conversation_id` exclude is not sent. Its key is listed in `ignored_filters`.
- Any other exclude is the facet complement, and needs the in-window facet list first. Facets are requested with the window only, as `view.svelte.ts` already does.
- An empty complement (the existing `{ empty: true }` case) returns an empty slice for that ask. It does not throw, and it does not invent a zero for `cost_usd`.

`ask: conversation` sends `id` and, when the resolved window has `from` or `to`, those two. It does not send dimension filters. Keys that were set are listed in `ignored_filters`. Pass the body through, including `window_totals` when the read returned it and `truncated` when it returned it.

Other asks, one underlying read unless named:

- `trend` and `breakdown`: the query read. Map rows to series of `{ key, points: [{ t, v }] }`. No breakdown dim is one series. A dim is one series per key. Leave points sparse. Do not zero-fill.
- `distribution`: the distribution read. Pass rows and bins through.
- `quality`: three reads — window scores, the all-time baseline path the quality page already calls, and score-series for the kind and bucket. The slice has the window score band, the baseline, and the score series. A bucket with no point stays absent.
- `conversations`: the conversations read, first page. Pass rows through. Pass `next` through when the read returned it. Do not rename `next` to `truncated`.
- `executions`: the executions read. Always include `counts`. Include `series` only when the request set a bucket.

A 400 from a read rejects the promise. It is not `clamp` and not an empty success. Do not invent a measure or a dimension the server cannot answer. Pass `measure` and `dim` through.

Every result includes `controls`, the in-window facet values (`Facets`). Also `window: { from, to }` as RFC3339 for the resolved window (`all=1` on a query ask has no from/to pair: `window` is `{ all: true }` and `clamp` is absent). Include `partial`, `ignored_filters`, and `truncated` only when a composed read produced them. Union them across composed reads. Field meanings stay design 7's.

Do not edit `src/lib/analysis/chart-frame/`. Those types are frame stubs. This unit's result types live in `aggregate.ts`. Phase 4 wires them.

Amend only the **Data layer** bullet in `docs/design/07-analytics-site.md`. State that landing and analysis read through this boundary, one request in and one result out, and that those callers do not name `/v1/analytics/*` or `GET /v1/baselines`. The boundary may compose those reads. Keep the sentences about debounce, abort, cache, `partial`, and `ignored_filters`; they still describe the client the current report pages use.

### Keep untouched

`src/lib/query.ts`, `src/lib/params.ts`, `src/lib/types.ts`, `src/lib/view.svelte.ts`, `src/lib/presets.ts`, `src/lib/api.ts`, report routes, `+page.svelte`, the session gate, and `src/lib/analysis/`. Existing pages keep their fetches until phase 4 and phase 5. `packages/yakka/internal/serve` and `packages/yakka/internal/store` stay untouched. The two failing `tests/e2e/shell.spec.ts` cases are carried from phase 2; do not fix them here.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npm test -- src/lib/aggregate.test.ts` → fails first because the module is absent, then passes. The tests call `aggregate` once per ask (`trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, `executions`) with an injected fetcher and receive that ask's slice. When the fake read returns `partial`, `ignored_filters`, or `truncated`, the result carries them. The test's `aggregate(...)` arguments contain neither `/v1/analytics` nor `baselines`. The injected fetcher may observe those paths.
- A `conversation_id` exclude is listed in `ignored_filters` and is not a parameter on any read the fetcher sees.
- A rest ask whose requested span is wider than 399 days includes `clamp` with `rest-days`, and `window.from`/`window.to` are not the requested pair.
- A bucket whose `bucketCount` exceeds 400 includes `clamp` with `bucket-cap` and does not include points for that range. The fetcher sees no series read in that case.
- Omitted `from`/`to` and omitted preset resolve to a span of thirty days ending at the injected now.
- `tenant` is sent only when the request carries it.
- `cd packages/yakka-analytics && npm test` → the package unit suite passes.
- Observable: `git diff --name-only` against the parent commit includes no path under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
