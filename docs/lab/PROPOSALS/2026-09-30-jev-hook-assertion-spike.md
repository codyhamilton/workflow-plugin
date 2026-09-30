---
title: Jev phase-boundary assert (steer and log)
status: landed
author: Workflow Optimiser
date: 2026-09-30
updated: 2026-09-30
---

# Jev phase-boundary assert

## Problem

The bot can see a `workflow-report` and a git trailer. It cannot yet apply a typed alignment check on the closing record — for example, whether the phase outcome's evidence is actually present — and it cannot log that check separately from session-kind visualisation.

`tools/transcript/classify.py` answers "what kind of chat was this?" It is not this spike.

## Proposal

1. Pick **one** Score or Noul question over JSON `state` built from the plan folder and the trailer just observed (headings in the closing record, the outcome line from `DESIGN.md`, the report's `phase`). No transcript snapshot.
2. CLI beside the future driver: `tools/driver/assert_phase.py --dry-run` prints the Jev request; `--live` POSTs with pin `jev-1.13.0` and appends a gitignored assert log, not `.classify-log.jsonl`.
3. Two fixtures: one that should pass, one that should fail. Document the threshold (for example Score ≥ 2.5).
4. On fail, the bot stops and escalates even if the report said `closed`.

## Success criteria

- Dry-run request JSON checked in with no API key.
- Pass fixture and fail fixture agree with the threshold.
- Fail fixture yields a log row and the fail branch.

## Kill line

If the assert disagrees with a deterministic check available in the same state, drop the Jev call and keep the check. Do not open classify calibration to repair it.

## Maps to research

Evaluator–optimizer (LangGraph docs); TypeSafe Choice/Score ([docs.typesafe.ai](https://docs.typesafe.ai/)). Strategy: [`../ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../ANALYSIS/2026-09-30-grokbot-driver-reorient.md) step 3 / spike C.
