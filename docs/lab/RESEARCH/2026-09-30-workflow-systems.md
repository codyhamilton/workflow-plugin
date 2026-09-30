# Deep dive: How agentic / LLM workflow systems are designed

**Date:** 2026-09-30 (Australia/Brisbane)  
**Author:** Workflow Optimiser (seed)  
**Scope:** Patterns that inform workflow-plugin — not a framework comparison for greenfield apps.

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

- **`design` / `refine`** contexts should emphasise reasoning over artifacts (plans, contracts) with minimal tool thrash.
- **`execute`** contexts should emphasise tool use bounded by briefs — orchestrator reasons on `IMPLEMENTATION.md`, workers act on code.
- **Evals** should capture trajectories (transcript tools), not only `DESIGN.md` / `IMPLEMENTATION.md` finals — otherwise we cannot see ReAct-style failure modes.

### Orchestrator–worker (LangGraph pattern)

[LangChain: Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) describes **orchestrator–worker**: a planner spawns variable subtasks (often via parallel `Send`), then aggregates results.

**Implication (high confidence):**

- **`refine`** is the orchestrator for a **single phase**; **`execute`** dispatches workers per brief — classic orchestrator–worker with a fixed phase boundary.
- **`iterate`** is orchestrator–worker with **unknown worker count** (divergent candidates) — closer to LangGraph’s dynamic fan-out than core `execute`.
- **Risk:** supervisor misrouting and worker echo loops — mitigated here by **disjoint brief ownership** and **phase trailers** (`Workflow-Phase:`).

### SWE-agent: the interface is the product

[SWE-agent (arXiv:2405.15793)](https://arxiv.org/abs/2405.15793) argues LM agents need tailored **agent–computer interfaces** (ACI), not raw shell alone.

**Implication (high confidence):**

- Skill markdown + brief templates + git trailers are our ACI. Optimising the plugin is often **interface design** (what workers see, what is verbatim, what is forbidden).
- **`transcript-parser`** and **`classify.py`** are how we measure ACI changes — tool histograms and session kind labels should move when skills change.

---

## 3. Graphs, conversations, and state

### LangGraph: explicit graphs with cycles

[LangGraph multi-agent workflows (LangChain blog)](https://www.langchain.com/blog/langgraph-multi-agent-workflows) models agents as **nodes**, control as **edges**, supports cycles (retry, repair) and hierarchical teams (subgraphs).

**Implication (medium confidence):**

- Core workflow is a **linear graph** with optional bounce (`refine` → `design`). `iterate` adds **cycles** (diverge → judge → reconcile).
- If we implement `tools/driver/`, represent phases as **checkpoints** (resume after human or CI) similar to LangGraph interrupt/checkpoint patterns described in practitioner guides — see [Phoenix LangGraph cookbook](https://arizeai-433a7140.mintlify.app/docs/phoenix/cookbook/agent-workflow-patterns/langgraph) (evaluator–optimizer, supervisor).

### AutoGen: conversation as program

[AutoGen (arXiv:2308.08155)](https://arxiv.org/abs/2308.08155) composes **conversable agents** with programmable patterns (two-agent, group, nested).

**Implication (high confidence):**

- **Briefs routed verbatim** ≈ AutoGen messages with fixed recipients — aligns with README hypothesis #2 (briefs beat messengers).
- **Human input** modes map to interactive `design` checkpoints and assumption ledgers.
- v0.4’s event/actor model ([Microsoft Research article](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/)) suggests that if we outgrow skill prompts, an explicit event log may scale better than transcript-only forensics.

### OpenHands SDK: production agent stack

[OpenHands SDK documentation](https://docs.openhands.dev/sdk) and [SDK architecture paper (arXiv:2511.03690)](https://arxiv.org/html/2511.03690v2) emphasise **typed tools**, **workspaces** (local vs remote sandbox), **event-sourced conversations**, and **security confirmation** before risky actions.

**Implication (medium confidence):**

- **`workflow` core** ≈ remote/sandboxed pipeline workspace; **`workflow-lab`** ≈ local workspace with richer tools.
- **`post-build`** QA + exact-SHA deploy proof ≈ OpenHands-style confirmation before irreversible ops.
- **Condenser / context management** lessons support README hypothesis #8 (cost ∝ context × turns) — fresh orchestrator per phase is our condenser.

---

## 4. Evaluator–optimizer and harnesses

### Evaluator–optimizer loop

LangGraph docs name **evaluator–optimizer**: generate → evaluate → revise until acceptable.

**Mapping (high confidence):**

| Plugin stage | Evaluator role |
|--------------|----------------|
| Per-phase verify in `execute` | Cheap-tier outcome check |
| `comprehensive-review` | Premium evaluator on whole design |
| Remediation briefs + re-run | Optimizer pass |
| `evals/` harness | Offline evaluator–optimizer on full workflow |
| Jev `classify.py` | Cheap **typed** evaluator on session behaviour (not code correctness) |

### SWE-bench style verification

[SWE-bench](https://www.swebench.com/SWE-bench/) applies patches in Docker and runs tests ([evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/)).

**Implication (high confidence):**

- Our eval scenarios should declare **verifiers** (CI command, file rubric, or human sign-off) in `source.md`.
- Separate **inference** (workflow run) from **grading** (harness) — same separation as SWE-agent inference vs SWE-bench eval.

### Typed eval with Jev (TypeSafe)

[TypeSafe docs](https://docs.typesafe.ai/) — Choice / Score / Noul over JSON `state`; [budget limits](https://www.jevtypesafeai.com/how-to-use).

**Implication (high confidence):**

- Use Jev where we need **calibrated probabilities** and **closed labels** — session kind, brief completeness, workflow alignment — not for compiling code.
- Batch questions per request (Choice + Score) to minimise round trips — already in `classify.py` design.
- **Review gate:** auto-accept Choice when `confidence ≥ 0.8`; else require `human_label` in JSONL (see FINDINGS 2026-09-30).

---

## 5. Human-in-the-loop (HITL)

Sources: AutoGen human-input modes; OpenHands security/confirmation; LangGraph interrupt/checkpoint patterns (practitioner cookbooks).

**Implication (medium confidence):**

- **`design` interactive** and assumption ledger are HITL at plan time — prevents expensive autonomous thrash.
- **Classify low-confidence rows** are HITL at measurement time — prevents bad metrics from poisoning eval conclusions.
- **Do not** add HITL inside `execute` hot paths for cloud pipeline without a headless fallback (core plugin rule).

---

## 6. Observability

LangGraph documentation recommends tracing (e.g. LangSmith) for multi-step graphs ([workflows doc](https://docs.langchain.com/oss/python/langgraph/workflows-agents)).

**Our stack today (high confidence):**

- `tools/transcript/extract.py` → normalized JSON
- `stats.py` / `cost.py` / `iterate_analysis.py` — deterministic analytics
- `classify.py` + `.classify-log.jsonl` — typed semantic layer
- `evals/results/` — outcome comparisons

**Gap:** no unified trace UI — BACKLOG addresses harvest and join keys.

---

## 7. Concrete mapping table (skills)

| External pattern | workflow-plugin anchor |
|------------------|------------------------|
| Planner–executor | `design`+`refine` vs `execute` workers |
| Orchestrator–worker | `execute` + briefs |
| Supervisor routing | Human/coordinator dispatching skills |
| Multi-agent debate | `iterate` divergence + judge |
| Evaluator–optimizer | `comprehensive-review` + evals |
| ACI design | Skills, briefs, trailers |
| HITL | Interactive design, classify review gate |
| Benchmark harness | `evals/` (fixture TBD) |
| Typed cheap eval | Jev via `classify.py` |

---

## 8. Open questions (for PROPOSALS / BACKLOG)

1. Does Jev **workflow_alignment** Score correlate with human judgment of phase discipline? (Needs labeled data.) **2026-09-30 strategy pass:** not answerable from the eight-row log. Score confidence never reached 0.8; there is no human alignment field. Do not use Score as a KPI yet.
2. Should session **kind** taxonomy merge with `iterate_analysis.py` phases or stay orthogonal? (Spike doc recommends orthogonal until labels settle.) **2026-09-30 strategy pass:** stay orthogonal. Disagreement is expected. `mixed` did not fire even on a three-way tie — ambiguity is not a label the model uses.
3. When does a LangGraph-style **repair loop** belong inside `execute` verify vs bouncing to `refine`? **2026-09-30 strategy pass:** parked. Behaviour change; out of the measure-first window.

The critique of this note and the reordered backlog live in [`../ANALYSIS/2026-09-30-strategy-pass.md`](../ANALYSIS/2026-09-30-strategy-pass.md).

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
