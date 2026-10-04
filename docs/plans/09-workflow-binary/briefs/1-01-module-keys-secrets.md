---
brief_id: 210
design_id: 209
---

# Brief: 1-01 — Go module, keys and secret patterns

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its output is consumed by units
1-02 and 1-03 of this phase, and later by the drain (phase 2) and the shim (phase 4), which call the
same functions.
Owned paths: `tools/workflow/go.mod`, `tools/workflow/internal/keys/`,
`tools/workflow/internal/secrets/`, `docs/plans/09-workflow-binary/reports/1-01-module-keys-secrets.md`.
Touch nothing else.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing.
Runs alongside: nothing (1-02 and 1-03 follow; they change `go.mod`).
Budget: 6 files to read, about 500 lines to write including tests, 40 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/design/01-event-model-and-ingest.md` — Keys (lines 28-47) and Decisions 6 (lines 153-157). Binding.
2. `docs/design/03-remote-service.md` — Runtime (lines 15-34) and Deterministic precheck (lines 97-107). Binding.
3. `docs/design/02-edge-capture.md` — Scrub outcome and Scrub (lines 85-87, 109-110), Write surfaces kind patterns (lines 188-189). Binding.
4. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 1 (lines 141-153).
5. `tools/hooklog/hooklog.py` lines 27-31 — the legacy scrub regex, a starting point for the pattern set, not a contract.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

Create the `workflow` Go module and the two pure packages every later unit hashes and screens with:
`internal/keys` (design 1 keys and the path-to-kind rule) and `internal/secrets` (the one pattern
set "shared by the client scrub and the server precheck", DESIGN.md Phase 1 Surfaces).

## Contract

Settled by the design-intent docs; cite, do not reinterpret:

- Design 1 Keys: `repo_id` algorithm (origin, else first remote by name; drop scheme and `user@`;
  scp `host:path` → `host/path`; lowercase host; drop trailing `/` and `.git`; no remote →
  `root:` plus the lexically first root commit SHA). Path relative to `git rev-parse
  --show-toplevel` from the file's directory, `/` separators, outside any repo → no artifact.
  Content hash is SHA-256 of raw bytes. Row hash is SHA-256 of the fact's canonical JSON.
- Design 2 kind patterns: `docs/plans/<plan>/DESIGN.md` (design), `docs/plans/<plan>/briefs/*.md`
  (brief), `docs/plans/<plan>/reports/*.md` (report).
- Design 3 precheck pattern set: "the client scrub's patterns plus provider key formats, JWTs,
  connection strings with inline passwords, and `.env`-style assignments to names ending `KEY`,
  `SECRET`, `TOKEN` or `PASSWORD`". "The reason names the pattern and line, never the matched text."
- Design 3 Runtime: no cgo; standard library only for these two packages.

Decisions made at refine (settled; do not re-derive):

- Module path `github.com/codyhamilton/workflow-plugin/tools/workflow` (the repo's `origin`),
  created with `go mod init` from `tools/workflow/` using Go 1.27.1 at `~/.local/go/bin`.
- Row hash input: the fact JSON object with the top-level `id` (the drain's transport id,
  `<queue file>#<n>`) and `content` (artifact bytes, represented by `content_hash`) keys removed.
  Rationale: design 3 Ingest says the row hash is "computed from the envelope alone", and the
  stored raw envelope holds no content (design 3 Storage: "Rows hold the hash, never the bytes"),
  so a view can recompute the hash from the stored row.
- Canonical JSON: decode with `UseNumber` (numbers keep their literal text), object keys sorted,
  no insignificant whitespace, HTML escaping off, no trailing newline. Arrays keep order.
- One pattern set, applied identically by `Scan` and `Redact`.

## Changes

`tools/workflow/go.mod` — new, via `go mod init`. No dependencies in this unit.

`internal/keys` exports (names are a contract for 1-02, 1-03 and phases 2 and 4):

- `ContentHash(b []byte) string` — lowercase hex SHA-256.
- `Canonical(raw []byte) ([]byte, error)` — the canonical form above of a JSON object with `id` and
  `content` removed; error if `raw` is not a JSON object.
- `RowHash(raw []byte) (string, error)` — `ContentHash(Canonical(raw))`.
- `NormalizeRemote(url string) string` — pure; table-tested with at least
  `git@github.com:a/b.git`, `https://github.com/a/b`, `ssh://git@GitHub.com/a/b.git/`,
  `https://user:pw@host.example/x/y.git` → the forms design 1 gives.
- `RepoID(dir string) (string, error)` — runs `git` in `dir` per the algorithm.
- `RepoPath(file string) (repoTop, rel string, ok bool, err error)` — `ok=false` outside a repo.
  Resolve symlinks on both sides before relativising.
- `Kind(rel string) string` — `"design"`, `"brief"`, `"report"`, or `""`.

`internal/secrets` exports:

- `type Hit struct { Pattern string; Line int }` — 1-based line. Never carries matched text.
- `Scan(text string) []Hit` — every hit, in text order.
- `Redact(text string) string` — each match replaced by `[REDACTED:<pattern>]` (phase 2's hook-event
  scrub uses this).
- `Patterns() []string` — the stable pattern names.

Patterns (Go RE2, no lookbehind), each with a stable snake_case name that appears in reasons: private
key blocks (`-----BEGIN … PRIVATE KEY-----`), the legacy prefixes (OpenAI/Anthropic `sk-`, GitHub
`ghp_`/`gho_`/`ghs_`/`ghu_`/`github_pat_`, AWS `AKIA…`, Slack `xox?-`), other provider key formats
you can state precisely (for example Google `AIza…`, Stripe `sk_live_`/`rk_live_`), JWTs (three
base64url segments, first starting `eyJ`), `Bearer <token>`, connection strings with an inline
password (`scheme://user:password@host`), and `.env`-style assignments `NAME=value` /
`NAME: value` where `NAME` ends `KEY`, `SECRET`, `TOKEN` or `PASSWORD` (case-insensitive, optionally
quoted value).

Placeholders must not hit, because design and brief files in this repo discuss these variables:
an assignment value shorter than 8 characters, or one starting `$`, `<`, `{`, `…`, `...`, `*`, or
`x`-runs like `xxxx`, is not a secret. `WORKFLOW_SERVE_KEYS=a=ka,b=kb` (name ends `KEYS`) is not a
hit. Same for a connection string whose password is a placeholder.

### Keep untouched

Everything outside the owned paths. `tools/hooklog/` stays Python and is not edited; its regex is
reference only.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.
Run from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

- `go vet ./... && go test ./...` → passes.
- `go test -run 'Canonical|RowHash' -v ./internal/keys` → shows: key order and whitespace do not
  change the hash; adding or changing `id` or `content` does not change it; changing any other
  field does; a number like `1.700000000123456789e9` survives unchanged.
- `go test -run RepoID -v ./internal/keys` → in `mktemp -d` git repos (via `t.TempDir()`): scp and
  https remotes give the same ID; a repo with remotes `upstream` only uses it; a repo with no remote
  gives `root:<sha>`; two worktrees of one repo give the same ID. Set `GIT_CONFIG_GLOBAL=/dev/null`
  and a local user name/email in tests so the host's git config cannot leak in.
- `go test -run Scan -v ./internal/secrets` → one positive case per pattern, with the reported line
  correct in multi-line text; `Hit` and `Redact` output never contain the matched text; the
  placeholder cases above do not hit. Build test secrets by string concatenation at runtime so no
  committed source line is itself a credential-shaped literal.
- A test `TestRepoDocsClean` that, when run inside this repo, scans every `git ls-files '*.md'` file
  and fails listing `path:line pattern` (never the text) for any hit; skipped outside a repo. It
  passes. If a hit is a real credential, stop and report `blocked` without printing it.

Safety: test only in temp dirs (`t.TempDir()` or `mktemp -d`). Never read or write
`~/.local/share/workflow*`, the live queue, or the legacy service. Never print or log
`TYPESAFE_API_KEY` or any key.

Commit: title `[exec <execution_id>] Phase 1: Go module, keys and secret patterns` (the
orchestrator supplies the id; if it supplied none, use `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/1-01-module-keys-secrets.md` (design 1, Execution report:
what was done against this brief, verifiably; departures and why; unfinished work; known problems;
nothing derivable such as files touched or duration) and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
