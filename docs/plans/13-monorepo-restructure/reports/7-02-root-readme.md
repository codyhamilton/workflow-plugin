# Unit report: 7-02 — Root README install and layout prose

**Status:** done

## What changed (against brief)

- Root `README.md`: title and identity (`yakka`, `codyhamilton/yakka`); clone/curl/marketplace install (`yakka@yakka`, `~/.cursor/plugins/local/yakka`, `.cursor/skills/yakka/`); env vars `YAKKA_*`; phase trailers `Yakka-Phase:` / `Yakka-Plan:` with CHANGELOG pointer for legacy trailers; OpenCode package `packages/opencode-yakka-hooks` and signal log default `~/.local/state/yakka/jev-signal-log.jsonl` (`YAKKA_JEV_SIGNAL_LOG`); monorepo layout tree (`plugins/yakka`, `packages/yakka`, `packages/opencode-yakka-hooks`, `plugins/yakka/bin/yakka`); hooklog queue/drain prose; cloud bootstrap `bootstrap-yakka-skills.sh`; removed stale `workflow-plugin` / `tools/driver/.jev-signal-log.jsonl` literals.

## Residual scan (`python3 tools/release/scan_residual_names.py --scope all`)

| | README.md hit count |
|---|---------------------|
| Before | 43 |
| After | 0 |

## Done evidence (grep)

| Check | Result |
|-------|--------|
| `rg 'codyhamilton/yakka' README.md` | clone, raw install URL, marketplace `repo` |
| `rg 'yakka@yakka' README.md` | install/update/marketplace examples |
| `rg 'tools/driver/\.jev-signal-log' README.md` | no matches |
| `rg 'workflow-plugin\|workflow@workflow-plugin' README.md` | no matches |
| `scan_residual_names.py --scope all` → `README.md:` | no output |

## Deviations

- Legacy `Workflow-Phase:` acceptance is described via “legacy phase/plan trailers” + `CHANGELOG.md` instead of spelling `Workflow-Phase:` in README (residual scanner flags that trailer string outside skill legacy lines).
- Added an explicit **Cursor desktop** install bullet (`~/.cursor/plugins/local/yakka`) in Quick install; brief listed the path in contract prose but not as a numbered change.

## Unfinished work

None for this unit.

## Known problems

None identified; `docs/lab/` historical links left unchanged per brief.
