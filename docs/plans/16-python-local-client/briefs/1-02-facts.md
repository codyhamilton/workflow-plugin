# Brief: 1-02 — Fact building

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/client/yakka.py`, `plugins/yakka/client/test_facts.py`, `docs/plans/16-python-local-client/reports/1-02-facts.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push.
Report: before committing, write `docs/plans/16-python-local-client/reports/1-02-facts.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: 1-01.
Runs alongside: 1-04.
Budget: 10 files to read, about 1,100 lines to change, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Domain: Plugin client, the **`drain`.** bullet (lines 29), and Assumption 7 (lines 110-114).
2. `docs/design/02-edge-capture.md` — **Building facts**, **Commit facts**, **Scrub outcome**, **Scrub**, and **Write surfaces** (lines 66-87, 109-111, 189-202). Binding.
3. `docs/design/01-event-model-and-ingest.md` — Facts and Keys (lines 17-48). Binding. Fact wire names are the Go struct, not a fresh shape.
4. `packages/yakka/internal/ingest/ingest.go` — `Fact` and `Rename` JSON tags (lines 43-71). The wire shape.
5. `packages/yakka/internal/facts/facts.go` — `File`, `Output`, and `Build` (lines 45-56 and the file comment at lines 1-24), then the rest by grep.
6. `packages/yakka/internal/facts/facts_test.go` — the tests to port, including the fixture path near line 96.
7. `plugins/yakka/client/yakka.py` — only the callables 1-01 left: `Kind`, `ContentHash`, `RepoID`, `RepoPath`, `Scan`, `Redact`, `Canonical`, `RowHash`. Do not re-read the tests you are not changing.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Port fact building so the drain unit can turn a queue file into the same facts the Go client posts, including scrub and commit catch-up.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> **`drain`.** Same queue (`$YAKKA_QUEUE` or `~/.local/share/yakka/queue`), same `.drain.lock` flock, same fact building and client scrub, same `POST <endpoint>/v1/ingest` body `{"facts":[...]}` with `Authorization: Bearer <key>` when a key is set. Delivery follows [design 2](../../design/02-edge-capture.md): delete on `accepted` or `duplicate`; `rejected/` plus a `.reason` on a rejected fact; retry on 5xx, network error, 401, 403, 408; `Retry-After` on 429; split on 400 or 413; idle exit with rescan. Fact kinds, `repo_id`, content hash, and the secret scrub follow [design 1](../../design/01-event-model-and-ingest.md). The lock is the ported Go tests in `internal/clientconfig`, `keys`, `secrets`, `facts`, and `drain`, excluding `TestHostedRetriesLockAndWakes`, plus the drain half of `TestHalfSetEnvRefusal`. Cases in `cmd/yakka/drain_test.go` that boot `yakka serve` stay Go. Strings the ported tests assert are part of the contract.

This unit is the `facts` part of that lock. Design 2's delivery table is the drain unit's. From `facts.go`:

```go
// File is one queue file: its name and raw bytes.
type File struct {
	Name string
	Data []byte
}

// Output is the result for one File.
type Output struct {
	Name    string
	Facts   []json.RawMessage
	Reasons []string
}
```

> hook_event is always #0

and a fact id is `"<file name>#<n>"`. Python 3.10 and the standard library only.

## Changes

Add `File`, `Output`, `Build`, and `WritePaths` to `plugins/yakka/client/yakka.py`, using the 1-01 callables. Do not duplicate keys or secrets. `Build(ctx, files)` keeps the Go result: one `Output` per input, in order; `Facts` are JSON objects with the `ingest.Fact` tags; `Reasons` non-empty means the drain will reject the file after sending. A git failure skips that fact and is not a reason. git runs without a shell.

`test_facts.py` ports these Go tests and their asserted strings, importing `yakka`: `TestWritesFixtures`, `TestWritesCoalesceAndMissing`, `TestBadFiles`, `TestCommitFixtures`, `TestCommitDedupeInBatch`, `TestSecretScrub`, `TestSecretInCommittedBlob`, `TestWritePaths`. Read fixtures from `packages/hooklog/tests/fixtures/` the way `facts_test.go` does. Do not copy or edit the fixtures.

Write the failing tests before the port.

### Keep untouched

Do not change `Load`, `Path`, `ErrPartialEnv`, the key callables, the secret callables, `cmd_drain`, `main`, or the three test modules from 1-01. Do not implement `Run`, HTTP, or the `drain` command. Do not edit Go files, `spool.sh`, design 2, or the OpenCode plugin. Do not add a module or `__init__.py`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- From the repo root, `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'` → exit 0, including 1-01's modules.
- From `packages/yakka`, `go test ./internal/facts -count=1` → exit 0.
- `python3 plugins/yakka/client/yakka.py drain` still exits 2 with stderr `yakka drain: not implemented`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
