# Workflow lab — research & ops workspace

This tree is the **durable notebook** for optimising the [workflow-plugin](https://github.com/codyhamilton/workflow-plugin): research, proposals, analysis pointers, goals, and dated findings. Maintainer skills (`iterate`, `transcript-parser`, `workflow-tuning`, and related) live as Claude Code project skills under `.claude/skills/` at the repo root — prompt-driven tooling for maintainers. **This folder is what the Workflow Optimiser agent maintains in git**.

## Who maintains what

| Area | Owner | Location |
|------|--------|----------|
| Core workflow skills (design → close-out) | plugin releases | `skills/` |
| Maintainer project skills | repo checkout | `.claude/skills/` (incl. `white-paper` for evidence-backed research) |
| Research, goals, findings, proposals | **Workflow Optimiser** (agent + Cody) | `docs/lab/` |
| Long-form architecture & plans | humans + design skill | `docs/ARCHITECTURE.md`, `docs/plans/` |
| Eval harness layout | workflow-tuning | `evals/` |
| Transcript tooling (cost, extract, classify viz) | engineering spikes | `tools/transcript/` |
| Bot driver (status, one-phase trigger, asserts, skill check) | engineering spikes | `tools/driver/` |

## Closed research

Stage A is closed: [WHITE-PAPER-CLOSE.md](WHITE-PAPER-CLOSE.md) (established / hypotheses / open) and [GUIDANCE-measurement.md](GUIDANCE-measurement.md). Next stage is data collection through the quality service.

## Cadence

- **Weekly (light):** skim `FINDINGS.md`, update `GOALS.md` if remit shifted, triage `BACKLOG.md`, move or close items in `PROPOSALS/`.
- **After a notable run:** append a dated bullet to `FINDINGS.md` (bot/driver log, assert result, eval verifier, merged PR harvest). Session classify may be attached as a chart; it is not the result.
- **When exploring a theme:** add or extend a note under `RESEARCH/` and link it from `RESEARCH/INDEX.md`.
- **When a hypothesis deserves a white paper:** use the [`white-paper` skill](../../.claude/skills/white-paper/SKILL.md): theory → wide research → refined thesis → test → analysis → accepted facts, looping through failed and null tests. Research packs live under `RESEARCH/<date>-<slug>/`; consolidated papers under `PROPOSALS/`.

## How to use this space

1. For Jev work, start from the [lab results](JEV-RESULTS.md), then the [hypotheses](JEV-HYPOTHESES.md) and [active methodology](JEV-METHODOLOGY.md). For wider work, read [`GOALS.md`](GOALS.md).
2. Read [`FINDINGS.md`](FINDINGS.md) for the latest grounded state of the plugin and tooling.
3. Open [`PROPOSALS/`](PROPOSALS/) for draft work items (status in each file’s frontmatter).
4. Read the current strategy pass via [`ANALYSIS/README.md`](ANALYSIS/README.md), then the case studies under `docs/analysis/`.
5. Browse [`RESEARCH/INDEX.md`](RESEARCH/INDEX.md) for external references mapped to the bot, hooks, trailers, and asserts.
