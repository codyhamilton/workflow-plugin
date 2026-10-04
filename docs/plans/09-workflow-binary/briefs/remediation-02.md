---
brief_id: 238
design_id: 209
---

# Remediation 02: `env_assignment` precheck rejects ordinary plan prose

Severity: high. This is worse than the "loose" limit already recorded: it fires routinely on this
repo's own docs. Source: service-side review (`review-service.md`).
Owned paths: `tools/workflow/internal/secrets/secrets.go`, `tools/workflow/internal/secrets/secrets_test.go`.

The pattern set is shared: the client scrub (`internal/facts`, `secrets.Scan` and `secrets.Redact`)
and server ingest (`internal/ingest`) both use it. Coordinate with whoever owns the client side.
Both sides must pass after the change.

## Defect

`internal/secrets/secrets.go` line 37:

```
(?i)[A-Za-z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)["']?[ \t]*[=:][ \t]*["']?([^\s"']+)
```

The pattern has three problems:

- It is case-insensitive.
- It has no line anchor or word boundary.
- It accepts `:` as the separator.

So any prose of the form "<word ending in key/secret/token/password>: <token of 8 or more
characters>" matches, unless `placeholder` happens to excuse the value.

Scanning `docs/plans/*/{DESIGN,IMPLEMENTATION}.md`, briefs and reports, 8 of 57 files are rejected.
About 6 of those are benign prose. Examples:

- `docs/plans/06-*/DESIGN.md` line 99: "Trailer key: `Workflow-Phase:`"
- `briefs/3-02-*.md` line 111: "No key: `Options.ScreenStep`"
- `briefs/4-02-*.md` line 187 and `reports/4-02-mcp-shim.md` line 30: "secret: aws_access_key at
  line 3". The shim's own rejection message is itself rejected when an agent quotes it.

## Why it matters

The ingest precheck rejects the whole write, and the client scrub withholds the version. The skills
now tell agents to fix a rejection before going on, so agents will be pushed into rewriting
harmless prose. A false-positive rate near 10% of design documents also teaches people to ignore
rejections, which weakens the true positives.

## Fix approach (needs judgment)

- Match env-style names only: an uppercase identifier at the line start, or after
  `export `/whitespace/`"`, then `=` (for example `^\s*(?:export\s+)?[A-Z][A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)\s*=`).
- Keep a separate, stricter form for `:`: a quoted YAML or JSON key such as `"api_key": "..."` or
  `api_key: <value>` at line start, where the value has secret-like entropy or length.
- Treat values starting with a backtick, `<`, `$` or `{` as placeholders.
- Keep every existing positive test passing. The provider-specific patterns (`github_token`,
  `aws_access_key` and the rest) are unaffected.

## Done evidence

Run from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH` and `TYPESAFE_API_KEY=`.

- Fail first: add a corpus test. It reads the lines quoted above, or walks `../../docs/plans` and
  `../../docs/design` when present (skip if absent), and asserts zero `env_assignment` hits. Quote
  its failure before the fix.
- After the fix, the corpus test passes and every existing `secrets_test` positive case still
  matches.
- New positive cases match: `API_KEY=abcd1234efgh`, `export GITHUB_TOKEN="..."` and
  `"client_secret": "..."`.
- `go vet ./... && go test -race -count=1 ./...` passes, including the `facts` and `ingest`
  tests.
