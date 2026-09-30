# Event schema draft — minimal envelope

Version: `workflow_analytics_envelope` **v1** (lab). Collectors should accept unknown fields and optional `payload` keys.

## Envelope (all events)

```json
{
  "schema_version": 1,
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts": "2026-09-30T12:00:00.000000+00:00",
  "host_kind": "cloud",
  "host_detail": "cursor-cloud",
  "session_id": "bc-0d942d33-7e86-5b68-b969-cfcc54169a71",
  "repo": "github.com/codyhamilton/workflow-plugin",
  "plan": "docs/plans/06-phase-driver",
  "slug": "phase-driver",
  "phase": 1,
  "kind": "driver.trigger",
  "source": "tools/driver/run_record.py",
  "payload": {}
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `schema_version` | yes | Integer; currently `1` |
| `event_id` | yes | UUID v4; idempotency on collector |
| `ts` | yes | ISO-8601 UTC |
| `host_kind` | yes | `local` \| `cloud` \| `opencode` |
| `host_detail` | no | e.g. `cursor-cloud`, `claude-code-remote`, `desktop` |
| `session_id` | no | Harness session / cloud `bcId` when known |
| `repo` | no | Canonical repo URL or `owner/name` |
| `plan` | no | Plan folder path |
| `slug` | no | Design slug from `DESIGN.md` |
| `phase` | no | int or `"wrap-up"` / `"done"` |
| `kind` | yes | Namespaced string (table below) |
| `source` | no | Emitter script module path |
| `payload` | yes | Family-specific body (may be empty object) |

### `host_kind` detection (lab helper)

Implemented in [`proofs/dual_write_sink.py`](proofs/dual_write_sink.py):

| Condition | `host_kind` | `host_detail` |
|-----------|-------------|---------------|
| `WORKFLOW_INSTALL_MODE=opencode` | `opencode` | `opencode` |
| `CURSOR_AGENT=1` | `cloud` | `cursor-cloud` |
| `CLAUDE_CODE_REMOTE=true` | `cloud` | `claude-code-remote` |
| `CLAUDECODE` set | `local` | `claude-code` |
| else | `local` | `desktop` or unset |

Override: `WORKFLOW_ANALYTICS_HOST_KIND` for tests.

## `kind` namespace

| `kind` | Maps from | `payload` carries |
|--------|-----------|-------------------|
| `driver.trigger` | `run_record.entry_from_trigger` | `skipped`, `last_report`, `phase_dispatch` |
| `driver.assert` | `run_record.entry_from_assert` | `assert` slice (no full closing record) |
| `assert.live` | `.assert-log.jsonl` row | `question_id`, `state_hash`, `pass`, `jev`, `usage` |
| `jev.post_tool_batch` | `.jev-signal-log.jsonl` | Existing row minus duplicated top-level fields |
| `jev.subagent_stop` | same | Existing row |
| `jev.shadow` | proposal | `jev.question_id`, `jev.score` |
| `harness.check_skills` | `check_skills.py` | `ok`, `missing` |

## Compatibility with `.jev-signal-log.jsonl`

Existing rows already have `ts`, `kind`, `session_id`, `agent_id`, and nested `gate`. Migration path:

1. **Ingest as-is** into collector with `schema_version: 0` legacy flag, or  
2. **Wrap** at dual-write time: envelope fields + `payload` = full legacy row.

Lab proof uses (2) for new writes; local file may stay legacy until product wiring.

## Compatibility with `.run-record.jsonl`

Run record uses `record_version`, `kind` (`trigger` \| `assert`), and `ts`. Dual-write maps:

- `kind: trigger` → `driver.trigger`
- `kind: assert` → `driver.assert`

Keep appending the **existing** run-record shape locally for backward compatibility; emit envelope only on remote POST.

## Size and redaction

- Target **≤ 32 KiB** per POST (soft); hard reject at collector **256 KiB**.
- Do **not** ship full `closing_record.body` or transcript paths in remote `payload` by default; use hashes and counts (assert log already uses `state_hash`).
- Never ship `TYPESAFE_API_KEY`, `ANTHROPIC_API_KEY`, or `CURSOR_API_KEY`.

## Auth (remote)

| Env | Purpose |
|-----|---------|
| `WORKFLOW_ANALYTICS_URL` | HTTPS endpoint; unset = local only |
| `WORKFLOW_ANALYTICS_TOKEN` | Optional Bearer token |
| `WORKFLOW_ANALYTICS_LOCAL_LOG` | Override local JSONL path for lab sink (default: same as family-specific log) |
