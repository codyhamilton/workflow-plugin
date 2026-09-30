# Workflow lab — research & ops workspace

This tree is the **durable notebook** for optimising the [workflow-plugin](https://github.com/codyhamilton/workflow-plugin): research, proposals, analysis pointers, goals, and dated findings. It complements the interactive lab plugin under `plugins/workflow-lab/` (skills such as `iterate`, `transcript-parser`, `workflow-tuning`) — those skills stay prompt-driven; **this folder is what the Workflow Optimiser agent maintains in git**.

## Who maintains what

| Area | Owner | Location |
|------|--------|----------|
| Core workflow skills (design → close-out) | plugin releases | `skills/` |
| Interactive / local lab skills | plugin releases | `plugins/workflow-lab/skills/` (incl. `lab-proposal` for white-paper research packs) |
| Research, goals, findings, proposals | **Workflow Optimiser** (agent + Cody) | `docs/lab/` |
| Long-form architecture & plans | humans + design skill | `docs/ARCHITECTURE.md`, `docs/plans/` |
| Eval harness layout | workflow-tuning | `evals/` |
| Transcript tooling (cost, extract, classify viz) | engineering spikes | `tools/transcript/` |
| Bot driver (status, one-phase trigger, asserts, skill check) | engineering spikes | `tools/driver/` |

## Cadence

- **Weekly (light):** skim `FINDINGS.md`, update `GOALS.md` if remit shifted, triage `BACKLOG.md`, move or close items in `PROPOSALS/`.
- **After a notable run:** append a dated bullet to `FINDINGS.md` (bot/driver log, assert result, eval verifier, merged PR harvest). Session classify may be attached as a chart; it is not the result.
- **When exploring a theme:** add or extend a note under `RESEARCH/` and link it from `RESEARCH/INDEX.md`.
- **When a signal may deserve a white paper:** run the **`lab-proposal`** skill (`plugins/workflow-lab/skills/lab-proposal/`) — **signal → triage (Grok) → research pack (Composer) → proposal (Grok 4.7)**. Research packs live under `RESEARCH/<date>-<slug>/`; finished proposals under `PROPOSALS/`. Weekly review skims open proposals; behaviour changes wait for Cody.

## How to use this space

1. Start from [`GOALS.md`](GOALS.md) for current success metrics and focus order.
2. Read [`FINDINGS.md`](FINDINGS.md) for the latest grounded state of the plugin and tooling.
3. Open [`PROPOSALS/`](PROPOSALS/) for draft work items (status in each file’s frontmatter).
4. Read the current strategy pass via [`ANALYSIS/README.md`](ANALYSIS/README.md), then the case studies under `docs/analysis/`.
5. Browse [`RESEARCH/INDEX.md`](RESEARCH/INDEX.md) for external references mapped to the bot, hooks, trailers, and asserts.

## Agent defaults (Optimiser remit)

- **Control target:** Grok Bot (or an equivalent unattended driver) runs phases. Humans escalate on `unsuccessful`. Current strategy: [`ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](ANALYSIS/2026-09-30-grokbot-driver-reorient.md).
- **Collection vs strategy:** Composer (or an equivalent cheap collector) gathers trailers, costs, transcripts, and assert rows. **Grok** writes strategy passes. Avoid the fast tier; avoid high-context models unless a pass truly needs them.
- **Jev:** TypeSafe (`jev-1.13.0` pinned) for **assert hooks** — alignment, logging, steering on compact phase state. `tools/transcript/classify.py` is visualisation of session kind, not a KPI.
- **Landing policy:** additive, non-breaking changes merge to `master`.

## Related entry points

- Repo overview: [`docs/OVERVIEW.md`](../OVERVIEW.md)
- OpenCode (skills symlink install, harness limits): [`README.md` § OpenCode](../../README.md#opencode-partial-compatibility) and `./install.sh --opencode-skills`
- OpenCode + DeepSeek Flash (encouraged for units; sign-off review gate, guidance only): [`GUIDANCE-flash-review-gate.md`](GUIDANCE-flash-review-gate.md)
- Operating hypotheses: root [`README.md`](../../README.md) § Operating hypotheses
- Eval format: [`evals/README.md`](../../evals/README.md)
- Transcript toolkit: [`tools/transcript/README.md`](../../tools/transcript/README.md)
- Phase driver design: [`docs/plans/06-phase-driver/DESIGN.md`](../plans/06-phase-driver/DESIGN.md)
