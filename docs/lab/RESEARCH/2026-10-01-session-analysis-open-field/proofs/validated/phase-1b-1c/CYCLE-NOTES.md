# Phase 1b + 1c cycle notes

**Date:** 2026-10-01  
**Live TypeSafe POSTs:** 0

## 1b Framing registry

- `framing/registry.json`: **10** registered `early-signal-v0` blobs (8 open-field tournament/pool slugs + 2 cheap-analysis spike slugs).
- `framing/REGISTRATION-TEMPLATE.md`: documents **8 baseline / 24 search** split and `unregistered_framing` handling.
- `dry_run_batch_log.json`: 8 workers × 4 tournament framings, dedupe row, cap-at-1 live-shaped check, dummy key absent from artifact.
- `manifests/card_hash_manifest.json`: placeholder stats cards for **n = 34** from shape-qual pack (pending phase **1a** extractor).

## 1c Mount probe

- `WORKFLOW_PROGRESSIVE_CORPUS` unset; default redacted maps fixtures used.
- Pilots: mix of `file_missing` (not in committed fixture set), `prose_required` on redacted JSONL, no `prose` on this VM without a raw Ubuntu mount.
