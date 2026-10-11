# 4-11 — Quality: scores with exactly one kind, on the shared client

Status: **done with concerns**

## What changed

- `packages/workflow-analytics/src/routes/quality/+page.svelte` — rewritten on the shared client:
  `view.paramsFor('rest')` + `scoresParams(base, kind)` for slot `quality-scores`, `getJSON` for the
  all-time `baselines` call on slot `quality-baselines`, and `view.setInclude('kind', [k])` for the kind
  tabs. The selected kind is the first valid `kind` include, default `design`. Table markup and the
  `quality-kind-<k>`, `q-row`, `q-<check>-w-<f>`, `q-<check>-b-<f>` ids are unchanged; no chart added.
- `tests/e2e/quality.spec.ts` — added a tab→URL test, a "exactly one kind on every scores request"
  test, a "switching kind issues one scores request" assertion, and a 1 s timing test. The existing
  zero-scorer and stubbed-response numeric assertions are kept verbatim.

## Done evidence

Old `quality.spec.ts` run against the new page, before editing the spec: **3 passed, 0 failed**
(zero-scorer 639 ms, `?kind=brief` 378 ms, stubbed 951 ms). No test failed, so no edit was forced by
breakage; the spec additions cover the new brief requirements.

- `npm test` → 76 passed (11 files).
- `npm run build` → built (`adapter-static`, wrote `build`).
- `E2E_PORT=4411 npm run test:e2e -- quality.spec.ts` → 5 passed.
- Test 3 asserts every `/v1/analytics/scores` request carries exactly one `kind`, and that a fixture
  with no `kind` in the URL requests `kind=design`; it then clicks the brief tab and asserts exactly
  one new scores request with `kind=brief`.

## Departures from the brief

- Kept the `quality-kind-note` element (a URL naming several kinds shows the first). It is not named
  in the brief but was on the old page and is harmless.
- Kept `setError`/`clearError` on failure so fetch errors still surface in the shell's error panel;
  the brief only named `getJSON`.

## Contradiction between this brief and its cited contract

- Brief line 30: "No chart is added: Quality is a table in the design."
  `DESIGN.md` line 218: "Quality: distribution charts beside the baseline."
  These directly contradict. I followed the brief (table only, no chart) and am reporting the conflict
  rather than resolving it silently.

No contradiction found between the brief's contract and the server: `scores` is `400 "kind required"`
unless exactly one `kind` is sent (`parseFilter`, `scoresKind`), and `baselines` takes only `kind`. The
client cache key includes `kind`, so baselines cache per kind. `scores` is requested with `rest`'s
399-day clamp; the shell shows `notice-clamped` for All time. `ANALYZE facts` is server-side, untouched.

## Unfinished / known problems

- None in this unit. The e2e run printed an unrelated `layerchart`/`d3-shape` unused-import warning;
  out of scope here.
