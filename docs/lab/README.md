# Workflow lab — research & ops workspace

This tree is the **durable notebook** for optimising the [workflow-plugin](https://github.com/codyhamilton/workflow-plugin): research, proposals, analysis pointers, goals, and dated findings. It complements the interactive lab plugin under `plugins/workflow-lab/` (skills such as `iterate`, `transcript-parser`, `workflow-tuning`) — those skills stay prompt-driven; **this folder is what the Workflow Optimiser agent maintains in git**.

## Who maintains what

| Area | Owner | Location |
|------|--------|----------|
| Core workflow skills (design → close-out) | plugin releases | `skills/` |
| Interactive / local lab skills | plugin releases | `plugins/workflow-lab/skills/` |
| Research, goals, findings, proposals | **Workflow Optimiser** (agent + Cody) | `docs/lab/` |
| Long-form architecture & plans | humans + design skill | `docs/ARCHITECTURE.md`, `docs/plans/` |
| Eval harness layout | workflow-tuning | `evals/` |
| Transcript / classify tooling | engineering spikes | `tools/transcript/` |

## Cadence

- **Weekly (light):** skim `FINDINGS.md`, update `GOALS.md` if remit shifted, triage `BACKLOG.md`, move or close items in `PROPOSALS/`.
- **After a notable run:** append a dated bullet to `FINDINGS.md` (session classify, eval result, merged PR harvest).
- **When exploring a theme:** add or extend a note under `RESEARCH/` and link it from `RESEARCH/INDEX.md`.

## How to use this space

1. Start from [`GOALS.md`](GOALS.md) for current success metrics and focus order.
2. Read [`FINDINGS.md`](FINDINGS.md) for the latest grounded state of the plugin and tooling.
3. Read the latest strategy pass under [`ANALYSIS/`](ANALYSIS/) before promoting a proposal.
4. Open [`PROPOSALS/`](PROPOSALS/) for draft work items (status in each file’s frontmatter).
5. Follow [`ANALYSIS/README.md`](ANALYSIS/README.md) into deeper case studies under `docs/analysis/`.
6. Browse [`RESEARCH/INDEX.md`](RESEARCH/INDEX.md) for external references mapped to this plugin’s skills and eval strategy.

## Agent defaults (Optimiser remit)

- **Cloud agents:** Composer default; **Grok 4.7 medium** for heavy synthesis — avoid “fast” and avoid high-context models unless explicitly requested.
- **Typed eval:** TypeSafe Jev (`jev-1.13.0` pinned) for cheap structured labels over transcript snapshots (`tools/transcript/classify.py`).
- **Landing policy:** additive, non-breaking changes merge to `master`.

## Related entry points

- Repo overview: [`docs/OVERVIEW.md`](../OVERVIEW.md)
- Operating hypotheses: root [`README.md`](../../README.md) § Operating hypotheses
- Eval format: [`evals/README.md`](../../evals/README.md)
- Transcript toolkit: [`tools/transcript/README.md`](../../tools/transcript/README.md)
