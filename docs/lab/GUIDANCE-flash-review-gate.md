# Guidance — DeepSeek Flash / OpenCode review gate

**Status:** guidance (non-breaking). No installer, driver, or hook behaviour changes — operators and orchestrators follow this pattern by convention.

**Related:** Codex harness (separate from OpenCode; Sol/Luna) — [`GUIDANCE-codex-harness.md`](GUIDANCE-codex-harness.md). OpenCode skills install and harness limits — [`README.md` § OpenCode](../../README.md#opencode-partial-compatibility). OpenCode hooks proposal (`status: resolved`, plugin unwired) — [`PROPOSALS/2026-09-30-opencode-hooks-plugin.md`](PROPOSALS/2026-09-30-opencode-hooks-plugin.md). Lab pack — [`RESEARCH/2026-09-30-opencode-hooks-plugin/`](RESEARCH/2026-09-30-opencode-hooks-plugin/INDEX.md). Cheap analysis harness (Flash drafts, local volume labels, TypeSafe fan-out — design only) — [`RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/`](RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/INDEX.md).

## Encouraged use

**DeepSeek Flash is encouraged** on the build path when you need to **ration orchestrator capacity** — during Claude availability gaps, parallel unit throughput, or cost/token pressure. Map Flash freely to **execute briefs** and **implement phase units**; this document does **not** limit *whether* to use Flash. It only bounds **who may sign off** the phase after Flash contributed unit work.

## When the gate applies

The gate applies whenever Flash (or an equivalent cheap OpenCode map) **executed briefs or phase units** under `execute`. The same sign-off rules apply if Flash is used outside OpenCode in the same economic tier for unit work.

It does **not** relax design, refine, or plan-end `comprehensive-review` rules; it adds a **phase review hold** after Flash touched unit execution.

## Core rule (sign-off only)

**Flash in the build path ⇒ mandatory phase review before close. No auto close-out.**

Flash workers must **not** sign off or close the phase: no terminal phase verification, no `Workflow-Phase:` trailer, and no treating the phase as done. That responsibility stays with the orchestrator tier. Using Flash for brief/unit work **auto-triggers the need for phase review** — **hold** until **Grok** or **Claude Code** reviews the phase outcome and signs off.

## Required pattern

```
Flash draft (briefs / units)  →  Sonnet 5.5 review of Flash work  →  Claude Code or Grok phase validation and sign-off
```

1. **Flash drafts and implements** on assigned briefs and units — encouraged when capacity needs rationing.
2. **Every Flash build-path pass triggers a Sonnet 5.5 review agent afterward — not optional.** Route Flash output (diffs, brief completion, unit reports) to an independent **Sonnet 5.5** pass keyed to the design phase outcome and brief done-evidence. Mandatory relay, not “if time permits.”
3. **Phase validation and sign-off are Claude Code or Grok only** (Build Orchestrator). They review the phase (including Sonnet’s review of Flash work), verify the phase outcome, and only then may land `Workflow-Phase:` and close the phase. Flash does not sign off; a Flash run must not imply the phase is closed.

Flash does not replace `comprehensive-review` at plan end.

## Volume analysis is not this gate's build path

Transcript summaries, early-window labels, and TypeSafe framing trials are specified in [`RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/DESIGN.md`](RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/DESIGN.md). Flash may draft those artifacts. Sonnet 5.5 reviews the drafts, and Claude Code or Grok signs the review as a **study convention** for those artifacts. That convention does not add a phase-close rule and does not change the checklist below. Drafts do not become gold seats. A local llama.cpp server (default `http://127.0.0.1:8080/v1`, override `WORKFLOW_LOCAL_LLM_URL`) is for high-volume window labels only. It is not the OpenCode default for other agents, and this guidance does not write provider config.

## What does not change

- **`assert_phase --deterministic`** remains the hard kill line for phase boundaries on any harness where it is wired.
- **Jev / PostToolBatch-style soft signals** stay **advisory** where installed (Claude Code, Cursor driver, OpenCode lab proofs). This guidance does not add enforcement hooks.
- **Skill names and install paths** are unchanged (`execute`, `comprehensive-review`, OpenCode symlinks under `~/.config/opencode/skills/`). The `execute` skill still always stops after a phase close — only Claude Code or Grok performs that close when Flash ran on units.

## Operator checklist

| Step | Model / role | Required? |
|------|----------------|-----------|
| Execute briefs / implement phase units | DeepSeek Flash (OpenCode map or equivalent) | **Encouraged** when rationing capacity |
| Review Flash unit work | **Sonnet 5.5** review agent | **Always** after Flash on the build path |
| **Hold** — phase review before close | — | **Always** when Flash ran on units; no auto close-out |
| Phase outcome verification + `Workflow-Phase:` close | **Claude Code** or **Grok** (orchestrator) | **Always** for sign-off; not Flash |

## Rationale (one paragraph)

Flash stretches orchestrator capacity across more unit work without changing workflow quality bars. The gate is narrow: Sonnet 5.5 reviews Flash output, then Grok or Claude Code signs the phase so boundaries stay with the Build Orchestrator and Flash never auto-closes a phase.
