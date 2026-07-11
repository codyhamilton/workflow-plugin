# workflow-plugin

Private plugin marketplace containing workflow skills for plan, execute, and review.

## Operating hypotheses

The workflow design rests on these assumptions. Some are informally validated (noted where), none are proven in the cloud-pipeline context. Each is falsifiable, and each names its validation route: **eval** (harness scenario runs, see `evals/`) or **observational** (harvested from real pipeline outcomes via workflow-tuning).

1. **Verbatim intent survives; paraphrase decays.** Capturing the human's actual words (request, issue, task) lets downstream agents match what was done to why — anchoring review placement, QA derivation, and gap-filling. Paraphrase loses the intent that matters. *(Informally validated in human workflows. Observational.)*
2. **Briefs beat messengers.** Context authored once by its owner and routed verbatim to its consumer outperforms orchestrator paraphrase — in subagent prompt quality (especially long-context jobs) and in review-remediation accuracy. *(Observed in iterate; untested as a plugin-wide invariant. Eval.)*
3. **A plan is a deliverable, not a stop on the way to a build.** A dedicated planning context produces more accurate plans than a fused plan-build workflow, and separation enables gating, plan validation, adversarial planning, and plans that are valuable unbuilt. *(Observed in iterate's divergence cycles; untested as a head-to-head. Eval.)*
4. **Status belongs to the tracker, not the repo.** Removing the repo backlog (folder-status taxonomy, roadmap sync) sheds structural-compliance load without losing recoverability, because durable artifacts carry intent and outcome while PRs carry status. *(Untested. Observational.)*
5. **Orienting-why beats persuading-why.** Skills that state the failures they prevent help agents fill unspecified gaps; prose that argues the design's correctness costs context without changing behavior. *(Untested. Eval.)*
6. **A cold reader keeps plans honest.** Plan quality holds only when a separate context must work from the artifacts alone — the executor locally, the downstream review stage in a pipeline. *(Untested. Observational.)*

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
