# Report: 3-01 scorer, check loading, execution-report checks (exec 22)

## Done against the brief
- New package `tools/workflow/internal/scorer`: `scorer.go` (interface, `ErrUnreachable`, `Fake`), `checks.go`, `jev.go`, tests.
- New `tools/quality/checks/execution-report.json` (5 report checks, content as the brief fixes).
- Fail first: with no implementation the tests failed to compile (`undefined: Checks`, `LoadChecks`, `Jev`, `NewJev`). With the loader but no checks file, `TestReportChecksVerbatim` failed with `report checks = 0, want 5` and `TestLoadChecks/real` with `report = 0, want 5`. After adding the file, both pass.
- `go vet ./... && go test -race ./...` passes, all packages.
- Real `tools/quality` loads 11 design, 11 brief, 5 report checks; each report `q` is found verbatim in design 1 (test reads the file).
- `TestJev` (httptest) covers method, path, bearer, Content-Type, Accept, model, snapshot prefix and 60,000 truncation, one score question per check of each kind plus `screen_credential`, one request for Screen then Score, 0/0.333/0.667/1 mapping and invert, screen 0,1 pass and 2,3 flag, 500/503/429/401/403/closed server wrap `ErrUnreachable`, 400/malformed body/missing or non-numeric screen answer do not, and no error contains the key or content.
- Live call: `WORKFLOW_JEV_LIVE=1 go test -run TestJevLive` ran (0.30 s): verdict pass, 11 `d.*` scores, all in [0,1] (0.143 to 0.997). Not skipped.
- Legacy: `grep -rn "checks/" tools/quality/*.py` shows only the usage string in `load_checks.py:2`; `put_checks` rejects any kind other than brief/design (400). The new file does not reach the legacy service. No legacy code changed.

## API for 3-02
`scorer.Scorer` {`Name`, `Screen`, `Score`}; `scorer.Verdict{Flag, Reason}`; `scorer.Score{Check, Result}`; `scorer.ErrUnreachable`; `scorer.LoadChecks(dir) (Checks, error)` with `Checks.For(kind) []Check` and `Checks.Count(kind) int`; `scorer.NewJev(key, checks) *Jev` with fields `URL`, `Model`, `Client`; `scorer.Fake{Verdict, Scores, Err}` with recorded `ScreenCalls` and `ScoreCalls` ([]Call{Content, Kinds}). Constants `DefaultURL`, `DefaultModel`. `Jev.Name()` returns the model, `jev-1.13.0`.

## Departures
- Live API returned non-multiples of 1/3 (e.g. 0.583), so raw scores are fractional, not integers 0..3. Mapping is score/3 rounded to 3 places regardless; the screen level uses the raw value truncated to int for the reason string, while the flag compares the int (a raw 1.9 would pass). Not exercised live for the screen; 3-02 need not care.
- `Jev.Screen` keeps check answers for at most 4 content hashes.

## Unfinished
None for this brief.

## Known problems
- Content is sent unscrubbed (legacy `quality.py` scrubbed first); the brief says the precheck is upstream, so the scorer does not scrub.
- The legacy criteria.json also holds a `version` and `note` key; the loader ignores any non-kind key.

## Orchestrator amendment

The screen level was `int(raw)`, so a fractional 1.9 passed. It is now `math.Round(raw)`: 1.5 and
above flags. `TestJev/screen_levels` covers 0, 1, 1.4, 1.5, 1.9, 2 and 3.
