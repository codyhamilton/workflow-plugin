---
brief_id: 220
design_id: 209
---

# Brief: 3-01 — Scorer, check loading and the execution-report checks

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its package is consumed by 3-02,
which wires it into `workflow serve`'s screen worker; its checks file is read by that service and
referenced by the skills in phase 6.
Owned paths: `tools/workflow/internal/scorer/` (new), `tools/quality/checks/execution-report.json`
(new), `docs/plans/09-workflow-binary/reports/3-01-scorer-checks.md` (new). Touch nothing else; in
particular not `tools/quality/criteria.json`, the other checks file, `go.mod` (no new dependencies:
`net/http` and `encoding/json` are enough), or any other `internal/` package.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing (phases 1 and 2 are committed).
Runs alongside: nothing (3-02 depends on this unit's API).
Budget: 8 files to read, about 500 lines to write including tests, 50 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/design/03-remote-service.md` — Screening and scoring (lines 147-177) and Configuration
   (lines 49-63). Binding.
2. `docs/design/01-event-model-and-ingest.md` — Execution report (lines 81-118), especially the
   Rubric (lines 105-111). Binding for the checks file's wording.
3. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 3 (lines 190-201) and Assumption 3.
4. `tools/transcript/lib/jev_client.py` — `API_URL`, `JEV_MODEL`, `validate_systemone_questions`
   and `post_systemone` (lines 11-12, 80-147): the request shape you reproduce.
5. `tools/quality/quality.py` — `jev_spec` and `jev_scores` (lines 167-213): how the legacy scorer
   turns checks into questions and answers into scores. The Go scorer must ask the same thing.
6. `tools/quality/criteria.json` — the `brief.jev` and `design.jev` maps (ignore `det`; those are
   deterministic checks that stay in Python). Use `python3 -c` or `jq` to look; do not read it whole.
7. `tools/quality/checks/acceptance-provenance.json` — the checks-file shape.
8. `tools/quality/lifecycle.py` `put_checks` (lines 103-127) — only to confirm what follows under
   "Legacy service".

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, a `Scorer` exists that, given one artifact's content, returns a pass or
flag credential verdict and that kind's check scores (0 to 1) from a single System One request; the
check set the service loads at start is the same one the legacy scorer asks; and design 1's report
rubric is a loadable check file whose wording a test pins to design 1. 3-02 can then wire it in
without reading Python or the TypeSafe API.

## Contract

Cited, binding (design 3, Screening and scoring): "The scorer sits behind a `Scorer` interface
(`Screen`, `Score`). The model behind Jev is not part of any contract here." "The Jev
implementation makes one System One request per content hash (`POST
https://api.typesafe.ai/v1/systemone`, as `tools/transcript/lib/jev_client.py` does today): the
kind's checks as `score` questions, plus one screen question asking whether the text contains a
credential. A screen score at or above its flag level is a flag." "Checks are the existing check
definitions (`tools/quality/criteria.json` plus `tools/quality/checks/*.json`), loaded from files at
start; the execution report kind takes the candidate checks in design 1. Rubric wording for the
execution report is defined once and shared with the skill (design 1)." Design 3 Configuration:
"`TYPESAFE_API_KEY` | scorer credential; server side only, never in any client config".

Design 1, Execution report: "The wording is defined once and referenced by both the skill and the
service's checks, so they cannot drift."

Decisions made at refine (settled):

- **Interface** (package `scorer`):
  ```go
  type Verdict struct{ Flag bool; Reason string } // Reason names the screen and level, never text
  type Score struct{ Check string; Result float64 } // 0..1, higher is better
  type Scorer interface {
      Name() string // written to screens.scorer and scores.scorer, e.g. "jev-1.13.0", "fake"
      Screen(ctx context.Context, content []byte, kinds []string) (Verdict, error)
      Score(ctx context.Context, content []byte, kinds []string) ([]Score, error)
  }
  var ErrUnreachable = errors.New("scorer unreachable")
  ```
  `kinds` is every artifact kind the content was seen under (`design`, `brief`, `report`, or empty).
  3-02 calls `Screen` and, on a pass, `Score` with the same arguments.
- **One request per content hash**: `Jev.Screen` sends one request holding the screen question and
  the checks of every kind in `kinds`, and keeps the parsed check answers keyed by the content's
  SHA-256; `Jev.Score` with the same content returns them without a request (and removes them). A
  `Score` with no kept answers makes its own request. Keep at most a few entries; this is a
  hand-off between two calls, not a cache.
- **Request**: `{"model": "jev-1.13.0", "state": {"snapshot": <prefix><text>}, "questions": {...}}`,
  headers `Authorization: Bearer <key>`, `Content-Type` and `Accept: application/json`, timeout
  120 s. Prefix as in `quality.py`: `"DESIGN DOCUMENT:\n"` for design, `"BRIEF:\n"` for brief,
  `"EXECUTION REPORT:\n"` for report (first kind in `kinds` decides), `"DOCUMENT:\n"` for none.
  Text is truncated to 60,000 characters (as `quality.py`). Each check becomes
  `{"type": "score", "instructions": q, "criteria": levels}` under its check name. The URL is a
  field on `Jev` (default the API URL) so tests can point it at `httptest`.
- **Screen question**: name `screen_credential`, type `score`, instructions `"Does this text contain
  a credential: an API key, token, password, private key or connection string with a live secret?"`,
  criteria (the level index is the raw score; here a higher level means more credential-like, so
  it is not a quality score and is never written to `scores`):
  `["No credential or secret value appears", "Only placeholders, redacted values, variable names
  or documented example values", "A value that may be a live credential, token, password or private
  key", "A live credential, token, password or private key is plainly present"]`. Flag level is 2:
  a raw score of 2 or 3 is a flag, with reason `screen: jev screen_credential level <n>`.
- **Answers**: `answers[name].score` (a number 0-3) divided by 3, inverted (`1 - x`) where the check
  says `invert`, rounded to 3 places, as `quality.py`. A missing check answer is left out; a missing
  or non-numeric `screen_credential` answer is an error (not a pass).
- **Errors**: transport errors, timeouts, HTTP 5xx, 429, 401 and 403 wrap `ErrUnreachable` (the
  content stays pending and the worker backs off). Other 4xx and a malformed body are plain errors.
  No error string, log line or test output may contain the key, the request body, the content or the
  response body; status code and a short cause only.
- **No key**: `NewJev` is only called with a non-empty key; with none, 3-02 uses no scorer and the
  verdict is `unscreened`. This package never reads the environment except in the live test.
- **Checks loading**: `LoadChecks(dir string) (Checks, error)` where `dir` holds `criteria.json` and
  `checks/`. From `criteria.json`, each top-level kind object's `jev` map gives `name → {q, levels,
  invert}`; `det` is ignored. Then `checks/*.json` in filename order, each `{"checks": [{kind, name,
  q, levels, invert?, active?}]}`: a check overrides the same name; `active: false` removes it
  (legacy `jev_spec` semantics). Accepted kinds: `brief`, `design`, `report`. A missing
  `criteria.json`, unparsable JSON, an unknown kind, an empty `q` or fewer than two levels is an
  error naming the file and check. `invert` absent or `null` is false. `Checks` exposes
  `For(kind) []Check` (stable order by name) and counts per kind for 3-02's start-up line.
- **Fake**: `scorer.Fake{Verdict, Scores, Err}` (or equivalent) implementing `Scorer` with name
  `"fake"`, recording calls, for 3-02's tests. Keep it in a non-test file so other packages can use it.
- **Execution-report checks file**: `tools/quality/checks/execution-report.json`, exactly:
  ```json
  {
   "note": "Execution report rubric, design 1 (docs/design/01-event-model-and-ingest.md, Execution report, Rubric). Each q is the rubric line verbatim; this file is the one definition the skill and the service share.",
   "checks": [
    {"kind": "report", "name": "r.done_verifiable", "q": "Says what was done against the brief, verifiably (commits, test results).", "levels": ["Does not say what was done", "Says what was done, with no evidence", "Says what was done, with evidence for some of it", "Says what was done against each part of the brief, with commits or test results"], "invert": false, "basis": "Design 1, Execution report, Rubric."},
    {"kind": "report", "name": "r.departures_named", "q": "Names every departure from the brief with its reason.", "levels": ["Departures are evident but not named", "Some departures named, without reasons", "Departures named, some reasons missing", "Every departure named with its reason, or says there were none"], "invert": false, "basis": "Design 1, Execution report, Rubric."},
    {"kind": "report", "name": "r.unfinished_actionable", "q": "Leaves unfinished work specific enough to act on without reopening the whole execution.", "levels": ["Unfinished work is evident but not mentioned", "Mentioned only vaguely", "Mostly specific; some items need the execution reopened", "Every unfinished item can be acted on as written, or says there is none"], "invert": false, "basis": "Design 1, Execution report, Rubric."},
    {"kind": "report", "name": "r.problems_plain", "q": "States known problems plainly.", "levels": ["Known problems omitted or hidden", "Hinted at or hedged", "Stated, some softened or buried", "Every known problem stated plainly, or says there are none"], "invert": false, "basis": "Design 1, Execution report, Rubric."},
    {"kind": "report", "name": "r.nothing_unusable", "q": "Contains nothing the consumer cannot use.", "levels": ["Mostly narration or derivable facts", "Much the consumer cannot use", "A little the consumer cannot use", "Nothing the consumer cannot use"], "invert": false, "basis": "Design 1, Execution report, Rubric."}
   ]
  }
  ```
  Format it as you like; the content is fixed.
- **Legacy service** (verified at refine): the Python service never scans `tools/quality/checks/`;
  files there reach it only through `load_checks.py <file>` → `PUT /v1/checks`, whose `put_checks`
  rejects any kind other than `brief`/`design` with a 400. A new file there therefore changes
  nothing for the running legacy service. Confirm this with a grep and say so in the report; do not
  change the legacy code.

## Changes

New package `internal/scorer`: the interface and `ErrUnreachable`, `Checks`/`LoadChecks`, `Jev`
(`NewJev(key string, checks Checks) *Jev`, fields for URL, model and `*http.Client`), `Fake`, and
tests. New file `tools/quality/checks/execution-report.json`.

### Keep untouched

`tools/quality/criteria.json` and `checks/acceptance-provenance.json` (the legacy service and the
lab read them). Every other Go package; `go.mod` and `go.sum`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

Fail first: write `TestReportChecksVerbatim`, `TestLoadChecks` and `TestJev` (below) before the
implementation and before `execution-report.json` exists; run them and quote the failure (compile
errors for missing identifiers, then `TestReportChecksVerbatim` failing on the absent file). Each
guards one risk: the verbatim test guards rubric drift between design 1 and the service (design 1:
"so they cannot drift"); the load test guards the Go service asking a different check set from the
legacy scorer; the Jev test guards a request shape TypeSafe rejects and a secret or key leaking into
errors.

- `go vet ./... && go test -race ./...` → passes; the new tests run with no network and no key.
- `go test -v -run 'TestLoadChecks|TestReportChecksVerbatim' ./internal/scorer` → loading the real
  `../../../quality` directory gives 8 design checks + 3 from acceptance-provenance (11), 8 + 3 brief
  (11), and 5 report checks; each report check's `q` appears verbatim in
  `docs/design/01-event-model-and-ingest.md` (the test reads that file, so the wording cannot drift).
  Bad files (unknown kind, one level, missing criteria.json, `active:false` removing a check) are
  covered with temp dirs.
- `go test -v -run TestJev ./internal/scorer` against an `httptest` server → asserts the request
  method, path, bearer header, `model`, the snapshot prefix and truncation, one `score` question per
  check of each given kind plus `screen_credential`; exactly one HTTP request for `Screen` then
  `Score` on the same content; raw 0..3 maps to 0, 0.333, 0.667, 1 and inverts where flagged; screen
  raw 2 and 3 flag, 0 and 1 pass; 500, 429, 401 and a closed server give `errors.Is(err,
  ErrUnreachable)`; 400 and a malformed body do not; no error string contains the test key or the
  content.
- `WORKFLOW_JEV_LIVE=1 go test -v -run TestJevLive ./internal/scorer` → the one live call: skipped
  unless `WORKFLOW_JEV_LIVE=1` and `TYPESAFE_API_KEY` is non-empty; screens and scores a small
  secret-free design (inline in the test, about 30 lines of plain prose, no key-like strings) with
  the real checks; expects a pass and at least one `d.*` score in [0, 1]; if the API answers
  `ErrUnreachable`, `t.Skip` with the status, so it is reported, not failed. Run it once and quote
  the outcome (verdict, number of scores, or the skip reason) in the report. The test logs check
  names and scores only.
- `grep -rn "checks/" tools/quality/*.py` shows only `load_checks.py`'s usage string, and
  `put_checks` rejects kind `report` — quoted in the report.

Safety: temp dirs only (`t.TempDir()`). Start no `serve`; if you do for any reason, use a port other
than 8765 or 8770 and kill it after. `TYPESAFE_API_KEY` is in the environment: never print, log,
echo or write it anywhere (no `env`, `printenv`, `set -x`, `echo $TYPESAFE_API_KEY`, no `t.Log` of
headers or requests), never place it in a file or config. Only `TestJevLive` reads it.

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 3: scorer and checks` (the
orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/3-01-scorer-checks.md` (design 1, Execution report: what was
done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), including the live call's outcome and the final exported API names 3-02 will use, and
include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
