---
title: Jev hook assertion spike (offline fixture)
status: proposed
author: Workflow Optimiser
date: 2026-09-30
---

# Jev hook assertion spike

## Problem

We have session-level classify (`session_kind`, `workflow_alignment`). We lack **artifact-level** typed checks cheap enough to run in eval or post-phase verify (e.g. “does this `IMPLEMENTATION.md` mention verification evidence per unit?”).

## Proposal

1. Define one **Noul or Score** question over a JSON `state` built from plan folder artifacts (not full chat) — e.g. parse headings from `IMPLEMENTATION.md` + phase list from `DESIGN.md`.
2. Implement a dry-run CLI beside `classify.py` (`--dry-run` pattern) that prints request JSON without POST.
3. Run against 3 fixture folders (synthetic or redacted from `docs/plans/`).
4. Document expected use: optional hook after `execute` verify, **offline only** in v0.

## Success criteria

- Pinned `jev-1.13.0` request JSON checked into `evals/` or `tools/transcript/fixtures/` (no API keys).
- Clear accept/reject threshold documented (e.g. Score ≥ 2.5).
- BACKLOG item for live POST gated on classify calibration.

## Maps to research

Evaluator–optimizer loop (LangGraph); TypeSafe Choice/Score ([docs.typesafe.ai](https://docs.typesafe.ai/)).
