---
title: Archive Jev classify spike design in-repo
status: deferred
deferred_reason: POC archive for the classify visualisation. Not on the measurement path.
author: Workflow Optimiser
date: 2026-09-30
---

# Archive classify spike design doc

**Status: deferred / POC** (2026-09-30 strategy pass). The code on master is enough for a visualisation. An in-repo narrative can wait until someone is actively changing `classify.py`.

## Problem

Implementation landed in `tools/transcript/classify.py`, but the **full spike narrative** (taxonomy table, snapshot slices, out-of-scope list) currently lives only in external notes / chat exports.

## Proposal

Add `docs/lab/RESEARCH/2026-09-30-jev-classify-spike-design.md` (or link from `tools/transcript/README.md`) capturing:

- Choice taxonomy and Score legend (aligned with code constants)
- Snapshot field list and token caps
- Logging schema for `.classify-log.jsonl`
- Explicit out-of-scope (no full transcript POST, no indexer bodies)

Keep code as source of truth for flags; doc for humans and Optimiser.

## Success criteria

- Single in-repo URL for onboarding classify contributors.
- FINDINGS and INDEX link to it.

## Status note

**proposed** — content merge only, no runtime change.
