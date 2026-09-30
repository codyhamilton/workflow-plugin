# Findings log

Append-only, dated notes. Prefer facts and pointers over speculation. Confidence: **high** / **medium** / **low**.

---

## 2026-09-30 — Lab workspace seeded; plugin + classify baseline

### Plugin map (high)

- **Core `workflow`:** version **2.5.0** (`/.claude-plugin/plugin.json`) — skills `design`, `refine`, `execute`, `comprehensive-review`, `close-out`, `post-build`.
- **Lab `workflow-lab`:** version **1.1.0** — `setup`, `iterate`, `transcript-parser`, `workflow-tuning`.
- **Evals:** harness documented in `evals/README.md`; **fixture corpus empty** (no `scenarios/` populated in repo yet).
- **Phase driver:** described in `docs/OVERVIEW.md` as `tools/driver/` — **not present in tree**; design lives in `docs/plans/06-phase-driver/DESIGN.md` (medium).
- **Transcript toolkit:** `tools/transcript/` — extract, stats, cost, search, `iterate_analysis.py` (regex phase skim); **classify spike landed on master** (`classify.py`, `lib/snapshot.py`, `lib/jev_client.py`, pin `jev-1.13.0`).

### Jev transcript classify — live batch (high for numbers, medium for label quality)

Eight sessions classified 2026-09-30 (UTC) into `tools/transcript/.classify-log.jsonl` (see attached export used for this seed). Model **jev-1.13.0**; each row includes `session_kind` (Choice) and `workflow_alignment` (Score 0–3).

| source | session_id (prefix) | kind | conf | align score | snapshot tok est | input_tokens |
|--------|---------------------|------|------|-------------|------------------|--------------|
| claude-code | d006f5a0 | workflow | 0.82 | 2.1 | 284 | 1244 |
| claude-code | af9b5cb1 | build | 0.73 | 2.25 | 694 | 2111 |
| claude-code | 30844998 | workflow | 0.85 | 2.46 | 878 | 2351 |
| claude-code | bd4f6c0d | plan | **0.30** | 2.29 | 496 | 1692 |
| cursor | 1dc10dd4 | ops | 0.93 | 1.47 | 110 | 838 |
| cursor | 77572779 | ops | **0.45** | 0.81 | 109 | 834 |
| cursor | a2be9531 | workflow | **0.62** | 1.2 | 143 | 872 |
| cursor | eac38429 | question | **0.41** | 1.16 | 103 | 831 |

**Spot-check verdict (medium):** labels are **mostly plausible** (workflow/build/ops/question mix matches heterogeneous sessions). Four rows fall **below 0.8 confidence** on `session_kind` — treat as **review-gate** candidates, not auto-metrics.

**Claude vs Cursor snapshot shape (medium):** Claude-code rows show **higher `snapshot_token_estimate`** (284–878) than Cursor (103–143) at similar `input_tokens` ~800–870 for Cursor vs ~1.2k–2.3k for Claude. Hypothesis: **Claude extract text is distorted** (reported “newline-per-char” bug in snapshot user-message fields) — needs fix in snapshot builder or parser, not taxonomy change. See proposal `PROPOSALS/2026-09-30-snapshot-claude-text-join.md`.

**Workflow alignment score (low–medium):** Scores cluster ~1–2.5; several runs show **moderate Score confidence** (e.g. 0.46–0.68) even when Choice confidence is high — do not use Score alone for gates until calibrated.

### Design spike (high)

Pre-implementation spike doc: Jev Choice over ≤~4k token snapshot, optional Score in same request, JSONL logging with `human_label` — aligned with merged code. API: TypeSafe System One, pin `jev-1.13.0`. Primary refs: [docs.typesafe.ai](https://docs.typesafe.ai/), [jevtypesafeai.com how-to-use](https://www.jevtypesafeai.com/how-to-use).

### Operating hypotheses (medium)

Root `README.md` lists eight falsifiable hypotheses; most still **untested** in cloud-pipeline context. Eval empty → hypotheses remain observational only.

---

## 2026-09-30 — Classify batch measurement (superseded for prioritisation)

Full numbers and taxonomy notes: [`ANALYSIS/2026-09-30-strategy-pass.md`](ANALYSIS/2026-09-30-strategy-pass.md). No proposal promoted from that pass. The chart above remains valid; driver work does not wait on blind labels or snapshot parity.

---

## 2026-09-30 — Control and measurement reoriented to Grok Bot

### Policy (high)

Cody's updated remit, written through in [`ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](ANALYSIS/2026-09-30-grokbot-driver-reorient.md) and reflected in `GOALS.md` / `BACKLOG.md` / `RESEARCH/`:

- Optimise three layers: the workflow, observability, and **end-to-end control by Grok Bot** (or an equivalent unattended driver).
- Jev is for **assert hooks** (alignment, logging, steering at phase boundaries).
- `classify.py` is **visualisation** of session kind. The 8-row batch earlier in this file stays a sample chart. Its sub-0.8 rows and the Claude snapshot-size hypothesis are **not** blockers.
- Composer collects observations; Grok writes strategy. This entry is the strategy pass.

### Ranked next engineering steps (high as priorities, untested as outcomes)

1. Read-only phase **status** JSON from `Workflow-Phase:` trailers.
2. Bot-callable **one-phase trigger** (CLI `--once` or MCP).
3. One **Jev assert** with a fail branch; kill if it disagrees with a deterministic check.
4. External **run record** (report, cost, asserts) — no status file in the plan folder.
5. **SessionStart** / cloud install so core skills exist with no human prompt.
6. One **outcome row** (verifier + trailers + cost) that classify does not gate.

Success metrics and kill lines are in the analysis doc. No driver code landed with this pass.

### Proposals (high)

| Proposal | Status after this pass |
|----------|------------------------|
| `2026-09-30-jev-hook-assertion-spike.md` | **proposed** — retargeted to a steering assert |
| `2026-09-30-first-eval-scenario.md` | **proposed** — score is verifier + cost |
| `2026-09-30-classify-human-label-workflow.md` | **deferred** |
| `2026-09-30-snapshot-claude-text-join.md` | **deferred** |
| `2026-09-30-spike-design-archive.md` | **deferred** (POC archive) |

---

## 2026-09-30 — Phase status CLI (spike A / step 1)

### Observation (high)

- **`tools/driver/status.py`** resolves `open` (`phase` | `wrap-up` | `done`), `phase`, `closed[]`, and `done` from `DESIGN.md` `### Phase` count and `Workflow-Phase:` trailers on `git log <default>..HEAD` only — no `IMPLEMENTATION.md`, no LLM.
- **Kill line:** open phase does not depend on IMPLEMENTATION prose; trailer contract in `skills/execute/SKILL.md` is sufficient.
- **Tests:** `python3 -m unittest discover -s tools/driver/tests` — mid-plan, wrap-up, done, malformed trailer ignored (git fixtures on a branch ahead of default).
- **Usage:** `python3 tools/driver/status.py docs/plans/06-phase-driver/ [--default-branch master]`

---

## 2026-09-30 — One-phase trigger (spike B / step 2)

### Observation (high)

- **`tools/driver/run.py --once`** resolves via `status.py` / `resolve.py`, dispatches **one** phase or wrap-up through `tools/driver/providers/` (`dry-run` when no `ANTHROPIC_API_KEY` / `CURSOR_API_KEY`; Claude/Cursor stubs until design Phases 2–3), parses `workflow-report`, returns JSON with `turns` / `cost_usd` / `mode`. Does not commit.
- **Dry-run kill line honoured:** default without keys returns `report.status: incomplete` and an explicit reason — not `closed` pretending work ran. Fixture path `tools/driver/tests/fixtures/agent_outputs/phase2_unsuccessful.txt` proves unsuccessful parsing.
- **MCP-shaped:** `tools/driver/mcp_server.py` one-shot (`status`, `trigger_phase`) or stdio JSON lines; `poll` returns not in-flight for sync providers.
- **Grok Bot loop:** documented in `tools/driver/README.md` — bot calls `status` → `run.py --once` → reads report → repeats; human on `unsuccessful`.
- **Live dispatch:** not available in the plugin CI/cloud agent VM (no headless provider keys). Bot host must supply `ANTHROPIC_API_KEY` or `CURSOR_API_KEY` before unattended multi-phase runs can close trailers without human `execute`.

---

## 2026-09-30 — Phase assert CLI (spike C / step 3)

### Observation (high)

- **`tools/driver/assert_phase.py`** evaluates compact phase state (`closing_record`, `design_outcome`, `workflow_report`, `trailer`) — not session classify.
- **Jev** pin `jev-1.13.0`; `--dry-run` / missing `TYPESAFE_API_KEY` prints request JSON; `--live` appends `tools/driver/.assert-log.jsonl` (separate from classify).
- **Pass/fail** is **deterministic** (Verification + Carried headings, phase/trailer alignment, outcome or substantive verification text). Jev Score threshold documented at **≥ 2.5** for logging; **fail branch** `stop_and_escalate`.
- **Kill line exercised:** `fixtures/assert/fail_state.json` fails deterministic while fixture Jev score 3.0 would pass — bot must follow deterministic (`jev.disagreed_with_deterministic`).
- **Tests:** `python3 -m unittest discover -s tools/driver/tests`.

---

## 2026-09-30 — Run record (step 4)

### Observation (high)

- **`tools/driver/run_record.py`** appends one JSON object per `run.py --once` / `assert_phase.py` invocation to a log **outside** the plan folder (`tools/driver/.run-record.jsonl` by default, or `DRIVER_RUN_RECORD` / `--record`).
- **Kill line:** record entries omit `closed[]` and other git-duplicative status; open phase still comes from `status.py` + trailers only.
- **Resume:** `status.py --run-record PATH` merges `run_record` rollup (`last_report`, per-phase `turns`/`cost_usd`, `last_assert`, `total_cost_usd`) so a fresh bot session can state phase (git), last report status, and cost without transcripts or classify.
- **CLI:** `record_cli.py` summarizes JSONL; tests in `test_run_record.py`.

---

## 2026-09-30 — Unattended core-skill bootstrap (step 5)

### Observation (high) — Cursor cloud enters a prebaked image

This cloud agent (`bc-f6673c0c-cb02-5af9-95c3-8e239f425b54`) booted from snapshot `bld-20260930-898776ef-818d-45ac-831f-6cd727afc323` (`gitSetup: reuse`, `warmFork: warm_fork`). `environmentJsonPath` is null (db-backed personal environment, not a repo `.cursor/environment.json`).

At process start, before any install:

- `CURSOR_AGENT=1`, hostname `cursor`, `~/.cursor/plugins/cache/.cloud-plugin-manifest.json` present. No TTY; `/dev/tty` does not open. No `CLAUDECODE`, `CLAUDE_CODE_REMOTE`, or `CLAUDE_CODE_ENTRYPOINT`.
- `./install.sh --print-route` → `route: cursor-cloud`, `core_only: true`, `dest: /workspace/.cursor/skills/workflow`, `reason: CURSOR_AGENT=1`.
- `python3 tools/driver/check_skills.py` exited **1**. `skills_found` was empty; `missing` was `design`, `refine`, `execute`, `comprehensive-review`, `close-out`, `post-build`. `~/.claude/skills/` was also absent.
- The session skill list did not include those six names (Cursor built-ins under `~/.cursor/skills-cursor/` only).

**Kill line for this harness:** hooks are the wrong layer. Cursor cloud has no SessionStart hook and no `reloadSkills`. Project skills are discovered when the agent process starts, so an install during the first turn cannot make that turn list core skills. Bake core-only `install.sh` into the environment image (`docs/lab/bootstrap/cursor-cloud-setup.sh`, `WORKFLOW_INSTALL_MODE=cloud`), snapshot, and require `check_skills.py` to exit 0 on the next boot **before** the first prompt. This spike did not rebuild the image.

### Claude Code on the web (not observed live)

Claude's own hooks doc sets `CLAUDE_CODE_REMOTE=true` on the web and honors SessionStart `reloadSkills`. That is the right layer for a fresh container per session. This VM is Cursor, so that path was not executed against a live Claude container. A consuming repo copies `docs/lab/bootstrap/session-start.sh` (same bytes as the root README heredoc) and merges `docs/lab/bootstrap/claude-settings-fragment.json`. The hook no-ops when `CLAUDE_CODE_REMOTE` is unset. The installer then writes core skills to `~/.claude/skills/` and does not install lab.

### Installer and check (high)

- Explicit `WORKFLOW_INSTALL_MODE=cloud|claude-code|interactive` wins over ambient signals, so an image bake is not captured by a stray `CLAUDECODE`, and a Claude hook is not captured by `HOSTNAME=cursor`.
- Unset mode keeps the previous order: Claude signals, then Cursor signals, then piped or non-interactive → workspace `.cursor/skills/workflow/`. Core only on those routes.
- `.gitignore` again ignores `.cursor/skills/workflow/` (the entry was replaced by `__pycache__/` in `bd92ef2`).
- `check_skills.py` is the bot gate: JSON `{ok, harness, skills_found, missing, skills_root}`, exit 0 iff each core skill dir contains `SKILL.md`. Lab is not required. No network. Disk presence stands in for a chat skill list, which this spike cannot automate.
- Tests: `python3 -m unittest discover -s tools/driver/tests` (route matrix, core-not-lab copy with `WORKFLOW_INSTALL_SKIP_REFRESH=1`, hook no-op vs `reloadSkills`, setup script).

---

## 2026-09-30 — First outcome row (step 6)

### Observation (high)

Fixture stand-in, not a live multi-phase dogfood. No `ANTHROPIC_API_KEY` or `CURSOR_API_KEY` in this environment. Classify was not called. The quality signal is the verifier exit code (trailer completeness + deterministic assert), not a person reading a diff.

- **Command:** `python3 evals/scenarios/trailer-completeness/verify.py` (bot stand-in: `status.py` → `run.py --once` → `assert_phase.py --deterministic`).
- **Verifier:** **pass** (exit 0). Checks: status pass, trailers pass, once pass (skipped — history already `done`), assert pass (`decision_source: deterministic`, exit 0).
- **Trailers:** `trailer-completeness:1`, `trailer-completeness:2`, `trailer-completeness:done`. `other-slug:1` is on the fixture branch and is not in `closed`.
- **Status:** `open: done`, `closed: ["trailer-completeness:1", "trailer-completeness:2"]`, `done: true`.
- **Cost:** unavailable — no `ANTHROPIC_API_KEY` or `CURSOR_API_KEY`. Dry-run `cost_usd: 0` was not recorded as a provider cost. Live Claude/Cursor adapters are still stubs, so a key in this tree would not have produced a dollar figure either (`cost.reason` then contains "not implemented"; the trailer row still passes).
- **Artifacts:** `evals/scenarios/trailer-completeness/` (`source.md`, `reference/expected.json`, `reference/assert_state.json`, frozen `baseline/outcome.json`). Negative check: `--omit-trailer trailer-completeness:2` exits 1.
- **Tests:** `python3 -m unittest discover -s tools/driver/tests -p 'test_*.py'` (includes `test_outcome_scenario.py` and `assert_phase.py --deterministic`).

---

## 2026-09-30 — Cheap-Jev judgement white paper (draft)

### Observation (high)

- Proposal [`PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) (`status: draft`) records four soft signals: PostToolBatch size/progress, post-refine brief complexity, unit-complete “needs review?”, phase-complete alignment sanity.
- Inputs: research pack [`RESEARCH/2026-09-30-jev-cheap-judgement-signals/`](RESEARCH/2026-09-30-jev-cheap-judgement-signals/INDEX.md). Maps Claude evidence cited there: **16%** of 150 subagents over the ideal band; densest 5h window **~63.35M** tokens; worker `92a48e004519` at **296** API calls.
- No hook and no `assert_phase` behaviour change. Spikes wait until Cody accepts. Deterministic phase kill line stays authoritative.
- **Proofs landed (4/4):** [`RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/`](RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/README.md) — `run_proofs.sh` validates PostToolBatch probe, gate simulation, Jev schema dry-runs, measurement recipe. White paper rewrite deferred to Grok.

---

## 2026-09-30 — Cheap-Jev judgement white paper (resolved)

### Observation (high)

- Proposal [`PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) rewritten to `status: resolved`. Recommendations accepted pending product wiring. Default hooks, driver, `assert_phase`, and `classify.py` are unchanged. Remaining work is implementation.
- Accepted gate: `band_exit` at **76** turns; handoff at **85** / **125k** peak / **3MiB**; escalate at **100** / **130k** / **5MiB**. Optional Jev when `jev_eligible` (handoff and turns ≥ 85 or peak ≥ 128k or transcript ≥ 3MiB). Simulation on workers `92a48e004519` and `bb6165018de0` trips all four flags. Source: proofs on master `112ccfe` (PR #24).
- Schemas in `proofs/jev_signal_schemas.py` are the contracts (`session-progress`, `refine-brief-complexity`, `unit-needs-review`, `phase-alignment-sanity`). Weekly skim recipe is the ops rule. `assert_phase --deterministic` stays the kill line. Classify stays a POC.
- **LCD harness (closed):** host `codyh-ubuntu`, checkout `112ccfe`, OpenCode 1.18.33 + `deepseek/deepseek-flash`. `run_proofs.sh` exit 0; gate checks true; unittest 6/6; fixture wrote 1 `post_tool_batch` row (`handoff_signal` and `jev_eligible`). OpenCode cannot fire Claude `PostToolBatch` command hooks (per-tool execute before/after only). Live `.jev-signal-log.jsonl` on OpenCode skipped. Live logging is Claude Code, or a custom OpenCode plugin that aggregates `tool.execute.after`. The fixture probe is the LCD stand-in.

---

## Template for future entries

```markdown
## YYYY-MM-DD — Title

### Observation (confidence)

- Fact with pointer to PR, log, or eval run.
```
