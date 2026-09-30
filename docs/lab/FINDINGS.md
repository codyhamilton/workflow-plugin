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

## Template for future entries

```markdown
## YYYY-MM-DD — Title

### Observation (confidence)

- Fact with pointer to PR, log, or eval run.
```
