# Unit report: 7-04 — Design doc contract sections

**Status:** done

## What changed (against brief)

- `docs/design/02-edge-capture.md`: queue/config paths, `YAKKA_QUEUE`, `yakka` subcommands, wrapper kick path.
- `docs/design/03-remote-service.md`: Go `yakka` binary, `YAKKA_SERVE_*`, `packages/yakka/catalogue`, data dir under `~/.local/share/yakka`.
- `docs/design/04-advisory-surface.md`: `yakka mcp`, wrapper registration path; phase/PR markers point at system-architecture dual-read section.
- `docs/design/05-distribution.md`: layout table, wrapper, env, per-harness rows, release artifacts (`yakka-<os>-<arch>`), `packages/opencode-yakka-hooks`.
- `docs/design/07-analytics-site.md`: `packages/yakka-analytics`, embed paths, `YAKKA_*` serve/bench env, `yakka-analytics-*` `localStorage` keys (dated cutover section left historical).
- `docs/design/system-architecture.md`: Go `yakka` runtime row; new **Plan folder and phase closure** with trailer dual-read rule.
- `docs/design/01-event-model-and-ingest.md`, `conversation-indexer.md`: no contract renames required (scan already clean).

## Residual scan (`docs/design/`)

**Before** (`python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^docs/design/'`): 33 hits across `02`, `03`, `04`, `05`, `07`.

**After:** no output (exit 0 for that pipeline).

## Done-evidence checks

```
rg 'Yakka-Plan|Workflow-Phase' docs/design/04-advisory-surface.md docs/design/system-architecture.md
→ dual-read + Yakka-Plan in system-architecture.md

rg 'packages/yakka' docs/design/05-distribution.md
→ layout rows present
```

## Deviations

- Dual-read prose lives primarily in `system-architecture.md#plan-folder-and-phase-closure`; `04-advisory-surface.md` links there instead of repeating the full paragraph (avoids duplicating trailer keys in two contract sections).
- `05-distribution.md` `RELEASE_URL` now points at `https://github.com/codyhamilton/yakka/releases/download` (yakka repo URL from restructure design), not `workflow-plugin`.

## Contradictions

None found between updated contract sections and `docs/plans/13-monorepo-restructure/DESIGN.md` names table.

## Unfinished work

None for this brief.

## Known problems

None.
