---
title: Fix Claude user-text extraction for Jev snapshots
status: deferred
deferred_reason: Snapshot parity between Claude and Cursor is not a blocker. Classify is visualisation-only.
author: Workflow Optimiser
date: 2026-09-30
---

# Fix Claude snapshot user-message text (newline-per-char)

**Status: deferred** (2026-09-30 strategy pass). The distortion hypothesis in FINDINGS still stands. It does not gate driver work or outcome metrics. Reopen only if a visualisation the collector relies on is unreadable.

## Problem

Live Jev classify batch (8 sessions, 2026-09-30) shows **much higher `snapshot_token_estimate` for claude-code** (284–878) than Cursor (103–143) while labels remain mostly plausible. Suspected cause: user query text in snapshots is built with **newline joins between per-character or per-token fragments**, inflating size and distorting signal for Jev.

Pointers: `tools/transcript/lib/snapshot.py` (reads `user_queries[].text` from extract JSON); `tools/transcript/parsers/claude.py` (`_extract_user_queries`).

## Proposal

1. Reproduce on one claude-code session: dump `first_user_message` from snapshot vs raw extract.
2. Fix join logic (likely `"".join` vs `"\n".join` when content items are single-character strings, or normalize Claude content blocks).
3. Add a small fixture test under `tools/transcript/` with redacted excerpt JSON.
4. Re-run classify on the same session IDs; compare `snapshot_hash` and token estimate.

## Success criteria

- Claude snapshot token estimates in line with visible user message length (order-of-magnitude).
- No regression for Cursor snapshots.
- Low-confidence classify rows optionally re-checked after fix.

## Non-goals

- Taxonomy changes to Jev Choice labels.
- Storing full transcripts in repo.
