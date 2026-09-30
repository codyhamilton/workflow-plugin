---
title: Classify human-label workflow and calibration report
status: proposed
author: Workflow Optimiser
date: 2026-09-30
---

# Classify calibration workflow

## Problem

Eight live classifications (2026-09-30) show **four `session_kind` rows with confidence &lt; 0.8** (`bd4f6c0d`, `77572779`, `a2be9531`, `eac38429`). JSONL rows still have `human_label: null` — we cannot compute accuracy or tune the 0.8 gate.

## Proposal

1. Document blind labeling steps in `tools/transcript/README.md` (or lab FINDINGS): label from taxonomy without peeking at Jev choice first.
2. Add a tiny script or `jq` recipe to merge labels into `.classify-log.jsonl` by `session_id`.
3. After ≥10 labeled rows, emit confusion matrix + calibration buckets (confidence deciles vs agreement).
4. Update FINDINGS with accept/reject threshold or taxonomy tweak.

## Success criteria

- ≥10 rows with `human_label` set.
- Report stored under `docs/lab/ANALYSIS/` or appended to FINDINGS.
- Explicit policy: auto-metrics only when `confidence ≥ 0.8` unless report says otherwise.

## Plugin tie-in

Feeds **`workflow-tuning`** observational harvest and future eval scenario selection (filter sessions by kind).
