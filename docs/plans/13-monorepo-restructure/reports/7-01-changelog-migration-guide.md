# Unit report: 7-01 — CHANGELOG migration guide

**Status:** done

## What changed (against brief)

- Inserted top `## 3.0.0 — 2026-10-18 — rename to yakka` in `CHANGELOG.md` with: full `WORKFLOW_*` → `YAKKA_*` table (Phases 5–6 inventory from `packages/yakka`, `plugins/yakka`, `tools/driver`, `install.sh`, `packages/hooklog`, `packages/opencode-yakka-hooks`), state-path table, four numbered harness remove-then-install blocks, `.gitignore` note, MCP/skill-prefix note, eight numbered maintainer actions, and explicit double-hook warning.
- All prior changelog sections unchanged below the new entry.

## Evidence

| Check | Result |
|-------|--------|
| Before: `grep -i rename CHANGELOG.md` | no match |
| After: `python3 -c "import re; t=open('CHANGELOG.md').read(); assert re.search(r'(?m)^##\\s+.*\\brename\\b', t, re.I)"` | exit 0 |
| `rg 'WORKFLOW_QUALITY_' CHANGELOG.md` | only in **Exception** paragraph (quality service unchanged) |

**Phase 7 [cmd] checklist (section headings in `CHANGELOG.md`):**

| Clause | Section |
|--------|---------|
| Env map | `### Environment variables (WORKFLOW_* → YAKKA_*)` |
| State paths | `### State paths` |
| Four harness blocks | `### Per-harness remove, then install` (Claude, Cursor, Codex, OpenCode) |
| Maintainer actions | `### Maintainer actions (outside this repo)` |

## Deviations

- Env inventory included `packages/hooklog` and `packages/opencode-yakka-hooks` (not only the four paths in required reading) so OpenCode/hooklog vars (`YAKKA_HOOKLOG_SPOOL`, `YAKKA_ANALYTICS_*`, etc.) appear in the map; suffix rule matches DESIGN.
- Documented `WORKFLOW_HOOKLOG_CLI` removal (no `YAKKA_*` successor) beside the `WORKFLOW_QUALITY_*` exception.
- Omitted `YAKKA_QUALITY_URL` from the table (tests only; quality URL stays `WORKFLOW_QUALITY_URL`).
- Omitted `YAKKA_LEGACY` (OpenCode test hook only).

## Contradictions

- None found between `CHANGELOG.md` and `install.sh`, `tools/cloud-env/bootstrap-yakka-skills.sh`, `plugins/yakka/.mcp.json`.

## Unfinished work

- None for this unit.

## Known problems

- None.
