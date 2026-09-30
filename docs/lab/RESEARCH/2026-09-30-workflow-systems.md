# Deep dive: How agentic / LLM workflow systems are designed

**Date:** 2026-09-30 (Australia/Brisbane)  
**Author:** Workflow Optimiser (seed; implications revised the same day)  
**Scope:** Patterns that inform workflow-plugin — not a framework comparison for greenfield apps.

**Policy (later the same day):** Grok Bot (or an equivalent unattended driver) owns the loop. Jev is for phase-boundary asserts. Session classify is visualisation. Authoritative write-up: [`../ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../ANALYSIS/2026-09-30-grokbot-driver-reorient.md). Sections 4–8 below match that policy.

---

## 1. Problem framing

Software agents today combine **language reasoning**, **tool execution**, and **multi-step control flow**. Production systems differ mainly in:

1. How **state** is represented (chat history vs graph state vs event log).
2. How **work is decomposed** (fixed workflow vs dynamic planner).
3. How **quality is checked** (tests, human review, LLM judges, typed evaluators).
4. How **risk is gated** (sandbox, confirmations, checkpoints).

workflow-plugin already encodes a **predetermined workflow** (design → refine → execute per phase → review → close-out) with **dynamic work** inside each phase (brief-routed workers). Research below maps external patterns onto that shape.

---

## 2. Planner–executor and orchestrator–worker

### ReAct: interleaved thought and action

[ReAct (arXiv:2210.03629)](https://arxiv.org/abs/2210.03629) shows LLMs performing better when **reasoning traces** and **actions** alternate: thoughts plan and recover; actions fetch environment feedback.

**Implication (high confidence):**

- **Grok Bot** holds a short reason step over status and the last report, then takes one environment action (`trigger_phase`). It does not absorb the phase transcript.
- **`execute`** contexts emphasise tool use bounded by briefs — the phase orchestrator reasons on artifacts, workers act on code.
- **Diagnosis** uses trailers, the `workflow-report`, per-phase cost, and assert logs. Transcript tools remain available for worker-level forensics.

### Orchestrator–worker (LangGraph pattern)

[LangChain: Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) describes **orchestrator–worker**: a planner spawns variable subtasks (often via parallel `Send`), then aggregates results.

**Implication (high confidence):**

- **Grok Bot** is the supervisor across phases and does no phase work. **`execute`** is the orchestrator for a **single phase** and dispatches workers per brief.
- **`iterate`** (lab, not on the bot's required path) is orchestrator–worker with an **unknown worker count**.
- **Risk:** supervisor misrouting and worker echo loops — mitigated by **disjoint brief ownership**, **phase trailers**, and a bot that only advances when status says the phase closed.

### SWE-agent: the interface is the product

[SWE-agent (arXiv:2405.15793)](https://arxiv.org/abs/2405.15793) argues LM agents need tailored **agent–computer interfaces** (ACI), not raw shell alone.

**Implication (high confidence):**

- Skill markdown + brief templates + git trailers are the **worker** ACI.
- The **bot** ACI is a small CLI/MCP: `status`, `trigger_phase`, and an assert result. Optimising control means designing that surface, not labeling chats.
- **`transcript-parser`** still extracts cost when the provider did not print it. **`classify.py`** can show whether the mix of session kinds shifted; it does not measure the bot ACI.

---

## 3. Graphs, conversations, and state

### LangGraph: explicit graphs with cycles

[LangGraph multi-agent workflows (LangChain blog)](https://www.langchain.com/blog/langgraph-multi-agent-workflows) models agents as **nodes**, control as **edges**, supports cycles (retry, repair) and hierarchical teams (subgraphs).

**Implication (medium confidence):**

- Core workflow is a **linear graph** with optional bounce (`refine` → `design`). `iterate` adds **cycles** (diverge → judge → reconcile) off the unattended path.
- `tools/driver/` checkpoints are the **`Workflow-Phase:` trailers** already specified in `docs/plans/06-phase-driver/DESIGN.md`. The bot resumes from git, not from a carried transcript. A person is resumed only on `unsuccessful`.

### AutoGen: conversation as program

[AutoGen (arXiv:2308.08155)](https://arxiv.org/abs/2308.08155) composes **conversable agents** with programmable patterns (two-agent, group, nested).

**Implication (high confidence):**

- **Briefs routed verbatim** ≈ AutoGen messages with fixed recipients — aligns with README hypothesis #2 (briefs beat messengers). The bot routes the plan folder; it does not paraphrase the brief.
- **Unattended design** uses the headless assumption ledger. Interactive checkpoints remain the human path.
- v0.4’s event/actor model ([Microsoft Research article](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/)) maps onto driver events (report, cost, assert) rather than a second transcript store.

### OpenHands SDK: production agent stack

[OpenHands SDK documentation](https://docs.openhands.dev/sdk) and [SDK architecture paper (arXiv:2511.03690)](https://arxiv.org/html/2511.03690v2) emphasise **typed tools**, **workspaces** (local vs remote sandbox), **event-sourced conversations**, and **security confirmation** before risky actions.

**Implication (medium confidence):**

- **`workflow` core** is what an unattended session installs (SessionStart hook, Cursor `install.sh`, or image bake). **`workflow-lab`** stays off that path.
- **`post-build`** QA + exact-SHA deploy proof ≈ OpenHands-style confirmation before irreversible ops, invoked by the bot as a stage rather than by a person watching the terminal.
- **Condenser / context management** lessons support README hypothesis #8 (cost ∝ context × turns) — a fresh phase session, started by the driver, is our condenser. The bot's own context stays on status and reports.

---

## 4. Evaluator–optimizer and harnesses

### Evaluator–optimizer loop

LangGraph docs name **evaluator–optimizer**: generate → evaluate → revise until acceptable.

**Mapping (high confidence):**

| Plugin stage | Evaluator role |
|--------------|----------------|
| Per-phase verify in `execute` | Cheap-tier outcome check |
| Jev assert hook | Typed steer on compact phase state, logged |
| `comprehensive-review` | Premium evaluator on whole design |
| Remediation briefs + bot re-dispatch | Optimizer pass |
| `evals/` harness | Offline evaluator on verifier + cost |
| Jev `classify.py` | Optional **chart** of session kind, not a gate |

### SWE-bench style verification

[SWE-bench](https://www.swebench.com/SWE-bench/) applies patches in Docker and runs tests ([evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/)).

**Implication (high confidence):**

- Outcome rows declare **verifiers** (command, file rubric, or trailer completeness). A human sign-off is an escalation, not the default grader.
- The bot's phase run is inference. Grading is the verifier plus provider cost — same separation as SWE-agent inference vs SWE-bench eval.

### Typed eval with Jev (TypeSafe)

[TypeSafe docs](https://docs.typesafe.ai/) — Choice / Score / Noul over JSON `state`; [budget limits](https://www.jevtypesafeai.com/how-to-use).

**Implication (high confidence):**

- Use Jev where a **closed assert** on compact phase state can steer the bot (outcome evidence present, report consistent with the trailer) and a wrong answer is bounded by the kill line in the strategy pass.
- Where git already decides (trailer present, phase index), skip Jev.
- Session-kind Choice in `classify.py` may still be batched for visualisation. It is not a review gate and it does not block the driver. The 2026-09-30 classify batch in FINDINGS is a chart, including its low-confidence rows.

---

## 5. Escalation (human on `unsuccessful` only)

Sources: AutoGen human-input modes; OpenHands security/confirmation; LangGraph interrupt/checkpoint patterns (practitioner cookbooks).

**Implication (medium confidence):**

- The **default driver is the bot**. Interactive `design` remains available for a person; the bot declares headless and gets the assumption ledger.
- **`unsuccessful`** (approach-open, design bounce, assert fail that is trusted) is the interrupt. The bot stops and escalates. It does not open a prompt inside the phase agent.
- Core skills keep a headless path so cloud sessions cannot dead-end. That is a standing plugin rule, and it is also the condition for SessionStart-installed skills to be usable unattended.

---

## 6. Observability

LangGraph documentation recommends tracing (e.g. LangSmith) for multi-step graphs ([workflows doc](https://docs.langchain.com/oss/python/langgraph/workflows-agents)).

**Stack the bot reads (CLIs on master; live provider keys still absent):**

- Core skill dirs on disk → `tools/driver/check_skills.py`
- `Workflow-Phase:` trailers + `DESIGN.md` → status JSON
- `workflow-report` fence → last status and reason
- Provider turns/cost printed per phase
- Jev assert JSONL (separate from classify)
- `evals/results/` when an outcome row exists

**Also in tree, not on the control path:** `tools/transcript/` extract, stats, cost, `iterate_analysis.py`, and `classify.py` (session-kind visualisation).

**Gap:** live headless dispatch and the first outcome row are still open. A unified trace UI is out of scope.

---

## 7. Concrete mapping table (skills)

| External pattern | workflow-plugin anchor |
|------------------|------------------------|
| Planner–executor | `design`+`refine` vs `execute` workers |
| Orchestrator–worker | `execute` + briefs, one phase |
| Supervisor routing | **Grok Bot** via status + `trigger_phase` |
| Checkpoints | `Workflow-Phase:` trailers |
| Multi-agent debate | `iterate` (lab; not required unattended) |
| Evaluator–optimizer | Phase verify, Jev assert, `comprehensive-review` |
| Worker ACI | Skills, briefs, trailers |
| Bot ACI | `tools/driver/` CLI/MCP |
| Cloud bootstrap | Cursor image bake of `install.sh` (core only); Claude remote `SessionStart` |
| Escalation | `unsuccessful` report, headless ledger |
| Benchmark harness | Verifier + cost (`evals/`, fixture still empty) |
| Typed steer | Jev assert on compact phase state |
| Typed viz | `classify.py` session kind |

---

## 8. Open questions (for PROPOSALS / BACKLOG)

1. Can status JSON from trailers alone drive the bot, with no read of `IMPLEMENTATION.md`? (P0 spike; kill line if no.)
2. Which single Jev assert is safe to steer on, checked against a deterministic fixture? (P1; kill if it false-steers.)
3. Which harness Grok Bot starts — Claude `SessionStart`, Cursor cloud `install.sh`, or a prebaked image? **Cursor cloud, observed 2026-09-30:** the bot enters a prebaked image; bake core-only `install.sh` (see FINDINGS bootstrap). Claude Code on the web stays the SessionStart path; that container was not observed in the spike.
4. When does a repair loop belong inside `execute` verify versus bouncing to `refine`? (Unchanged workflow question.)

Parked, not open: whether `workflow_alignment` matches a human label, and whether session kind should merge with `iterate_analysis.py`. The eight-row classify measurements live in [`../ANALYSIS/2026-09-30-strategy-pass.md`](../ANALYSIS/2026-09-30-strategy-pass.md); they inform charts, not driver gates.

---

## References (primary)

- Yao et al., ReAct: https://arxiv.org/abs/2210.03629  
- Yang et al., SWE-agent: https://arxiv.org/abs/2405.15793  
- Wu et al., AutoGen: https://arxiv.org/abs/2308.08155  
- LangGraph workflows: https://docs.langchain.com/oss/python/langgraph/workflows-agents  
- LangGraph multi-agent: https://www.langchain.com/blog/langgraph-multi-agent-workflows  
- OpenHands SDK: https://docs.openhands.dev/sdk  
- OpenHands SDK paper: https://arxiv.org/html/2511.03690v2  
- SWE-bench: https://www.swebench.com/SWE-bench/  
- TypeSafe: https://docs.typesafe.ai/  
