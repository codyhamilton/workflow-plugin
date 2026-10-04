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

## Carried

None.
