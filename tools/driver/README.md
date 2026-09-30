# Phase driver

Deterministic phase closure and bot-callable primitives for the Grok Bot loop (`docs/plans/06-phase-driver/DESIGN.md`). Policy: [`docs/lab/ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../../docs/lab/ANALYSIS/2026-09-30-grokbot-driver-reorient.md).

## How Grok Bot discovers and drives the workflow

Plugin **skills** (`design`, `execute`, …) are installed separately. They are **not** visible until that install has already landed on disk — see [`docs/lab/CONSUMING_REPO.md`](../../docs/lab/CONSUMING_REPO.md).

| Harness | Bootstrap | Why |
|---------|-----------|-----|
| Cursor cloud | `docs/lab/bootstrap/cursor-cloud-setup.sh` in the **image** install, then snapshot | Agents boot from a prebaked image. Skills are read at process start. There is no session hook. |
| Claude Code on the web | Copy `docs/lab/bootstrap/session-start.sh` + settings fragment | Fresh container per session. `reloadSkills` makes the install visible on that session. |

Both paths install **core only** (never `workflow-lab`). `WORKFLOW_INSTALL_MODE=cloud` or `claude-code` forces the route.

The **driver** is a small Python toolkit the bot calls in a fixed loop:

| Step | CLI (today) | Purpose |
|------|-------------|---------|
| 0 | `check_skills.py` | Exit 0 iff the six core skill dirs exist for this harness |
| 1 | `status.py <plan-folder>` | Read-only JSON: open phase, closed trailers, `done` |
| 2 | `run.py <plan-folder> --once` | One fresh phase session; returns `workflow-report` + cost |
| 3 | `assert_phase.py --state …` | Typed alignment on compact phase state; fail → stop and escalate |
| 4 | `status.py --run-record …` (optional) | Merge external run record: last report, per-phase cost, last assert |
| 5 | Repeat 1→4 until `open` is `done` or report is `unsuccessful` |

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

## Run record (step 4)

One JSON object per driver invocation, **outside** the plan folder (Invariant 3 unchanged). Git trailers remain ground truth for which phase is open; the record holds what git cannot: provider **turns/cost**, the **last `workflow-report`**, and **assert** slices.

Default log: `tools/driver/.run-record.jsonl` (gitignored). Override with `--record PATH` on `run.py` / `assert_phase.py`, `--run-record PATH` on `status.py`, or env `DRIVER_RUN_RECORD`.

| Field in record | Kept? |
|-----------------|-------|
| `last_report` (`status`, `phase`, `reason`) | yes |
| `phase_dispatch` (`turns`, `cost_usd`, `provider`, `mode`) per invocation | yes |
| `assert` (`pass`, `question_id`, `fail_branch` when fail) | yes |
| `closed[]`, `open`, IMPLEMENTATION prose | **no** (kill line — use git via `status.py`) |

`run.py --once` appends a `trigger` line and echoes the same object under `run_record` in stdout JSON. `assert_phase.py` appends an `assert` line when `--fixture-jev` or `--live` runs.

Summarize without git:

```bash
python3 tools/driver/record_cli.py --record /tmp/driver-run.jsonl --plan-folder docs/plans/06-phase-driver
```

Fresh session (phase from git, status/cost from record):

```bash
python3 tools/driver/status.py docs/plans/06-phase-driver/ --run-record /tmp/driver-run.jsonl
```

Stdout adds `run_record`: `{ last_report, phases, total_cost_usd, last_assert, … }` alongside the usual git-derived fields.

## Core skills check (step 5 bootstrap)

```bash
python3 tools/driver/check_skills.py
./install.sh --print-route    # route JSON only; does not copy or fetch
```

`check_skills.py` prints JSON and does not use the network:

```json
{
  "ok": true,
  "harness": "cursor-cloud",
  "skills_found": ["design", "refine", "execute", "comprehensive-review", "close-out", "post-build"],
  "missing": [],
  "skills_root": "<workspace>/.cursor/skills/workflow"
}
```

| `harness` | `skills_root` |
|-----------|----------------|
| `cursor-cloud` | `<workspace>/.cursor/skills/workflow/<skill>/SKILL.md` |
| `claude-code` | `~/.claude/skills/<skill>/SKILL.md` |
| `interactive` | none — unattended install did not run; `ok` is false |

Exit 0 only when `ok` is true. A skill counts when `<skill>/SKILL.md` is a file. Lab skills are ignored. Detection matches `install.sh` (explicit `WORKFLOW_INSTALL_MODE`, then Claude signals, then Cursor cloud signals or a non-interactive shell). This is disk presence, not a claim that the harness listed the skills in chat.

## Grok Bot integration

Typical unattended loop (shell or tool calls):

0. **Bootstrap once per fresh container / image**, then **`python3 tools/driver/check_skills.py`**. Stop if it exits non-zero — do not dispatch `execute` without core skills.
1. **Read ground truth** — `python3 tools/driver/status.py <plan-folder>` → `open`, `phase`, `closed[]`.
2. If `open` is `done`, stop.
3. **Trigger one phase** — `python3 tools/driver/run.py <plan-folder> --once` (with keys for live, or `--dry-run` in dev).
4. Read `report.status`:
   - `closed` → build compact state and run **`assert_phase.py`** (pass `--record` or `DRIVER_RUN_RECORD`); on fail or `stop_and_escalate`, escalate — do not auto-continue.
   - `incomplete` → re-dispatch once per design, then escalate.
   - `unsuccessful` → escalate to a human; do not auto-continue.
5. **`status.py --run-record`** when resuming in a new session — open phase from git, last report status and cumulative cost from the record.
6. Repeat from step 1 (re-run step 0 only after a fresh container).

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

Includes `check_skills.py` and `install.sh --print-route` / core-only copy (`WORKFLOW_INSTALL_SKIP_REFRESH=1`, no network).
