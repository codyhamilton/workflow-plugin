# Strategy pass: Grok Bot driver, asserts, measurable outcomes

**Date:** 2026-09-30 (Australia/Brisbane)  
**Author:** Workflow Optimiser (Grok strategy pass)  
**Status:** current policy for `docs/lab/`  
**Supersedes:** the measurement and control emphasis in the same-day lab seed (classify-as-KPI, human coordinator as the default driver).

---

## Decision

Continual improvement of workflow-plugin uses published research plus outcomes we can observe on a run. The optimisation scope is three layers:

1. **The workflow** — cloud-safe core skills, verbatim briefs, phase trailers, cold reads.
2. **Observability** — facts a fresh process can read: git trailers, the phase report, provider cost, assert logs.
3. **Control** — an automated driver. **Grok Bot** (or an equivalent unattended agent) owns the loop. A person is the escalation target when a phase reports `unsuccessful`, not the default dispatcher of `execute`.

**Jev** (TypeSafe, pin `jev-1.13.0`) is for **assert hooks**: alignment checks, structured logs, and steering at phase boundaries. `tools/transcript/classify.py` stays a **visualisation** of session kind. Classify calibration, human-label gates, and Claude/Cursor snapshot parity are **not** blockers and are **not** success metrics.

**Collection vs strategy:** Composer (or an equivalent cheap collector) gathers transcripts, trailers, costs, and assert rows. Grok does this kind of strategy pass. Do not spend a strategy model on batch labeling.

The agent-orchestrated path in `docs/plans/06-phase-driver/DESIGN.md` stays valid where a harness already has two levels of nesting. The path we build and measure next is the one a bot can call: resolve from trailers, dispatch one fresh phase, read a report, decide.

---

## What this pass changes in the notebook

| Doc | Change |
|-----|--------|
| `GOALS.md` | Remit and metrics follow the three layers above. |
| `BACKLOG.md` | P0 is bot-callable status and dispatch; classify work is deferred. |
| `FINDINGS.md` | This decision recorded; the classify batch stays as a viz sample. |
| `RESEARCH/` | Takeaways remapped onto the bot, hooks, trailers, and asserts. |
| Classify proposals | `deferred` or `poc`. Assert spike stays active and is retargeted. |

No runtime code in this pass.

---

## Research implications (refined)

Sources are the same library as [`../RESEARCH/2026-09-30-workflow-systems.md`](../RESEARCH/2026-09-30-workflow-systems.md). The mapping below is what we will act on.

### Control loop

| Source | Refined implication | Conf. |
|--------|---------------------|-------|
| [ReAct](https://arxiv.org/abs/2210.03629) | The **bot** alternates a short reason step with an environment action: read status, trigger one phase, read the report and trailers, repeat. Phase workers still act inside `execute`. The bot does not absorb the phase transcript. | high |
| [LangGraph orchestrator–worker / supervisor](https://docs.langchain.com/oss/python/langgraph/workflows-agents) | Grok Bot is the supervisor node. `tools/driver/` (CLI loop or MCP one-phase) is the edge. Checkpoints are `Workflow-Phase:` trailers, already specified in the phase-driver design. | high |
| [AutoGen conversation programming](https://arxiv.org/abs/2308.08155) | The bot's "conversation" is tool calls (`status`, `trigger_phase`, `assert`), not a human chat that restates briefs. | high |
| [SWE-agent ACI](https://arxiv.org/abs/2405.15793) | Two interfaces, both designed on purpose. **Workers** see skills, briefs, and trailers. **The bot** sees a small CLI/MCP and JSON. Measuring only chat labels misses the bot interface. | high |
| [OpenHands SDK](https://docs.openhands.dev/sdk) (event log, confirmation) | The event log we can afford is driver stdout + assert JSONL + git. Headless `design` (assumption ledger) is the confirmation path for unattended runs. Interactive checkpoints are the human path. | medium |
| Phase-driver design (in-repo) | Phase closure is already a pure function of git + `DESIGN.md`. That function is the bot's ground truth. The `workflow-report` fence is the one-shot signal. MCP returns after one phase so the bot keeps the loop. | high |

### Hooks and cloud-safe skills

| Source | Refined implication | Conf. |
|--------|---------------------|-------|
| README `SessionStart` hook | A fresh cloud container has no prior `~/.claude/skills/`. Unattended sessions need that hook (or an image bake / Cursor `install.sh` into `.cursor/skills/`) **before** the bot asks for `execute`. The hook belongs on the consuming repo or the bot image, as the README already says. | high |
| Core vs lab split (`docs/OVERVIEW.md`) | The bot installs **core only**. Lab skills (`iterate`, `workflow-tuning`) are optional local tools. Core skills must keep headless defaults so a bot never blocks on a question. | high |
| [OpenHands security confirmation](https://arxiv.org/html/2511.03690v2) | Risky or ambiguous stops (`unsuccessful`, approach-open, design bounce) return to the bot, which escalates. They do not open an interactive prompt inside the phase agent. | medium |

### Measurement

| Source | Refined implication | Conf. |
|--------|---------------------|-------|
| [SWE-bench](https://www.swebench.com/SWE-bench/) | A scenario is measured by a **verifier** (command, artifact rubric, or trailer completeness) plus cost. Session-kind accuracy is not that verifier. | high |
| [LangGraph evaluator–optimizer](https://docs.langchain.com/oss/python/langgraph/workflows-agents) | Generate → evaluate → revise maps to phase verify, `comprehensive-review`, and re-dispatch. The cheap typed evaluate step is a **Jev assert** on compact phase state. | high |
| [TypeSafe / Jev](https://docs.typesafe.ai/) | Choice/Score/Noul over a small JSON `state`, inside token budget, logged with the pin. Use it where a deterministic check is awkward (outcome evidence present, brief matches contract) **and** a wrong steer is bounded. Where git already answers (trailer exists, phase index), do not call Jev. | high |
| Classify POC (`tools/transcript/classify.py`) | Useful as a **chart** of what kinds of sessions we run. It does not gate merges, evals, or the bot. Snapshot distortion and sub-0.8 rows stay noted in FINDINGS and do not block the driver. | high |
| README hypothesis #8 | The number the driver exists to print is **turns and cost per phase** from the provider. That is the observational test of "fresh orchestrator per phase." | high |

### Deprioritised readings

These were reasonable for the seed pass and are now parked:

- Calibrating `session_kind` against `human_label` before any other metric.
- Treating Claude vs Cursor snapshot token parity as a precondition for evals.
- Human-in-the-loop as the primary way phases advance.
- Merging session-kind taxonomy with `iterate_analysis.py` phase regex.

---

## Ranked next steps

Each step is the smallest thing that changes what the bot can do or what we can claim. Stop at the kill line; do not widen the spike to "finish the driver."

### 1. Read-only phase status the bot can call

Deterministic resolver: plan folder + `git log <default>..HEAD` trailers + `DESIGN.md` phase count → JSON `{open: phase|wrap-up|done, phase, closed[]}`. No model, no SDK, no writes. Shape matches Phase closure in `docs/plans/06-phase-driver/DESIGN.md`.

- **Success metric:** on a fixture set with known trailers, status JSON matches a hand resolution for every case (mid-plan, wrap-up, done, malformed trailer ignored). A bot or a stand-in script consumes the JSON without opening `IMPLEMENTATION.md`.
- **Kill line:** if "which phase is open" still depends on prose in `IMPLEMENTATION.md`, stop and fix the trailer contract in `execute` before any dispatch loop.

### 2. One-phase trigger the bot owns

CLI or stdio MCP: `trigger_phase` runs one fresh phase session (provider by key, as in the design) and returns the `workflow-report` plus turns/cost. The bot decides whether to call again. Default is one phase per call, matching the design's MCP front end.

- **Success metric:** an unattended bot run takes a signed-off design of at least two phases to the `done` trailer, or stops at the first `unsuccessful`, with **zero human `execute` dispatches**. Each phase line in the log has turns and cost.
- **Kill line:** if no headless provider key is available to the bot, stop and record the missing key. Do not simulate dispatch inside the strategy session. If a harness the bot already uses can nest coordinator → `execute` → workers and a separate process only adds latency, ship status (step 1) and leave trigger as a design note.

### 3. One Jev assert that can steer

A single typed question over compact state the driver already has (for example: phase-outcome evidence is present in the closing record, or the report's `phase` matches the trailer just written). Log JSONL (`question_id`, answer, confidence, `snapshot_hash`, jev pin). The bot or driver takes a documented fail branch. Session kind is not the question.

- **Success metric:** one pass fixture and one fail fixture; the assert agrees with the fixture label at the documented threshold; the fail fixture produces a logged row and a fail branch (stop or re-dispatch once).
- **Kill line:** if the assert disagrees with a deterministic check that was available in the same state (false steer on the fixture set), delete the Jev call and keep the deterministic check. Do not open a classify-calibration effort to "save" it.

### 4. Run record the next session can read

One JSON object per driver invocation, on stdout or a log **outside** the plan folder: phases closed, last report, per-phase cost, assert results. Invariant 3 stands — nothing in the repo carries status.

- **Success metric:** a fresh bot session, given only the repo plus that record, states current phase, last status, and cost without reading a transcript and without calling classify.
- **Kill line:** any field that duplicates git trailers or `IMPLEMENTATION.md` is cut. If nothing remains but cost, report reason, and assert results, that is the record.

### 5. Unattended core-skill bootstrap

For the harness Grok Bot actually starts: Claude Code on the web uses the existing `SessionStart` installer hook; Cursor cloud uses non-interactive `install.sh` into project-local skills. Document the bot's expected path in FINDINGS once observed.

- **Success metric:** a fresh container's first turn lists core skills (`design`, `refine`, `execute`, `comprehensive-review`, `close-out`, `post-build`) with no human prompt and without lab skills required.
- **Kill line:** if the bot only enters a prebaked image, hooks are the wrong layer — bake `install.sh` (core only) into the image and close the spike.

### 6. One outcome row that classify does not gate

A single dogfood or `evals/scenarios/` run scored by trailer completeness, a verifier command or artifact rubric, and provider cost. Classify output may be attached as a picture of the session.

- **Success metric:** one FINDINGS row with verifier pass/fail, cost, and trailer list, reproducible by the bot path in steps 1–2.
- **Kill line:** if the only quality signal is a person reading the diff, write that down and leave the scenario empty. Do not substitute `session_kind` agreement.

---

## Engineering spikes (concrete)

These are the build shapes for steps 1–3. They follow `docs/plans/06-phase-driver/DESIGN.md` and stay smaller than Phases 2–4 of that plan.

### Spike A — `workflow status` (step 1)

```
python3 tools/driver/status.py <plan-folder> [--default-branch main]
```

Stdout JSON only:

```json
{
  "plan": "docs/plans/06-phase-driver",
  "slug": "phase-driver",
  "open": "phase",
  "phase": 2,
  "closed": ["phase-driver:1"],
  "done": false
}
```

`open` is `phase`, `wrap-up`, or `done`. Malformed trailers are omitted, not errors. Exit 0 when resolution succeeds, non-zero when `DESIGN.md` has no phase headings. No network.

### Spike B — bot-callable phase primitive (step 2)

Same provider layer as the design, two front ends, bot uses the second:

| Call | Behaviour |
|------|-----------|
| CLI `python3 tools/driver/run.py <plan> --once` | Resolve, run **one** phase or wrap-up, print report and cost, exit. |
| MCP `status` | Spike A. |
| MCP `trigger_phase` | One fresh session; return report or `incomplete`. |
| MCP `poll` | In-flight dispatch, if the provider is async. |

The full-loop CLI (`run.py` without `--once`) can wait until `--once` has been driven by the bot twice. Grok Bot is the loop owner in the first milestone.

Provider selection stays key-based (`ANTHROPIC_API_KEY`, `CURSOR_API_KEY`). The bot's environment must hold one of them. The driver still never commits.

### Spike C — assert hook (step 3)

```
python3 tools/driver/assert_phase.py --state state.json --question outcome-evidence
```

`state.json` is built by the driver from the closing record's headings, the expected phase outcome line in `DESIGN.md`, and the trailer just observed — not from a chat snapshot. Request JSON is checkable in `--dry-run` with no API key. Live POST appends to a gitignored assert log, separate from `.classify-log.jsonl`.

Hook placement: after the phase agent returns, before the bot treats `closed` as permission to continue. A failed assert downgrades the bot's next action to stop-and-escalate even if the report said `closed`, until the kill line in step 3 says the assert is unsafe.

### Spike D — what we will not build in the next spike

- Human-label workflow for classify.
- Snapshot join fixes as a gate.
- A LangSmith-style trace UI.
- Per-turn Jev calls inside worker loops.
- A status file inside `docs/plans/<slug>/`.

---

## Suggested order for Cody

Ship **A**, then **B** against a two-phase fixture, then **C** on that same fixture's closing record. Bootstrap (**step 5**) can proceed in parallel if the bot's harness is already known. The outcome row (**step 6**) is the first run of B that we keep.
