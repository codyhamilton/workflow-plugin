# CYCLE — batch-002 multi-driver lever waves (Soft HOLD)

**Date:** 2026-10-02 AEST  
**Status:** measuring at volume — Soft Standard **HOLD** (no hooks / product unlock)  
**Join keys:** `session_id` + `checkpoint` (OUTCOME-SHEET). **Do not invent outcome labels.**

## Ping meters (live corpora with results.jsonl)

| Wave / dir | Driver | n_cells | fire | parse_miss | leak | notes |
|------------|--------|---------|------|------------|------|-------|
| typesafe | TypeSafe | 180 | 0 | 0 | 0 | H1-only first fill |
| typesafe-h25 | TypeSafe | 240 | 7 | 0 | 0 | H1–H5 interleaved |
| **typesafe-k1** | TypeSafe | **2500** | 35 | 0 | 0 | 840 lever combos; denser schedule eligibility list; ~1.84M in / 142k out tok; wall 59s; H1–H5 ≈504 each |
| typesafe-scale | TypeSafe | 1132 | — | — | — | parallel scale wave (meters pending/partial) |
| flash-hframings | Flash | 240 | 46 | 0 | 0 | H1 skew first fill |
| luna (v0) | Luna | 72 | 0 | 72 | 0 | blocked: codex trust/`/tmp` |
| luna-h25 | Luna | 72 | 5 | 0 | 0 | fixed `--skip-git-repo-check` |
| luna-b | Luna | 180 | 35 | 0 | 0 | competing b-wave |
| flash/luna-vol1 | Flash+Luna | 800+200 tgt | TBD | TBD | TBD | streaming |

**Approximate cumulative live cells (excl. archive):** ~4600+ and climbing (k2 launching).

## Protocol

- R1 no T leak; R2 no length-derived outcome tags; R3 fixed/denser T-independent schedule.
- TypeSafe adaptation of Flash runner: System One `jev-1.13.0` one POST/cell; choice/score map → label/rating/fire.
- Soft HOLD — policy-under-test only.

## Credit / throttle

TypeSafe ~$10 credit open; k1 spent rough ~1.8M input tokens. **k2 streaming** toward further thousands.

## Soft HOLD confirmation

No Soft Standard unlock. No hooks ship. No product behaviour change.
