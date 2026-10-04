---
brief_id: 222
design_id: 209
---

# Brief: 4-01 — Advisory reads in the service: checks, baselines, search

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its endpoints are consumed by the
`workflow mcp` shim (4-02, built in parallel against the response shapes fixed below) and verified
end to end by 4-03's `TestAdvisoryOutcome`.
Owned paths: `tools/workflow/internal/store/`, `tools/workflow/internal/serve/`,
`tools/workflow/cmd/workflow/main.go` (only `runServe` and `screenStep`: checks loading), new
`tools/workflow/cmd/workflow/reads_wiring_test.go`,
`docs/plans/09-workflow-binary/reports/4-01-service-reads.md` (new). Touch nothing else; in
particular not `internal/scorer`, `internal/facts`, `internal/mcp`, the `case "mcp"` line in
`main.go` (4-03 owns it), the other `cmd/workflow/*_test.go` files, `go.mod` or `go.sum` (no new
dependencies: FTS5 is in the `modernc.org/sqlite` build; verified at refine with a
`CREATE VIRTUAL TABLE … USING fts5(…, tokenize='porter unicode61')`, `MATCH`, `snippet()` and
`bm25()` query against v1.60.1).
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing (phases 1 to 3 are committed).
Runs alongside: 4-02 (disjoint paths; 4-02 codes to the shapes below, not to your code).
Budget: 9 files to read, about 650 lines to write including tests, 70 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/design/04-advisory-surface.md` — API (lines 52-65) and Scores and baselines (lines 67-71).
   Binding.
2. `docs/design/03-remote-service.md` — API (lines 65-75: "Within `/v1`, changes are additive
   only") and Tables (lines 127-139). Binding.
3. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 4 (lines 210-220).
4. `tools/workflow/internal/store/store.go` — `migrations` and `migrate` (lines 23-140), `Promote`
   and `DropBlob` (around lines 410-450), `Artifact` (lines 623-686).
5. `tools/workflow/internal/serve/serve.go` — `Options` (lines 85-100), `Handler`, `auth`,
   `artifacts` (lines 283-423).
6. `tools/workflow/cmd/workflow/main.go` — `runServe` and `screenStep` (lines 57-136).
7. `go doc ./internal/scorer Checks` and `go doc ./internal/scorer Check`; `go doc ./internal/keys
   Kind`.
8. `tools/workflow/internal/serve/serve_test.go` (`do`, `newServer`, `artBody`) and
   `screen_outcome_test.go` (`modeScorer`, `artBodyAt`, `post`, `waitFor`): reuse, do not copy.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, a running `workflow serve` answers the four advisory reads of design 4 for
the key's tenant: the artifact read it already has (plus one additive field), the checks it loaded,
per-check baselines over the latest version of each artifact of a kind, and full-text search over
the latest screened content of each artifact.

## Contract

Cited, binding (design 4, API): "Service reads behind the tools. All need the key, all are scoped to
the key's tenant."

| Request | Response |
|---|---|
| `GET /v1/artifacts?repo_id=&path=` | `{"repo_id","path","kind","versions":n,"latest":{"content_hash","received_at","conversation_id","source","screen":{"verdict","scorer","at"}\|null,"scores":[{"check","score"}]}}`, or 404 |
| `GET /v1/checks?kind=` | `{"checks":[{"kind","name","q","levels","invert"}]}` |
| `GET /v1/baselines?kind=` | `{"kind","checks":{"<name>":{"n","p25","median","p75"}}}` over the latest version of each artifact of that kind |
| `GET /v1/search?q=&kind=&limit=` | `{"hits":[{"repo_id","path","kind","content_hash","snippet","rank"}]}` |

"`search` is SQLite FTS5 over the latest screened content of each artifact (`passed` or
`unscreened`), ranked by `bm25`, with `snippet()` for the excerpt; `limit` defaults to 10. Nothing
smarter in this round." Design 4, Scores and baselines: "The baseline is the tenant's median and
interquartile range per check for the same kind." Design 3, API: "Within `/v1`, changes are
additive only: new optional fields, new endpoints."

Decisions made at refine (settled):

- **Verdict names.** The code writes `pass` (3-02), not `passed`. Design 4's "`passed` or
  `unscreened`" means verdicts `pass` and `unscreened`. Never index or return `flag` content.
- **`/v1/artifacts` additive field.** `latest.rejection`: `{"stage","reason","at"}` from the most
  recent `rejections` row for the latest content hash, or `null`. This is how a Jev screen flag
  (which leaves the fact and deletes the content) reaches the agent; without it the shim would show
  "awaiting screen" forever. Every existing field and the 404 stay exactly as now. `at` is RFC 3339
  UTC, as `screen.at`.
- **`/v1/checks`.** Reads the checks `serve` loaded at start (3-01's `scorer.Checks`), passed in a
  new `Options.Checks *scorer.Checks` (nil = none loaded). `kind` empty: every kind (design, brief,
  report, in that order, each by name); `kind` one of `design|brief|report`: that kind; anything
  else: 400 `{"error":"kind must be design, brief or report"}`. `levels` is the array, `invert` a
  bool. With no checks loaded: 200 `{"checks":[],"loaded":false}`; with checks, add
  `"loaded":true` (additive, so the shim can say why the list is empty).
- **Checks loading in `main.go`.** Load `WORKFLOW_CHECKS_DIR` whenever it is set, key or no key; a
  load error refuses to start, naming the file (as now). The same `Checks` value feeds both
  `screen.Step`'s Jev and `Options.Checks`. No key and a checks dir: keep the line `workflow serve:
  scorer none; verdicts are unscreened` and add one line `workflow serve: checks design=N brief=N
  report=N`. Key handling, the other lines and `TestServeScorerWiring` stay as they are.
- **`/v1/baselines`.** `kind` required, one of the three, else 400. For every `(repo_id, path)`
  whose `keys.Kind(path)` is that kind, take the latest `artifact_version` (by `received_at`, then
  rowid, as `Artifact` does); for its content hash take the latest score per check (`id DESC`,
  first seen, as `Artifact` does). Per check: `n` = number of artifacts contributing, `p25`,
  `median`, `p75` by linear interpolation between closest ranks (the R-7 / numpy default: position
  `(n-1)·q` in the sorted values), rounded to 3 places. A check with no scores is absent. A kind with
  nothing scored: 200 `{"kind":k,"checks":{}}`. The service computes stats for any `n ≥ 1`; whether
  `n` is enough to flag is the shim's decision (4-02: no flags below `n = 4`).
- **Search index.** Append migration 2 (never edit migration 1): `CREATE VIRTUAL TABLE search USING
  fts5(content_hash UNINDEXED, body, tokenize='porter unicode61')`. One row per content hash, not
  per path, so a copy or rename to a new path with already-stored content (which never passes
  through `pending/` again) is still found. `Promote` inserts the row (delete any row for the hash,
  then insert) in the same writer transaction as the `screens` row, for verdicts `pass` and
  `unscreened`; content that is not valid UTF-8 is not indexed. `DropBlob` deletes the hash's row.
- **Backfill for existing tenant dbs.** When `Open` runs migration 2 on a db whose `user_version`
  was 1, it indexes every blob on disk whose latest `screens` row is `pass` or `unscreened`, before
  the writer starts. A fresh db (version 0) has nothing to backfill. Expose the rebuild as
  `(*Tenant).Reindex(ctx)` too (idempotent: clears and rebuilds), for tests.
- **Search query.** `q` is required (400 when it has no word characters). It is never passed raw to
  `MATCH`: extract runs of letters, digits and `_` (Unicode), at most 32, quote each, and join them
  with ` OR ` (bm25 ranks documents matching more terms higher). Hits: join the FTS rows to the
  latest *screened* version per `(repo_id, path)` (latest `artifact_version` whose content hash has
  a `pass` or `unscreened` `screens` row and no `rejections` row; `ROW_NUMBER() OVER (PARTITION BY
  repo_id, path ORDER BY received_at DESC, rowid DESC)` works in this SQLite), one hit per
  `(repo_id, path)`, ordered by `bm25(search)` ascending (lower is better; `rank` is that value).
  `snippet(search, 1, '[', ']', '…', 16)`. `kind` optional: empty means all; otherwise one of the
  three (else 400), filtered with `keys.Kind(path)` in Go while reading rows in rank order, stopping
  at `limit`. `limit` default 10, clamp to 1..50, non-integer is 400. No hits: `{"hits":[]}`.
- **Auth and errors.** All three new endpoints are `GET` only, behind the existing `auth` (401 on a
  missing or wrong key; tenant scoping comes from the key). Errors are `{"error": "<short>"}`; a
  500 never includes SQL text, content or the key.

## Changes

`internal/store`: migration 2, index maintenance in `Promote` and `DropBlob`, the backfill in
`Open`, `Reindex`, the latest-rejection read for `Artifact` (a `Rejection *RejectionRow` or similar
on `Latest`), and reads for baselines and search (names are yours; say them in the report). Tests in
`store_test.go`. `internal/serve`: `Options.Checks`, handlers for `/v1/checks`, `/v1/baselines`,
`/v1/search`, the `rejection` field, the percentile helper, and `reads_test.go`.
`cmd/workflow/main.go`: checks loading as above. `cmd/workflow/reads_wiring_test.go`: the binary
check below.

### Keep untouched

Migration 1's text (existing tenant dbs depend on its index of applied migrations). The ingest path,
the screen worker and backoff, `/v1/health` and `/v1/ingest` shapes, the hosted drain (`host.go`,
`watch_*.go`). Phases 1 to 3's tests must pass unchanged.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

Fail first: write `TestAdvisoryReads` (below) first and quote its failure (404 from the mux for the
new paths). Each subtest guards one risk named in its line.

- `go vet ./... && go test -race -count=1 ./...` → passes, including `TestServeOutcome`,
  `TestCaptureOutcome`, `TestScreeningOutcome` and `TestServeScorerWiring` unchanged.
- `go test -v -run TestAdvisoryReads ./internal/serve` → a `Server` on `t.TempDir()` with two
  tenants and a `modeScorer`/`scorer.Fake` that returns scores; one subtest per line, each printing
  PASS/FAIL:
  1. **artifacts shape**: every design 4 field present with the right JSON type; `rejection` is
     `null` for a passed artifact and `{"stage":"screen",…}` for a flagged one; 404 for an unknown
     path (guards breaking the shape 4-02 codes against).
  2. **checks**: with `Options.Checks` from `scorer.LoadChecks("../../../quality")`, `kind=report`
     returns 5 checks with `q`, `levels` (array), `invert` (bool); empty `kind` returns 27; `kind=x`
     is 400; with nil checks, `{"checks":[],"loaded":false}`.
  3. **baselines**: five designs with known scores for one check, one of which has a newer version
     with a different score → `n` 5 and the p25/median/p75 computed from the latest versions only
     (the superseded score is excluded); `kind` missing is 400 (guards baselining over history).
  4. **search**: a passed design containing a distinctive word is found with `snippet` containing
     `[word]` and `kind` `design`; an `unscreened` brief is found; a flagged design's content is
     not; after a newer version of the same path without the word is promoted, the path no longer
     hits; a second path with identical content (a copy, never pending) is a hit; `kind=brief`
     filters; `q` of `"(*:` is 400, not 500; `limit=1` returns one hit.
  5. **tenant scope**: tenant B's key sees none of tenant A's checks-independent data (artifact
     404, baselines empty, search no hits); no key is 401 on all three new endpoints.
  6. **backfill**: a tenant db created at `user_version` 1 (open it with a store built at migration
     1, or create the v1 schema by hand) holding an `unscreened` blob → after `Open`, search finds it.
- `go test -v -run TestReadsWiring ./cmd/workflow` → the built binary with `TYPESAFE_API_KEY=`
  (blank) and `WORKFLOW_CHECKS_DIR=../../../quality` on `127.0.0.1:0` (parse the `listening on`
  line, as `capture_test.go`'s `startHosted` does): stderr has `scorer none` and `checks design=11
  brief=11 report=5`; `GET /v1/checks?kind=design` with the key returns 11 checks.

Safety: temp dirs only (`t.TempDir()`), with `WORKFLOW_SERVE_DATA`, `WORKFLOW_QUEUE`, `HOME` and
`WORKFLOW_CLIENT_CONFIG` set to temp paths for any binary run. Never touch
`~/.local/share/workflow*`, `~/.config/workflow` or the legacy spool. Any `serve` you start listens
on `127.0.0.1:0` or another port that is not 8765 or 8770 and is killed after (`t.Cleanup`); confirm
none survive with `pgrep -f '<tempdir>'` before reporting. `TYPESAFE_API_KEY` is in your
environment: every child process gets `TYPESAFE_API_KEY=` (blank); never print, log, echo or write
it (no `env`, `printenv`, `set -x`). No Jev call is made in phase 4. Never print the test keys in
error messages either.

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 4: advisory reads in serve`
(the orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/4-01-service-reads.md` (design 1, Execution report: what was
done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), including the `TestAdvisoryReads` lines, the exact JSON of one response per endpoint
from the test (with a fake hash), and the store method names, and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
