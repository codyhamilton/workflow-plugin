# Unit report: 6-02 — Core skills protocol and `yakka-tuning`

**Status:** done

## What changed (against brief)

- `plugins/yakka/skills/design/SKILL.md`: PR body marker `Yakka-Plan:` (writer).
- `plugins/yakka/skills/execute/SKILL.md`: `Yakka-Phase:` trailers, `Yakka-Plan:` PR line, `yakka-report` fence; one legacy-acceptance sentence.
- `plugins/yakka/skills/comprehensive-review/SKILL.md`, `post-build/SKILL.md`: resolve plan folder via `Yakka-Plan:`; one legacy-acceptance sentence each; `yakka-tuning` reference.
- `.claude/skills/workflow-tuning/` → `.claude/skills/yakka-tuning/` (`git mv`); `name: yakka-tuning`, titles and `reference.md` citations updated.
- `.claude/skills/setup/SKILL.md`: `/yakka:design` slash example.
- `.claude/skills/transcript-parser/SKILL.md`: `yakka-tuning` in description (no `workflow-plugin` literals were present).

## Grep / checks

**Before** (`rg 'Workflow-Phase|Workflow-Plan|workflow-report' plugins/yakka/skills/`):

- `comprehensive-review/SKILL.md` — `Workflow-Plan` (description + inputs)
- `design/SKILL.md` — `Workflow-Plan`
- `execute/SKILL.md` — `Workflow-Phase` (×4), `workflow-report`, `Workflow-Plan`
- `post-build/SKILL.md` — `Workflow-Plan`
- `comprehensive-review` also had `workflow-tuning` (separate grep)

**After:**

```
rg 'workflow-tuning' plugins/yakka/skills .claude/skills
→ no matches

rg 'workflow:(design|refine|execute)' .claude/skills/setup
→ no matches

test -d .claude/skills/yakka-tuning && test ! -e .claude/skills/workflow-tuning
→ exit 0

rg 'Workflow-Phase|Workflow-Plan|workflow-report' plugins/yakka/skills/
→ only legacy-acceptance sentences in comprehensive-review, execute, post-build
```

Phase 6 residual scan stub (`6-06`) not in tree; used focused `rg` per brief minimum.

## Judgement self-check

- `comprehensive-review`, `post-build`, `execute`: each has exactly one legacy-acceptance sentence naming `Workflow-Phase`, `Workflow-Plan`, and `workflow-report`.
- Writer instructions use `Yakka-Phase`, `Yakka-Plan`, and `yakka-report` where agents are told to emit artifacts.

## Deviations

None.

## Unfinished work

- `6-03` still owns `tools/driver/check_skills.py` `MAINTAINER_SKILLS` → `yakka-tuning` (per brief settled line).
- `.claude/skills/yakka-tuning/principles.md` still mentions `Workflow-Plan` / `Workflow-Phase` in historical seam prose (not in this unit's owned renames beyond the directory move).

## Known problems

None.
