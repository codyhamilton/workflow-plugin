# Research index — agent & workflow systems

Curated bibliography for optimising workflow-plugin. Each entry: **takeaway** → **implication for this repo** → **confidence** (how sure we are the mapping applies).

Deep dive for synthesis: [`2026-09-30-workflow-systems.md`](2026-09-30-workflow-systems.md).

**Dated research packs** (inputs to `PROPOSALS/` white papers; see `lab-proposal` skill):

| Pack | Question | Proposal (if any) |
|------|----------|-------------------|
| [`2026-10-01-progressive-jev-session-gates/`](2026-10-01-progressive-jev-session-gates/INDEX.md) | Progressive in-session Jev checkout every 15 turns after a first checkpoint near 75, tuned offline against multi-model gold exits. Extends cheap-Jev use case 1. **Confidence: not high** (no replay numbers yet). | [`../PROPOSALS/2026-10-01-progressive-jev-session-gates.md`](../PROPOSALS/2026-10-01-progressive-jev-session-gates.md) (`status: researching`) |
| [`2026-09-30-jev-cheap-judgement-signals/`](2026-09-30-jev-cheap-judgement-signals/INDEX.md) | Cheap conditional Jev judgements (hooks + refine/unit/phase soft signals) | [`../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) (`status: resolved` — recommendations accepted pending product wiring; proofs `112ccfe`) |
| [`2026-09-30-durable-analytics-sink/`](2026-09-30-durable-analytics-sink/INDEX.md) | Durable observability sink for local + cloud agents (dual-write JSONL + HTTP) | [`../PROPOSALS/2026-09-30-durable-analytics-sink.md`](../PROPOSALS/2026-09-30-durable-analytics-sink.md) (`status: resolved` — recommendations accepted pending product wiring; proofs `1bff769`) |
| [`2026-09-30-opencode-hooks-plugin/`](2026-09-30-opencode-hooks-plugin/INDEX.md) | OpenCode-native plugin for PostToolBatch-like soft signals (separate npm package; no Claude/Cursor drop-in) | [`../PROPOSALS/2026-09-30-opencode-hooks-plugin.md`](../PROPOSALS/2026-09-30-opencode-hooks-plugin.md) (`status: resolved` — recommendations accepted pending product wiring; proofs `d4c4da1`, LCD 4/4) |

**Current control and measurement policy** (2026-09-30, later pass): [`../ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../ANALYSIS/2026-09-30-grokbot-driver-reorient.md). Implications in this index follow that pass: Grok Bot drives, Jev asserts steer, classify visualises.

---

## Foundations: reason + act

| Source | Takeaway | Implication (skills / evals / tooling) | Conf. |
|--------|----------|------------------------------------------|-------|
| [ReAct (Yao et al., ICLR 2023)](https://arxiv.org/abs/2210.03629) | Interleave reasoning traces and environment actions so plans update from observations. | **Grok Bot** reasons on status JSON and the phase report, then acts by triggering one phase. Workers inside `execute` act on briefs. The bot does not fuse every phase into its own context. | high |
| [Google Research blog — ReAct](https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/) | Same paradigm; emphasises diagnosable trajectories. | The bot's diagnosable trail is **trailers + workflow-report + per-phase cost + assert log**. Briefs stay verbatim (README hypothesis #2). | high |

## Interfaces & coding agents

| Source | Takeaway | Implication | Conf. |
|--------|----------|-------------|-------|
| [SWE-agent (Yang et al., NeurIPS 2024)](https://arxiv.org/abs/2405.15793) | Custom **agent–computer interface (ACI)** materially changes success on repo tasks. | Two ACIs: skills/briefs/trailers for workers, and a **bot-callable CLI/MCP** (`status`, `trigger_phase`) for Grok Bot. Transcript tools show worker behaviour; they are not the bot's control surface. | high |
| [SWE-agent GitHub](https://github.com/SWE-agent/SWE-agent) | Inference vs evaluation split; Docker sandbox. | The driver runs inference one phase at a time. **Evals** grade with a verifier and cost, separate from the bot's prompt. | medium |
| [OpenHands SDK docs](https://docs.openhands.dev/sdk) | Modular agents: LLM + tools + workspace + conversation lifecycle. | Core skills are the cloud-safe workspace the bot installs. Lab skills stay off the unattended path. | medium |
| [OpenHands SDK paper (arXiv:2511.03690)](https://arxiv.org/html/2511.03690v2) | Event-sourced state, typed tools, security/confirmation before risky actions. | Events we keep: driver stdout, assert JSONL, git trailers. Headless assumption ledger is the bot's confirmation path; `unsuccessful` escalates. | medium |

## Multi-agent orchestration

| Source | Takeaway | Implication | Conf. |
|--------|----------|-------------|-------|
| [AutoGen (Wu et al., arXiv:2308.08155)](https://arxiv.org/abs/2308.08155) | **Conversation programming**: composable agent chats with humans/tools in the loop. | The bot's program is tool calls, not a human relay of briefs. `refine` → workers stays a static pattern inside one phase. | high |
| [AutoGen v0.4 (Microsoft Research)](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) | Actor/event model for scale. | Driver events (report, cost, assert) beat coordinator prose as the log the next session reads. | medium |
| [LangGraph multi-agent (LangChain blog, Jan 2024)](https://www.langchain.com/blog/langgraph-multi-agent-workflows) | Agents as graph nodes; supervisor and hierarchical teams. | **Grok Bot is the supervisor.** It does no phase work. Workers are brief-routed inside `execute`. Trailers are the checkpoints. | high |
| [LangGraph workflows & agents (LangChain docs)](https://docs.langchain.com/oss/python/langgraph/workflows-agents) | Named patterns: routing, parallelization, orchestrator–worker, **evaluator–optimizer**. | Evaluator–optimizer is phase verify + **Jev assert** + `comprehensive-review`. The bot applies the optimizer step by re-dispatching or escalating. | high |

## Evaluation & benchmarks

| Source | Takeaway | Implication | Conf. |
|--------|----------|-------------|-------|
| [SWE-bench overview](https://www.swebench.com/SWE-bench/) | Real issues + Dockerized test verification. | Outcome rows use a **verifier** (command, rubric, or trailer completeness) plus cost. The bot can re-run them. Session-kind charts are optional attachments. | high |
| [SWE-bench evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/) | JSONL predictions; harness caches by `run_id`. | When eval automation lands, key results by `run_id` under `evals/results/<scenario>/<timestamp>/`. | high |
| [TypeSafe / Jev docs](https://docs.typesafe.ai/) | Typed questions (Choice, Score, Noul) over compact `state`. | **Assert hooks** on phase state (alignment, log, steer). Pin `jev-1.13.0`. `classify.py` remains a session-kind visualisation, not the measurement path. | high |
| [Jev context budgets (how-to-use)](https://www.jevtypesafeai.com/how-to-use) | Hard token limits on state+questions. | Assert `state` is headings, trailer, and the outcome line — far under the budget. Store `snapshot_hash` in the assert log. | high |

## Observability (industry)

| Source | Takeaway | Implication | Conf. |
|--------|----------|-------------|-------|
| [LangGraph workflows doc — LangSmith tracing note](https://docs.langchain.com/oss/python/langgraph/workflows-agents) | Trace per-step data flow in complex graphs. | The bot's trace is **status JSON, workflow-report, per-phase cost, assert JSONL**, plus git. Classify JSONL is a side chart. No LangSmith dependency. | medium |

## Maintenance notes

- **AutoGen** is in maintenance mode; Microsoft points new production work to **Agent Framework** ([autogen README](https://github.com/microsoft/autogen)) — watch for patterns, not necessarily new dependencies.
- **SWE-agent** repo notes evolution toward mini-swe-agent; ACI lesson remains primary for us.

## How to add a row

1. Primary source URL (paper, official docs, or authoritative blog).
2. One-line takeaway grounded in that source.
3. Concrete mapping to the bot, a hook, a trailer, an assert, or an outcome verifier.
4. Confidence if the mapping is inferential.
