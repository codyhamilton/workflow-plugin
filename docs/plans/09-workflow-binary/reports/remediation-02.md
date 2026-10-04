# Report: Remediation 02 (brief 238)

Status: done.

## Change

`tools/workflow/internal/secrets/secrets.go`: `env_assignment` is now two regexes under one name.

- Env form: an uppercase identifier ending in KEY, SECRET, TOKEN or PASSWORD, preceded by line start, whitespace, a quote, a backtick or `(`, optional `export`, then `=`. Case-sensitive. `:` is no longer accepted here.
- Colon form (YAML/JSON): a quoted key, or a key at line start (optional list dash), then `:`. The value must be at least 16 characters and contain a digit, and must not be a placeholder.
- A leading backtick now marks a placeholder value (`$`, `<` and `{` already did).
- `Patterns()` collapses adjacent duplicate names, so it still lists `env_assignment` once.

## Evidence

Fail first (before the fix), from `go test ./internal/secrets`:

- `TestEnvAssignmentProse`: "Trailer key: `Workflow-Phase:`", "No key: `Options.ScreenStep`" and "secret: aws_access_key at line 3" each hit.
- `TestEnvAssignmentCorpus`: 14 false-positive lines across the docs corpus.

After: both pass, as do all existing positive and placeholder cases, the new positive cases (`API_KEY=abcd1234efgh`, an `export`ed GITHUB_TOKEN, a quoted client_secret key) and `TestRepoDocsClean`.

`go vet ./...` and `go test -race -count=1 ./...` were run with an empty TYPESAFE_API_KEY.

## Departure

The corpus test skips two lines that are genuine NAME=value examples quoted on purpose: `TYPESAFE_API_KEY=sentinel...` in brief 5-01 and the brief's own `API_KEY=abcd1234efgh` example. They are real assignments, correctly matched, and the docs are outside this brief's owned paths.
