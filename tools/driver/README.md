# Phase driver

Deterministic phase closure and one-phase dispatch for the Grok Bot loop (`docs/plans/06-phase-driver/DESIGN.md`, spike B in `docs/lab/ANALYSIS/2026-09-30-grokbot-driver-reorient.md`).

## Status (read-only)

```bash
python3 tools/driver/status.py docs/plans/06-phase-driver/
python3 tools/driver/status.py docs/plans/06-phase-driver/ --default-branch master
```

Stdout is JSON only. Resolution uses:

- `### Phase` headings in `DESIGN.md` (phase count)
- `Workflow-Phase: <slug>:<n>` and `Workflow-Phase: <slug>:done` trailers on commits in `git log <default>..HEAD`

Malformed or wrong-slug trailers are ignored. Does not read `IMPLEMENTATION.md`.

## One-phase trigger (`--once`)

Grok Bot owns the loop: resolve → dispatch **one** fresh phase session → read report → decide whether to call again. The driver **never commits**.

```bash
python3 tools/driver/run.py docs/plans/06-phase-driver/ --once --dry-run
python3 tools/driver/run.py docs/plans/06-phase-driver/ --once \
  --fixture-output tools/driver/tests/fixtures/agent_outputs/phase2_unsuccessful.txt
```

Stdout is JSON:

| Field | Meaning |
|-------|---------|
| `status` | Same object as `status.py` at dispatch time |
| `skipped` | `true` when `open` is already `done` |
| `dispatch` | Target (`phase` / `wrap-up`), review posture, plan path |
| `report` | Parsed `workflow-report` (`status`, `phase`, `reason`) |
| `turns`, `cost_usd` | From the provider SDK when live; `0` in dry-run |
| `provider`, `mode` | `dry-run` when no headless key or `--dry-run` |

### Provider selection

| Environment | Behaviour |
|-------------|-----------|
| No `ANTHROPIC_API_KEY` / `CURSOR_API_KEY` | **Dry-run** (default): returns `incomplete` with an explicit reason — not a fake `closed`. |
| `ANTHROPIC_API_KEY` only | Selects Claude adapter (live dispatch: Phase 2 plan — not implemented in this spike). |
| `CURSOR_API_KEY` only | Selects Cursor adapter (live dispatch: Phase 3 plan — not implemented in this spike). |
| Both keys set | Requires `--provider claude` or `--provider cursor`. |

Use `--dry-run` or `--fixture-output <file>` to prove the report contract in CI and bot harnesses without pretending live work ran.

### Harness adapters (pluggable)

`tools/driver/providers/` defines a small `PhaseProvider` interface (`run_phase` → final output text + turns/cost). Implementations:

- `dry_run.py` — contract tests and bot environments without headless keys
- `claude.py` — Claude Agent SDK (stub until Phase 2)
- `cursor.py` — Cursor cloud / headless agent (stub until Phase 3)

Live providers must return final output containing exactly one ` ```workflow-report ` JSON fence (see `skills/execute/SKILL.md`).

## Grok Bot integration

Typical unattended loop (shell or tool calls):

1. **Read ground truth** — `python3 tools/driver/status.py <plan-folder>` → `open`, `phase`, `closed[]`.
2. If `open` is `done`, stop.
3. **Trigger one phase** — `python3 tools/driver/run.py <plan-folder> --once` (with keys for live, or `--dry-run` in dev).
4. Read `report.status`:
   - `closed` → call `status` again (trailers should advance on the branch; driver does not commit).
   - `incomplete` → re-dispatch once per design, then escalate.
   - `unsuccessful` → escalate to a human; do not auto-continue.
5. Repeat from step 1.

MCP-shaped RPC (stdio JSON lines or one-shot for simple bots):

```bash
# One-shot (stdout JSON)
python3 tools/driver/mcp_server.py status --plan-folder docs/plans/06-phase-driver
python3 tools/driver/mcp_server.py trigger_phase --plan-folder docs/plans/06-phase-driver --dry-run

# Line-delimited JSON-RPC on stdin (method: status | trigger_phase | poll)
python3 tools/driver/mcp_server.py --stdio
```

`poll` is a no-op for sync providers (dry-run and future sync SDK calls). Async Cursor dispatch can use it in Phase 3+.

### Kill line (this environment)

No headless `ANTHROPIC_API_KEY` or `CURSOR_API_KEY` is available in the workflow-plugin CI/agent VM. **Live dispatch is not claimed here.** Spike B ships the provider interface, dry-run path, fixture-driven contract tests, and Grok Bot call documentation. Nesting-only harnesses that could run `execute` as a subagent gain no benefit from an extra process until a headless key is configured on the bot host.

## Tests

```bash
python3 -m unittest discover -s tools/driver/tests -p 'test_*.py'
```
