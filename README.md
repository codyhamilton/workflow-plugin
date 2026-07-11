# workflow-plugin

Private plugin marketplace containing workflow skills for plan, execute, and review.

Machine-readable contract: [`workflow-protocol.json`](workflow-protocol.json) (`workflow-protocol: 1`).

## Skills

| Skill | Description |
|-------|-------------|
| `workflow-plan` | Create and revise implementation plans |
| `workflow-execute` | Execute planned work packages with delegation and review |
| `comprehensive-review` | Independent review of significant changes |
| `iterate` | Branching plan/execute/review for goals with no fixed spec — build divergent candidates, judge, reconcile, extrapolate |
| `workflow-setup` | Bootstrap stable docs (`docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`) |
| `workflow-tuning` | Improve the plan/execute/review workflow itself |
| `transcript-parser` | Extract cost metrics from session transcripts |

Generic names (`plan`, `execute`, `setup`) are namespaced as `workflow-*` so they do not collide with other skill packs when installed into shared skill directories.

Portable artifact rules live in [`protocol/artifacts.md`](protocol/artifacts.md). Harness-specific model recommendations live in [`protocol/models.yaml`](protocol/models.yaml) — keep those separate so model churn does not rewrite artifact contracts.

## Quick install (interactive)

```sh
git clone git@github.com:codyhamilton/workflow-plugin.git
cd workflow-plugin
./install.sh
```

## Non-interactive install (automations / Cursor Cloud)

Use explicit targets. This is the path when Team Marketplace is unavailable and skills must be installed into a cloud agent environment:

```sh
./install.sh --target cursor
./install.sh --target cursor --target claude
./install.sh --target all
./install.sh --target cursor --ref master
```

| Flag | Meaning |
|------|---------|
| `--target cursor` | Install into `~/.cursor/skills/` and mirror a checkout to `~/.cursor/plugins/local/workflow` |
| `--target claude` | Install into `~/.claude/skills/` |
| `--target codex` | Install into `~/.codex/skills/` |
| `--target all` | cursor + claude + codex |
| `--ref <tag-or-sha>` | Checkout that ref before copying (optional; default is the current checkout / master) |

Override destinations with `--cursor-skills`, `--claude-skills`, `--codex-skills`, or `--cursor-plugin` when needed.

Example cloud-agent install step:

```sh
git clone https://github.com/codyhamilton/workflow-plugin.git /tmp/workflow-plugin
/tmp/workflow-plugin/install.sh --target cursor --ref master
```

## Manual installation

### Claude Code / Codex / shared skill dirs

```sh
./install.sh --target claude
# or
cp -r skills/* ~/.claude/skills/
cp -r protocol ~/.claude/skills/_workflow-protocol
cp workflow-protocol.json ~/.claude/skills/_workflow-protocol/
```

For marketplace-style install (so colleagues can `/plugin install workflow@workflow-plugin`), register this repo in `~/.claude/plugins/known_marketplaces.json`:

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

Skills become available as `workflow:workflow-plan`, `workflow:workflow-execute`, etc.

### Cursor

Preferred without Team Marketplace (also what cloud agents should use):

```sh
./install.sh --target cursor
```

That copies skills into `~/.cursor/skills/` and maintains `~/.cursor/plugins/local/workflow`.

Or clone the plugin checkout manually:

```sh
git clone git@github.com:codyhamilton/workflow-plugin.git ~/.cursor/plugins/local/workflow
```

## Structure

```
workflow-plugin/
├── workflow-protocol.json      # workflow-protocol: 1
├── protocol/
│   ├── artifacts.md            # portable artifact rules
│   └── models.yaml             # harness model recommendations
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── .cursor-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── install.sh
└── skills/
    ├── workflow-plan/
    ├── workflow-execute/
    ├── workflow-setup/
    ├── comprehensive-review/
    ├── iterate/
    ├── workflow-tuning/
    └── transcript-parser/
```
