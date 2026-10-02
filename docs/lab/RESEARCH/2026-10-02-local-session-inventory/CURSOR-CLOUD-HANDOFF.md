# Cursor cloud-run local cache handoff

Checked 2026-10-03. These counts describe this machine's local Cursor cache at inspection time.

## Verified stores and coverage

- Cursor global state DB (`~/.config/Cursor/User/globalStorage/state.vscdb`), `ItemTable` key `cloudAgentRepository.agents.*`: 430 distinct `bc-*` run metadata records. Fields include ID, timestamps, remote workspace path, name, and status. No message stream or turn count is present in those records.
- Same DB, `cursorDiskKV` `bcCachedDetails:*`: 67 blobs. Wire inspection of sample large blobs showed file paths and before/after file contents: file diff caches, not conversation message records.
- `~/.config/Cursor/User/globalStorage/conversation-search.db`: 430 `cloud-cache` `bc-*` search rows. Only 16 had nonempty flattened indexed body text at inspection. This is an incomplete, unstructured search index and cannot certify turns or a full transcript.
- No `bc-*` parent JSONL under `~/.cursor/projects/*/agent-transcripts/`, and no `bc-*` transcript file path was found under the inspected Cursor config/cache trees. Other remote or local stores were not ruled out.

## Tool support added

- `python3 tools/transcript/find.py --all --tool cursor-cloud` discovers local cloud-run metadata.
- `python3 tools/transcript/extract.py BC_ID --tool cursor-cloud` returns metadata with `transcript_available: false`, `indexed_text_available`, and null turn counts. Search of a cloud-run transcript rejects with an explicit unavailable-body error.
- `python3 tools/transcript/find.py --all --tool cursor --min-parent-assistant-turns 60` filters local JSONL sessions by observed parent assistant rows. Unknown counts are excluded with a per-source stderr count. `--tool cursor-cloud` with that filter excludes all cached cloud runs because their turn counts are unknown.
- `latest` with default `--tool all` continues to choose a readable transcript rather than cloud metadata. An explicit `--tool cursor-cloud` can choose its latest metadata record.

## Limits and next work

The parser does **not** pull complete cloud transcripts or calculate cloud turns. Any >=60 cloud-run cohort remains unmeasured. To add one, find an authoritative complete message stream for `bc-*` runs, establish assistant-turn semantics from its schema, verify coverage against these 430 IDs, then add extraction and threshold filtering based on observed rows. Keep partial search-index text separate from that stream.

Focused Cursor tests and `git diff --check` passed. Changes are uncommitted.

## Update 2026-10-03: later, deeper search (supersedes "no message stream" above)

A second pass over `state.vscdb` `cursorDiskKV` found local-chat-format composer and bubble rows for some cloud runs:

- 3 runs have a complete local transcript (`composerData` linked via `createdFromBackgroundAgent.bcId`, all bubbles present): `bc-5c140900` (33 bubbles), `bc-0a7f75bc` (155), `bc-8976074d` (69).
- `bc-c8f24931` has 97 bubble headers and no bodies (likely evicted); two more runs have only stray bubbles. These stay unknown.
- 16 runs have flattened search-index text only (no tool calls); turn counts from it are lower bounds.
- 19 of 430 runs have any body; **411 have none locally.** Working hypothesis (unverified): Cursor syncs cloud-run content lazily, only for runs loaded locally. The recoverable runs are therefore a self-selected sample.
- Full transcripts exist server-side and in the cloud VM (`/tmp/cursor/cloud-agent-transcripts/<ts>/<bc>/transcript.json`); API export is enterprise-only. A cloud agent can read run data, not yet tested.

`cursor-cloud` now reports `transcript_available`, `transcript_complete` and `transcript_store`, with exact `parent_*` turn counts only when every header has a bubble; all other counts stay null (unknown, not zero).
