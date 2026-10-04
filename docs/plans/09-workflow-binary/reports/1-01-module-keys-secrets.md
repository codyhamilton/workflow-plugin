# Execution report: 1-01 Go module, keys and secret patterns

Status: done.

## Done against the brief
- `tools/workflow` module created with `go mod init` (path `github.com/codyhamilton/workflow-plugin/tools/workflow`, go 1.27.1); no dependencies.
- `internal/keys`: `ContentHash`, `Canonical`, `RowHash`, `NormalizeRemote`, `RepoID`, `RepoPath`, `Kind` as specified.
- `internal/secrets`: `Hit`, `Scan`, `Redact`, `Patterns` with 12 named patterns: private_key_block, sk_key, github_token, github_pat, aws_access_key, slack_token, google_api_key, stripe_key, jwt, bearer_token, connection_string, env_assignment.
- Evidence: the tests were written first and failed to compile (undefined symbols) before the implementation. Afterwards `go vet ./... && go test ./...` passes, including `TestRepoDocsClean` over every tracked `*.md` (no hits, so no real credential was found; it ran, not skipped).
- Test secrets are built by runtime concatenation.

## Behaviour choices (within the brief)
- Matches from all patterns are merged; on overlap the earlier, then longer, match wins. `Scan` and `Redact` use this same merged set, so they always agree. A private key block reports the line of its `BEGIN` header.
- `sk-` and the other prefixes use a leading `\b`, so words like `task-...` do not hit (the legacy regex would).
- Connection-string passwords: no length rule, but `$`/`<`/`{`/`*` prefixes, x-runs and the words password/pass/pwd/secret/changeme are placeholders. The assignment pattern also applies the under-8-character rule.
- `RepoPath` returns `ok=false` with nil error for any `git rev-parse` failure in an existing directory; it errors if the directory does not exist or `git` is missing.
- `RepoID` picks `origin`, else the lexically first remote name.

## Departures
None.

## Known problems
- The assignment pattern is loose: any name ending KEY/SECRET/TOKEN/PASSWORD with a value of 8 or more characters hits, for example prose like `token: something-long`. The repo docs are clean today; later docs may need placeholders.
- `RepoPath` for a file whose directory does not yet exist returns an error rather than `ok=false`.
