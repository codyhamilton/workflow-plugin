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
cp -r plugins/workflow/skills/* ~/.claude/skills/
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

Copy the plugin to Cursor's local plugins directory, then restart Cursor:

```sh
cp -r plugins/workflow ~/.cursor/plugins/local/workflow
```

For Team Marketplace distribution (requires Cursor Teams/Enterprise), point your team to the `.cursor-plugin/marketplace.json` at the repo root.

## Structure

```
plugins/workflow/
├── .claude-plugin/plugin.json    # Claude Code plugin manifest
├── .cursor-plugin/plugin.json    # Cursor plugin manifest
└── skills/
    ├── planning/
    ├── plan-execution/
    ├── comprehensive-review/
    └── workflow-tuning/
```
