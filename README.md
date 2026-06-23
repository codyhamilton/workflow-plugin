# workflow-plugin

Private plugin marketplace containing workflow skills for plan, execute, and review.

## Skills

| Skill | Description |
|-------|-------------|
| `plan` | Create and revise implementation plans |
| `execute` | Execute planned work packages with delegation and review |
| `comprehensive-review` | Independent review of significant changes |
| `iterate` | Branching plan/execute/review for goals with no fixed spec — build divergent candidates, judge, reconcile, extrapolate |
| `workflow-tuning` | Improve the plan/execute/review workflow itself |

## Quick install

```sh
git clone git@github.com:codyhamilton/workflow-plugin.git
cd workflow-plugin
./install.sh
```

The installer detects opencode, Claude Code, and Cursor and asks before installing into each. No flags, no config required.

## Manual installation

### Claude Code / opencode

Both Claude Code and opencode use the same skills directory. Copy skills directly:

```sh
cp -r skills/* ~/.claude/skills/
```

Skills are available immediately. For marketplace-style install (so colleagues can `/plugin install workflow@workflow-plugin`), register this repo in `~/.claude/plugins/known_marketplaces.json`:

```json
{
  "workflow-plugin": {
    "source": {
      "source": "github",
      "repo": "codyhamilton/workflow-plugin"
    },
    "installLocation": "~/.claude/plugins/marketplaces/workflow-plugin"
  }
}
```

Then install with:

```
/plugin install workflow@workflow-plugin
```

Skills become available as `workflow:plan`, `workflow:execute`, etc.

### Cursor

Clone the repo into Cursor's local plugins directory, then restart Cursor:

```sh
git clone git@github.com:codyhamilton/workflow-plugin.git ~/.cursor/plugins/local/workflow
```

Or run `./install.sh` and accept the Cursor prompt.

## Structure

```
workflow-plugin/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── .cursor-plugin/plugin.json
└── skills/
    ├── plan/
    ├── execute/
    ├── comprehensive-review/
    └── workflow-tuning/
```
