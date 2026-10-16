# Report: 2-06 — Analytics site reads doc

Status: `done`

## What changed

Updated `docs/design/07-analytics-site.md` Analytics reads **Routes** to match plan 14 Phase 2 as implemented in units 2-01–2-05:

- **2-01** (`GET /v1/analytics/distribution`): measure/grain/dim/filter/bin/percentile/`top`/`truncated` contract documented.
- **2-02** (`GET /v1/analytics/score-series`): `kind`, `bucket`, bucket `t` rule, sparse check points, population vs `/scores`.
- **2-03** (`GET /v1/analytics/executions`): repeatable query `shape` (rows/cursor only), optional `bucket` + three-key `series` order, cursor binding.
- **2-04** (`GET /v1/analytics/conversations`): row fields `model`, `model_calls`, `unpriced_calls`, `cost_usd`, `tokens_in`, `tokens_out`.
- **2-05** (`GET /v1/analytics/conversation`): optional `from`/`to`, whole-run `totals`, `window_totals` when bounds set, cap semantics.

Added an explicit sentence that existing `/query` fields (and `/schema`, `/summary`, `/series`, `/scores`, `/baselines`) are unchanged. No edits to theme, dashboard, or site interaction sections.

Verified registered paths in `serve.go` include `/v1/analytics/distribution` and `/v1/analytics/score-series` alongside the extended routes.

## Done evidence

**Before** (failing check — Phase 2 route names absent from read API; no `/query` unchanged statement):

```
$ rg -n 'distribution|score-series|window_totals' docs/design/07-analytics-site.md
25:| `/quality` | Score distributions | ...
45:type** is the artifact kind plus its check distributions.

$ rg -n '/query.*unchanged|unchanged.*\/query' docs/design/07-analytics-site.md
(exit 1, no matches)
```

**After**:

```
$ rg -n 'distribution|score-series|window_totals' docs/design/07-analytics-site.md
104:- `GET /v1/analytics/distribution` — ...
125:- `GET /v1/analytics/score-series` — ...
189:  `window_totals` is that range's full totals ...
190:  `window_totals` is absent. ...
191:  ... `"window_totals"?,"events":[…],"truncated"?}`.

$ rg -n '/query.*unchanged|unchanged.*\/query' docs/design/07-analytics-site.md
194:Phase 2 leaves existing `/query` fields unchanged; ...
```

## Deviations

None.

## Contradictions

None between plan 14 Domain: Analytics reads and the updated design 7 section. Design 7's executions bullet previously described `shape` only as a row attribute; it now also documents the repeatable filter and `series`, per plan 14 (not a conflict — documentation catch-up).
