# Guidance — DeepSeek Flash / OpenCode review gate

**Status:** guidance (non-breaking). No installer, driver, or hook behaviour changes — operators and orchestrators follow this pattern by convention.

**Related:** OpenCode skills install and harness limits — [`README.md` § OpenCode](../../README.md#opencode-partial-compatibility). OpenCode hooks research (no resolved proposal doc; lab pack only) — [`RESEARCH/2026-09-30-opencode-hooks-plugin/`](RESEARCH/2026-09-30-opencode-hooks-plugin/INDEX.md).

## When this applies

This gate applies when **DeepSeek Flash** agents (or an equivalent cheap OpenCode map) are used on the **build path** — specifically to **execute briefs** or **implement phase units** under `execute`. That includes first-pass implementation during Claude availability gaps. The same intent applies if Flash is used outside OpenCode but in the same economic tier for unit work.

It does **not** relax design, refine, or plan-end `comprehensive-review` rules; it adds a **phase review hold** whenever Flash touched unit execution.

## Core rule

**Flash in the build path ⇒ the phase review gate is mandatory. No auto close-out.**

Flash workers must **not** close the phase automatically: no terminal phase verification, no `Workflow-Phase:` trailer, and no treating the phase as done. Using Flash for brief/unit work **auto-triggers the need for phase review** — stop and **hold** until **Grok** or **Claude Code** reviews the phase outcome and signs off.

## Required pattern

```
Flash draft (briefs / units)  →  Sonnet 5.5 review of Flash work  →  Claude Code or Grok phase validation and sign-off
```

1. **Flash may draft and implement freely** on assigned briefs and units. Speed and cost are appropriate here; Flash is not a signatory.
2. **Every use of Flash on the build path always triggers a Sonnet 5.5 review agent afterward — not optional.** Route Flash output (diffs, brief completion, unit reports) to an independent **Sonnet 5.5** pass keyed to the design phase outcome and brief done-evidence. Mandatory relay, not “if time permits.”
3. **Phase validation and sign-off are Claude Code or Grok only** (Build Orchestrator). They review the phase (including Sonnet’s review of Flash work), verify the phase outcome, and only then may land `Workflow-Phase:` and close the phase. **Never Flash alone**; **never** let a Flash run imply the phase is closed.

Flash does not replace `comprehensive-review` at plan end.

## What does not change

- **`assert_phase --deterministic`** remains the hard kill line for phase boundaries on any harness where it is wired.
- **Jev / PostToolBatch-style soft signals** stay **advisory** where installed (Claude Code, Cursor driver, OpenCode lab proofs). This guidance does not add enforcement hooks.
- **Skill names and install paths** are unchanged (`execute`, `comprehensive-review`, OpenCode symlinks under `~/.config/opencode/skills/`). The `execute` skill still always stops after a phase close — Flash simply **must not** perform that close.

## Operator checklist

| Step | Model / role | Required? |
|------|----------------|-----------|
| Execute briefs / implement phase units | DeepSeek Flash (OpenCode map or equivalent) | When chosen for economics |
| Review Flash unit work | **Sonnet 5.5** review agent | **Always** after Flash on the build path |
| **Hold** — phase review before close | — | **Always** when Flash ran on units; do not auto close-out |
| Phase outcome verification + `Workflow-Phase:` close | **Claude Code** or **Grok** (orchestrator) | **Always**; never Flash |

## Rationale (one paragraph)

Flash optimises tokens on brief and unit execution; it is not an orchestrator. Mandatory Sonnet 5.5 review of Flash work catches drift before orchestrator time. Requiring Grok or Claude Code to review and sign off keeps phase boundaries aligned with `execute` (orchestrator-owned close-out) and prevents unattended Flash runs from silently finishing a phase.
