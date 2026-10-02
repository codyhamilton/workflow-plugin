---
name: lab-proposal
description: Legacy lab signal triage and proposal layout. Use for maintaining an existing lab-proposal artifact. For new evidence-backed white paper research, use the white-paper skill.
---

# Lab proposal

> **Current research method:** For new work, use [`../white-paper/SKILL.md`](../white-paper/SKILL.md). This file records the older lab proposal convention and may help maintain existing documents. Its fixed model-role pipeline and proposal-first structure do not establish tested facts.

Lightweight path from **signal** to **research pack** to **white paper proposal**. This is not the full `design` → `execute` pipeline; it produces lab docs only until Cody accepts behaviour changes.

## When to use

- A recurring pattern shows up in transcripts, driver logs, evals, or weekly FINDINGS and needs a written recommendation before code changes.
- Grok Bot / Workflow System Manager triage says the question is worth a white paper (bounded scope, measurable success, additive lab landing).
- You are a **Composer cloud agent** asked to **collect** sources into a research pack — not to write the final `PROPOSALS/*.md` (that is a **Grok 4.7 high reasoning** pass).

## Pipeline

### 1. Signal

Signals are observations, not gates. Typical sources:

- Usage / transcript analysis (turns, context, 5h rolling windows, subagent band violations)
- Claude Code hook events (PostToolBatch, compaction, subagent lifecycle, stop failures)
- `docs/lab/FINDINGS.md`, driver `run_record` / assert JSONL
- Assert vs deterministic **disagreement** rows (`jev.disagreed_with_deterministic`)
- Mis-sized sessions (OVER_TURNS, OVER_CTX, fat JSONL) from lab tooling

Record the signal in one paragraph: what happened, where the data lives, why it might matter economically.

### 2. Triage (Grok Bot / Workflow System Manager)

Before spending research tokens:

- **Worth a white paper?** If no → append a FINDINGS bullet or BACKLOG line and stop.
- **Name the question** in one sentence (e.g. “Where should cheap Jev judgements sit between deterministic checks and human escalation?”).
- **Success metric** — what would “accepted” change in behaviour or measurement (not “ship code”).
- **Non-goals** — explicitly out of scope for this proposal (e.g. no classify calibration, no redo of landed phase assert).

Triage output: go/no-go, question, metric, slug (`YYYY-MM-DD-<slug>`).

### 3. Research pack (Composer cloud agents)

Dispatch **fresh, bounded** collector agents. **Never use fast-tier models** for research packs.

Material lands under:

`docs/lab/RESEARCH/<YYYY-MM-DD>-<slug>/`

Required:

- **`INDEX.md`** — what to collect, how each note maps to upcoming proposal sections, links to sibling docs.
- **Source notes** — short markdown files (or a single `SOURCES.md`) with citations, in-repo pointers, and concrete numbers where available.

Rules:

- Additive docs only; do not change runtime hooks or driver behaviour in this step.
- Link prior landed proposals and ANALYSIS passes; state how this paper is the **next layer**, not a redo.
- Pull numbers from attached analysis artifacts when present.

### 4. White paper (Grok 4.7 high reasoning)

**Not** part of the research-pack agent’s job. A separate Grok pass writes:

`docs/lab/PROPOSALS/<YYYY-MM-DD>-<slug>.md`

Inputs: research pack `INDEX.md` + notes + triage question/metric.

Posture:

- **Soft recommendations** — signals steer attention; they do not hard-gate merges or phases by default.
- **Jev behind deterministic conditions** where enforcement exists (phase assert kill line is the pattern).
- **No classify-as-KPI** strategy path.
- Wait for **Cody** before shipping behaviour into skills, hooks, or driver defaults.

After the white paper exists:

- Link it from `docs/lab/RESEARCH/INDEX.md` and add a row or bullet in `docs/lab/BACKLOG.md`.
- Weekly lab review skims open proposals (`status: draft|open`).

## White paper structure

Use YAML frontmatter on the proposal file:

```yaml
---
title: <human title>
status: draft | open | accepted | deferred | done
date: YYYY-MM-DD
signal: <one-line signal that triggered triage>
owners: <Workflow Optimiser, Cody, …>
---
```

Body sections (in order):

1. **Signal** — evidence and pointers (FINDINGS, charts, log excerpts).
2. **Problem** — what fails today; who pays (tokens, time, escalation noise).
3. **Proposal** — recommended hooks, judgements, or process changes (soft by default).
4. **Economics** — why cheap conditional Jev (or similar) beats always-on frontier review.
5. **Non-goals** — explicit exclusions.
6. **Measurement** — how to know the proposal worked without turning session classify into a KPI.
7. **Next spikes** — smallest implementable experiments after acceptance.

## Rules (lab policy)

| Rule | Meaning |
|------|---------|
| Signals steer, not hard-gate | Default: log, surface, weekly skim — not block CI or phases unless Cody promotes a rule. |
| Jev behind deterministic conditions | Authoritative pass/fail stays mechanical where git/state already answers; Jev is advisory or logged. |
| No classify-as-KPI | `tools/transcript/classify.py` stays visualization; eval verifiers and asserts are the measurement path. |
| Additive lab docs | Prefer new `RESEARCH/` and `PROPOSALS/` entries; avoid breaking core skills or driver contracts. |

## Related lab entry points

- Notebook: [`docs/lab/README.md`](../../../../docs/lab/README.md)
- Research index: [`docs/lab/RESEARCH/INDEX.md`](../../../../docs/lab/RESEARCH/INDEX.md)
- Backlog: [`docs/lab/BACKLOG.md`](../../../../docs/lab/BACKLOG.md)
- Control policy: [`docs/lab/ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../../../../docs/lab/ANALYSIS/2026-09-30-grokbot-driver-reorient.md)
