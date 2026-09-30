# Phase driver

Deterministic phase closure and bot-callable primitives for the Grok Bot loop (`docs/plans/06-phase-driver/DESIGN.md`). Policy: [`docs/lab/ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../../docs/lab/ANALYSIS/2026-09-30-grokbot-driver-reorient.md).

## How Grok Bot discovers and drives the workflow

Plugin **skills** (`design`, `execute`, …) are installed separately (`install.sh`, SessionStart hook, or Cursor project skills). They are **not** visible to Grok Bot until that install step runs in the consuming repo — see [`docs/lab/CONSUMING_REPO.md`](../../docs/lab/CONSUMING_REPO.md).

The **driver** is a small Python toolkit the bot calls in a fixed loop:

| Step | CLI (today) | Purpose |
|------|-------------|---------|
| 1 | `status.py <plan-folder>` | Read-only JSON: open phase, closed trailers, `done` |
| 2 | `run.py <plan-folder> --once` | One fresh phase session; returns `workflow-report` + cost |
| 3 | `assert_phase.py --state …` | Typed alignment on compact phase state; fail → stop and escalate |
| 4 | Repeat 1→3 until `open` is `done` or report is `unsuccessful` |

Session classify (`tools/transcript/classify.py`) is optional visualisation only — not part of this loop.

Provider keys for step 2: `ANTHROPIC_API_KEY` or `CURSOR_API_KEY` (design). The driver never commits.

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

## Assert (phase boundary, step 3)

Compact **state JSON** (not a transcript snapshot): closing-record headings and body, `design_outcome` for the phase, `workflow_report`, and the `trailer` just observed. Built by the driver/bot after a phase returns — not by `classify.py`.

```bash
python3 tools/driver/assert_phase.py --dry-run --state tools/driver/fixtures/assert/pass_state.json
python3 tools/driver/assert_phase.py --state state.json --live   # TYPESAFE_API_KEY; appends JSONL
python3 tools/driver/assert_phase.py --fixture-jev tools/driver/fixtures/assert/pass_jev_response.json \
  --state tools/driver/fixtures/assert/pass_state.json
```

- **Model:** TypeSafe Jev pin `jev-1.13.0` when `TYPESAFE_API_KEY` is set; `--dry-run` (or no key) prints the request JSON only.
- **Log:** `tools/driver/.assert-log.jsonl` (gitignored), separate from `tools/transcript/.classify-log.jsonl`.
- **Question:** `outcome-evidence` — Score on whether the closing record evidences the design outcome; documented pass threshold **≥ 2.5** on the Jev score.
- **Pass/fail (authoritative):** deterministic checks on the same state (report `closed`, trailer/report phase match, Verification + Carried headings, outcome or substantive verification text).
- **Fail branch:** `stop_and_escalate` — the bot must not treat `workflow-report.status: closed` as permission to continue when assert fails.
- **Kill line:** if Jev disagrees with the deterministic result on fixtures, **keep deterministic** and log `jev.disagreed_with_deterministic` (see `fixtures/assert/fail_state.json` + `fail_jev_response.json`).

Fixtures: `tools/driver/fixtures/assert/` (`pass_state.json`, `fail_state.json`).

## Grok Bot integration

Typical unattended loop (shell or tool calls):

1. **Read ground truth** — `python3 tools/driver/status.py <plan-folder>` → `open`, `phase`, `closed[]`.
2. If `open` is `done`, stop.
3. **Trigger one phase** — `python3 tools/driver/run.py <plan-folder> --once` (with keys for live, or `--dry-run` in dev).
4. Read `report.status`:
   - `closed` → build compact state and run **`assert_phase.py`**; on fail or `stop_and_escalate`, escalate — do not auto-continue.
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
