---
brief_id: 217
design_id: 209
---

# Execution report: 2-02 Fact building and client config

## Done

- `tools/workflow/internal/facts`: `Build(ctx, []File) []Output`, `File{Name, Data}`,
  `Output{Name, Facts []json.RawMessage, Reasons []string}`. Facts carry `id` `<Name>#<n>`
  (hook_event is `#0`). Contracts are in the package doc comment.
- `tools/workflow/internal/clientconfig`: `Load() (Config, error)`, `Config{Endpoint, Key}`, `Path()`,
  `ErrNoConfig`.
- `tools/hooklog/tests/fixtures/commit_calls.json`: `{"note","fixtures":[...]}`, 7 synthesized cases
  (extra `name` and `expect_commit` keys; placeholders `{{DIR}}`, `{{SHA7}}`).
- Tests: writes (all 11 `artifact_writes.json` payloads, coalescing, deleted file), commits (all
  fixtures, in-batch dedupe), secrets (worktree, committed blob, hook_event redaction), bad files, and
  an `ingest.Ingest` round trip on `store.Open(t.TempDir())` with no rejected result; clientconfig tests.

## Evidence

No failing check existed beforehand (new packages). After: `go vet ./... && go test ./...` passes in
`tools/workflow`; `-run 'Writes|Commit|Secret|Scrub' ./internal/facts` passes.

## Departures

- `diff-tree` runs with `-z` and `--no-commit-id` added, so paths with unusual characters are not
  quoted and no SHA line precedes the entries.
- Copy (`C`) lines in diff-tree contribute their destination to `paths` but not to `renames` or catch-up.
- Catch-up also covers type-change (`T`) lines.
- The "read once" coalescing is by a per-Build path cache; no test counts reads.
- Commit fact is emitted on the first file referring to a `(conversation, repo, sha)`.
- No `-C`/cwd base for a commit means no commit fact (never the process cwd).

## Unfinished / known problems

- Fixtures are synthesized and unverified against real harness output.
- Config file mode 0600 is not enforced on read.
