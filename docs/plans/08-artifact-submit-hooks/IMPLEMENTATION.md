# Artifact submit hooks implementation

Tool: Codex, direct build on `cursor/artifact-submit-hooks-0368`.
Run identity: branch plus starting HEAD `7361b726cce4df178f06ed01f94701353204651c`.
Started: 2026-10-04 (Australia/Brisbane).

The signed design is design 172. The user forbids ledger creation/updates for it,
agents, other checkouts, PRs, merges, and edits to DESIGN.md. These constraints
override execute's dispatch, brief creation, execution logging, and close-out
defaults. All three phases are being built directly and verified with isolated
test services, without contacting the live ledger.

## Phase 1 — Shared submit helper and predicate

Built `artifact_submit.py`: strict plan paths, service-only submission predicate,
hashing shared with lifecycle, correlated post APIs, parent design resolution,
advisory output, and hooklog outcome posting/spooling. Session artifacts now
expose `submission_bound` so execution-only joins cannot suppress a post.
Reposting an older body updates its latest-body timestamp (A → B → A).

Verification: `python3 -m unittest discover -s tools/quality/tests -p
'test_artifact_submit*.py'` initially failed on two fixture assumptions (non-git
root fallback and the shared environment's bearer token); both fixtures were
corrected. Re-run with `PYTHONWARNINGS=ignore::ResourceWarning`: 15 tests passed.
Python 3.14 emitted existing SQLite connection ResourceWarnings in the first run.
Tests use an ephemeral HTTP port and isolated service directory; the decoy local
directory cannot suppress posting to that HTTP store. No live ledger was used.

Execution id: none; lifecycle logging was not attempted because this direct
build explicitly forbids ledger work for design 172.

## Phase 2 — Harness wiring

Built registrations after hooklog on Claude/Codex PostToolUse, Cursor postToolUse
and afterFileEdit, including the standalone Cursor example. OpenCode invokes the
same Python helper after its tool log and leaves tool outputs unchanged. Its bus
events never invoke submission. `quality.py hook` delegates to the HTTP helper;
manual score remains available. Native fixture replay covers both designs and
briefs, including encoded Cursor args and Codex apply_patch input. Duplicate
Cursor surfaces and repeated MultiEdit paths are suppressed by the same predicate.

Session HTTP responses expose submission events, including posted_design, and
decode URL-encoded conversation ids. These small service changes make the
design's predicate and operator visibility observable through the named API.

Verification (WORKFLOW_QUALITY_URL empty at test-process start; all integration
tests select isolated ephemeral servers):

- Hook surface fixture suite: 5 tests passed.
- Full quality suite: 24 passed; after adding real HTTP error/timeout and encoded
  conversation coverage, 26 passed.
- Full hooklog suite: 21 passed, including all shipped registration smoke checks.
- OpenCode Python batch suite: 5 passed.
- OpenCode Node callbacks: 2 passed, including actual Python helper spawning,
  exactly one post then zero, bus/read exclusion, and helper failure handling.
- `git diff --check`: passed.

The HTTP fixture drains in-flight handlers before restoring store/environment
patches, keeping timeout tests isolated. ResourceWarnings from existing SQLite
connection handling are filtered during regression runs.

## Phase 2 Carried

None.

## Carried

None.
