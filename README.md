# workflow-plugin

Private plugin marketplace containing workflow skills for planning, execution, and review.

## Skills

| Skill | Description |
|-------|-------------|
| `planning` | Create and revise implementation plans |
| `plan-execution` | Execute planned work packages with delegation and review |
| `comprehensive-review` | Independent review of significant changes |
| `workflow-tuning` | Improve the plan/execute/review workflow itself |

## Quick install

```sh
git clone git@github.com:codyhamilton/workflow-plugin.git
cd workflow-plugin
./install.sh
```

The installer detects Claude Code and Cursor and asks before installing into each. No flags, no config required.

## Manual installation

### Claude Code

Copy skills directly to your user skills directory:

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

Skills become available as `workflow:planning`, `workflow:plan-execution`, etc.

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
    ├── planning/
    ├── plan-execution/
    ├── comprehensive-review/
    └── workflow-tuning/
```
