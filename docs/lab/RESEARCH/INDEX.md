# Research index — agent & workflow systems

Curated bibliography for optimising workflow-plugin. Each entry: **takeaway** → **implication for this repo** → **confidence** (how sure we are the mapping applies).

Deep dive for synthesis: [`2026-09-30-workflow-systems.md`](2026-09-30-workflow-systems.md).

---

## Foundations: reason + act

| Source | Takeaway | Implication (skills / evals / tooling) | Conf. |
|--------|----------|------------------------------------------|-------|
| [ReAct (Yao et al., ICLR 2023)](https://arxiv.org/abs/2210.03629) | Interleave reasoning traces and environment actions so plans update from observations. | `execute` workers should **act** (tools) while orchestrators **reason** on artifacts; avoid fusing plan+build in one context (matches cold-read design). Evals should log tool traces, not only final files. | high |
| [Google Research blog — ReAct](https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/) | Same paradigm; emphasises diagnosable trajectories. | `workflow-tuning` harvest should keep **verbatim briefs + trailers** for post-hoc diagnosis (aligns with README hypothesis #2). | high |

## Interfaces & coding agents

| Source | Takeaway | Implication | Conf. |
|--------|----------|-------------|-------|
| [SWE-agent (Yang et al., NeurIPS 2024)](https://arxiv.org/abs/2405.15793) | Custom **agent–computer interface (ACI)** materially changes success on repo tasks. | Skills are our ACI: tool names, brief shape, and `Workflow-Phase:` trailers matter as much as model choice. Invest in **transcript tools** (`tools/transcript/`) to see ACI effects. | high |
| [SWE-agent GitHub](https://github.com/SWE-agent/SWE-agent) | Inference vs evaluation split; Docker sandbox. | Mirror: **execute** produces artifacts; **evals/** + SWE-bench-style harnesses verify outcomes separately from prompting. | medium |
| [OpenHands SDK docs](https://docs.openhands.dev/sdk) | Modular agents: LLM + tools + workspace + conversation lifecycle. | Maps to core/lab split: `workflow` = pipeline-safe workspace; `workflow-lab` = local/interactive workspace extensions. | medium |
| [OpenHands SDK paper (arXiv:2511.03690)](https://arxiv.org/html/2511.03690v2) | Event-sourced state, typed tools, security/confirmation before risky actions. | `design` assumption ledger + interactive checkpoints ≈ HITL; `post-build` deploy proof ≈ confirmation gate. Log events in eval runs for replay. | medium |

## Multi-agent orchestration

| Source | Takeaway | Implication | Conf. |
|--------|----------|-------------|-------|
| [AutoGen (Wu et al., arXiv:2308.08155)](https://arxiv.org/abs/2308.08155) | **Conversation programming**: composable agent chats with humans/tools in the loop. | `refine` → `execute` routing is a **static** conversation pattern; `iterate` is dynamic multi-agent. Document which pattern a task uses in FINDINGS. | high |
| [AutoGen v0.4 (Microsoft Research)](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) | Actor/event model for scale. | If `tools/driver/` ships, prefer explicit message/event log over ad-hoc coordinator prose. | medium |
| [LangGraph multi-agent (LangChain blog, Jan 2024)](https://www.langchain.com/blog/langgraph-multi-agent-workflows) | Agents as graph nodes; supervisor and hierarchical teams. | `execute` coordinator (human or agent) ≈ supervisor; brief-routed workers ≈ team nodes. Phase boundaries ≈ graph checkpoints. | medium |
| [LangGraph workflows & agents (LangChain docs)](https://docs.langchain.com/oss/python/langgraph/workflows-agents) | Named patterns: routing, parallelization, orchestrator–worker, **evaluator–optimizer**. | **Evaluator–optimizer** maps to `comprehensive-review` + remediation briefs + re-verify; eval harness is offline evaluator–optimizer. | high |

## Evaluation & benchmarks

| Source | Takeaway | Implication | Conf. |
|--------|----------|-------------|-------|
| [SWE-bench overview](https://www.swebench.com/SWE-bench/) | Real issues + Dockerized test verification. | `evals/` scenarios should pin repo+commit and define **verifiable** outcomes (tests or artifact rubric), not vibes-only. | high |
| [SWE-bench evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/) | JSONL predictions; harness caches by `run_id`. | When we add eval automation, use immutable `run_id` per candidate and store `results/<scenario>/<timestamp>/`. | high |
| [TypeSafe / Jev docs](https://docs.typesafe.ai/) | Typed questions (Choice, Score, Noul) over compact `state`. | `classify.py` for session **kind** + cheap alignment score; future hooks for brief-quality Scores. Pin `jev-1.13.0` in logs. | high |
| [Jev context budgets (how-to-use)](https://www.jevtypesafeai.com/how-to-use) | Hard token limits on state+questions. | Keep snapshots ~1–3k tokens; store `snapshot_hash` not prose in any indexer. | high |

## Observability (industry)

| Source | Takeaway | Implication | Conf. |
|--------|----------|-------------|-------|
| [LangGraph workflows doc — LangSmith tracing note](https://docs.langchain.com/oss/python/langgraph/workflows-agents) | Trace per-step data flow in complex graphs. | Until LangSmith integration exists, **`tools/transcript/` + JSONL classify log** are the tracing layer for this plugin. | medium |

## Maintenance notes

- **AutoGen** is in maintenance mode; Microsoft points new production work to **Agent Framework** ([autogen README](https://github.com/microsoft/autogen)) — watch for patterns, not necessarily new dependencies.
- **SWE-agent** repo notes evolution toward mini-swe-agent; ACI lesson remains primary for us.

## How to add a row

1. Primary source URL (paper, official docs, or authoritative blog).
2. One-line takeaway grounded in that source.
3. Concrete mapping to a skill, eval artifact, or `tools/transcript/` hook.
4. Confidence if the mapping is inferential.
