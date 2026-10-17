# Unit report: 2-06 — Prose, stable docs, and changelog

**Status:** `blocked` (phase [cmd] residual scan; unit owned surfaces `done`)

## What changed

- `skills/execute/SKILL.md`, `skills/refine/templates/brief.md`: rubric → `packages/workflow/catalogue/checks/execution-report.json`.
- `.claude/skills/jev-variants/SKILL.md`: hooklog path → `packages/hooklog`.
- `docs/design/{01,03,05,07}-*.md`: layout and path prose for `packages/workflow`, `packages/hooklog`, `packages/workflow/catalogue`; removed stale "monorepo reorganisation" deferral from 05.
- `README.md`: hooklog doc links → `packages/hooklog/README.md`.
- `CHANGELOG.md`: `## 2.11.0` (package moves + absolute `tools/hooklog/spool.sh` migration warning).
- `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`: `2.10.0` → `2.11.0`.
- `.claude/skills/workflow-tuning/reference.md`: no `tools/*` path literals present; unchanged.

## Search command output

Owned-path checks:

```bash
rg 'tools/quality/checks/execution-report' skills
# (no output)

rg '"version":' .claude-plugin/plugin.json .cursor-plugin/plugin.json .codex-plugin/plugin.json
# "version": "2.11.0" (each file)
```

Phase 2 [cmd] scan (live tree; exclude `docs/plans/**`, `docs/lab/**`; exclude historical `CHANGELOG.md` lines below `## 2.11.0`):

```bash
rg 'tools/workflow|tools/hooklog|tools/quality/criteria\.json|tools/quality/checks' \
  --glob '!docs/plans/**' --glob '!docs/lab/**' \
| awk -F: '$1=="CHANGELOG.md" && $2+0>=21 {next} {print}'
```

```
CHANGELOG.md:  `.../tools/hooklog/spool.sh` from an older example, update it to `.../packages/hooklog/spool.sh`
CHANGELOG.md:  `tools/hooklog/codex-hooks.example.json` is removed; ...
CHANGELOG.md:- Hooklog capture is now a bash spooler plus an async drain. Hooks run `tools/hooklog/spool.sh`, ...
CHANGELOG.md:  `tools/hooklog/drain.py` normalises and scrubs, ...
packages/workflow/internal/ingest/normalise.go:// tools/hooklog/hooklog.py normalize() ...
packages/hooklog/hooklog.py:(tools/workflow) normalises, scrubs and posts it. ...
```

Interpretation: `2.11.0` changelog may cite the old spool path (DESIGN). Remaining hits are pre-`2.11.0` changelog bullets (exempt) plus two comment lines outside this brief's owned paths.

Path-segment forms (`'tools', 'hooklog'`, `../../../quality`): no hits outside `docs/plans/`.

## Deviations

- Phase [cmd] scan not clean: `packages/workflow/internal/ingest/normalise.go` and `packages/hooklog/hooklog.py` still contain forbidden literals in comments. Brief forbids editing outside owned paths; not fixed here.

## Contradictions

- Unit done evidence requires a clean live scan; brief also says do not fix non-owned files when hits remain → report `blocked` and commit owned prose/manifest/changelog only.

## Problems outside this unit's done evidence

Orchestrator-only: Claude hook session, `bin/workflow --version` with cache cleared, full `tools/release/build.sh`.
