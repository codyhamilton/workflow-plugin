---
cursor:
  subagentId: "bc-7bbf10da-cbf5-59a1-8d03-4b0c370855c9"
---

# Unit report: 7-05 — Automation post-build and eval fixture prose

**Status:** done

## What changed (against brief)

- `docs/automation/post-build.md`: product references now name the `yakka` plugin; install at `plugins/yakka`; canonical prompt loads `post-build` from `plugins/yakka/skills/` and Cursor project skills under `.cursor/skills/yakka/`. Kept “post-build workflow” and “workflow policy” where they mean the stage/method, not the plugin name.
- `evals/scenarios/trailer-completeness/source.md`: Repo URL line → `https://github.com/codyhamilton/yakka`. Task text still exercises `Workflow-Phase` and `Yakka-Phase` trailer keys unchanged.

## Done evidence

**Before:**

```
$ python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^(docs/automation/post-build|evals/scenarios/trailer-completeness/source)'
docs/automation/post-build.md:50:.cursor/(plugins/local|skills)/workflow
evals/scenarios/trailer-completeness/source.md:5:\bworkflow-(plugin|analytics|tuning|lab|signals|quality-placeholder)\b
```

**After:**

```
$ python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^(docs/automation/post-build|evals/scenarios/trailer-completeness/source)'
→ no output

$ rg 'github.com/codyhamilton/yakka' evals/scenarios/trailer-completeness/source.md
- URL: https://github.com/codyhamilton/yakka

$ rg '\.cursor/skills/yakka' docs/automation/post-build.md
`.cursor/skills/yakka/`; Claude Code
```

## Deviations

None.

## Contradictions

None observed between the brief, `DESIGN.md` Phase 7 surfaces, and `plugins/yakka/skills/post-build/SKILL.md` (`Yakka-Plan` / legacy `Workflow-*` acceptance in the skill vs `Workflow-Plan:` in `post-build.md` operator prose is intentional cross-era compatibility, not a conflict).

## Unfinished work

None for this brief.

## Known problems

None.
