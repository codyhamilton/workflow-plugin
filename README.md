# workflow-plugin

Private plugin marketplace containing workflow skills for plan, execute, and review, split across
a cloud-safe core plugin and a local lab plugin.

## Breaking change: the folder-status taxonomy is removed

Earlier versions of this plugin used the repo itself as a backlog: `[NEW]-` prefixes on plan
folders, numeric renumbering as work progressed, a parent-program folder hierarchy, and
`docs/ROADMAP.md` as a canonical schedule. **All of that is gone.** A plan folder now means exactly
one thing — the work is being built or was built — and status lives in the PR and the issue
tracker, never in a folder name or a schedule doc. `setup` no longer creates `docs/ROADMAP.md`.

**There is no automated migration.** If a repo adopted the old convention via this plugin,
upgrading gets you the new behavior going forward; it does not rename, renumber, or touch existing
folders. Old numbered folders (including `[NEW]-` prefixed ones) remain valid as historical
provenance — leave them as they are. New plan folders from this version on follow the plain
`docs/plans/<NN>-<slug>/` convention with no status encoded in the name.

## Breaking change: `plan` is now `design`, and refinement is per phase

`plan` is renamed `design` and writes `DESIGN.md` (the old `PLAN.md` and optional `DESIGN.md`
merged). A design bounds the change — intent, problem, domain contracts, ownership — and cuts it
into phases each closed by a provable outcome, with the phase count fixed at sign-off. `refine`
now briefs one phase at a time against the code the previous phase left; `execute` runs one phase
per orchestrator, verifies the outcome, records carried items with the closing `Workflow-Phase:`
trailer, then always stops and reports. Review runs once, after the last phase. The folder path `docs/plans/<NN>-<slug>/` and the
`Workflow-Plan:` marker are unchanged, and folders already carrying `PLAN.md` are still read.
Skills are also rewritten to state outcomes and constraints rather than steps; see
`workflow-tuning/principles.md` #1 and `docs/analysis/2026-09-08-workflow-vs-field.md` §7.

## Operating hypotheses

The workflow design rests on these assumptions. Some are informally validated (noted where), none are proven in the cloud-pipeline context. We build to them now and evaluate later — a dedicated eval effort, out of scope for the current revisions, will test them. Each is falsifiable and names its validation route: **eval** (harness scenario runs, see `evals/`) or **observational** (harvested from real pipeline outcomes via workflow-tuning).

1. **Verbatim intent survives; paraphrase decays.** Capturing the human's actual words (request, issue, task) lets downstream agents match what was done to why — anchoring review placement, QA derivation, and gap-filling. Paraphrase loses the intent that matters. *(Informally validated in human workflows. Observational.)*
2. **Briefs beat messengers.** Context authored once by its owner and routed verbatim to its consumer outperforms orchestrator paraphrase — in subagent prompt quality (especially long-context jobs) and in review-remediation accuracy. *(Strong observational support: a mid-run skill edit in a 67-subagent `iterate` session gave a clean before/after — gate prompts decayed 1199→213 chars with guidance inline, and held at 2833–3716 across three later cycles once it moved into verbatim-passed briefs. See lesson 20 in `workflow-tuning/reference.md`. Still untested head-to-head as a plugin-wide invariant. Eval.)*
3. **A plan is a deliverable, not a stop on the way to a build.** A dedicated planning context produces more accurate plans than a fused plan-build workflow, and separation enables gating, plan validation, adversarial planning, and plans that are valuable unbuilt. *(Observed in iterate's divergence cycles; untested as a head-to-head. Eval.)*
4. **Status belongs to the tracker, not the repo.** Removing the repo backlog (folder-status taxonomy, roadmap sync) sheds structural-compliance load without losing recoverability, because durable artifacts carry intent and outcome while PRs carry status. *(Untested. Observational.)*
5. **Orienting-why beats persuading-why.** Skills that state the failures they prevent help agents fill unspecified gaps; prose that argues the design's correctness costs context without changing behavior. *(Untested. Eval.)*
6. **A cold reader keeps plans honest.** Plan quality holds only when a separate context must work from the artifacts alone — the executor locally, the downstream review stage in a pipeline. *(Untested. Observational.)*
7. **Outcome-closed phases absorb drift more cheaply than up-front briefing.** Every closed plan record in `docs/plans/` shows late-phase discovery; refining one phase at a time against real code, with a provable outcome closing each phase, lands that discovery in refinement instead of in the build orchestrator, and a verified outcome gives backward signal to the design. *(Argued in `docs/analysis/2026-09-08-workflow-vs-field.md`; untested. Eval.)*
8. **Cost is context integrated over turns.** Decomposition pays when saved reads exceed added cold starts — roughly past 40 to 75 turns for a cheap worker — and the controllable lever is context growth per turn. A fresh orchestrator per phase bounds the largest lifetime in the run. *(Modelled, not measured. Observational, via per-agent turn and context counts in `IMPLEMENTATION.md`.)*

### Variants worth testing

Beyond validating the hypotheses head-to-head, candidate variations to try when the eval effort runs:

- **Brief density**: minimal briefs (contract + code pointers) vs full-context briefs (inlined excerpts) — where does long-context reliability actually come from?
- **Handoff purity**: execute dispatched with the plan folder alone vs plan folder plus a planner-written summary — does extra warm context help the executor or contaminate the cold read?
- **Plan review shape**: single clean adversarial reviewer (current) vs a short sequential relay (iterate's harden pattern applied at plan stage) for ordinary plans.
- **Remediation split**: iterate's split (straightforward fixes applied inline during review, briefs only for structural findings — now the core design) vs the all-briefs baseline (reviewer briefs everything, fixers and a fresh re-review handle all findings).
- **QA authorship**: QA plan derived by the review stage from acceptance criteria (current design) vs authored by the plan stage upfront and merely executed downstream.
- **Assumption-ledger salience**: ledger inline in DESIGN.md vs a separate surfaced artifact at the checkpoint — does presentation change how often humans intervene, and to what benefit?
- **Refinement horizon**: one phase at a time (current design) vs all phases up front — how much of the up-front brief set is invalidated by later-phase discoveries, and what does re-dispatch cost?
- **Phase verification tier**: cheap-tier outcome check per phase plus one terminal premium review (current design) vs premium review at every boundary.

## Skills

Two plugins. **Core** (`workflow`) is cloud-safe — no interactive gates that dead-end headless, no
local-filesystem dependencies — and is what a build/pipeline environment installs. **Lab**
(`workflow-lab`) is local and/or interactive; the pipeline never requires it.

The loop: **design → (refine → execute → verify → close) per phase → review → close-out.** A design
fixes phases each closed by a provable outcome; each phase is refined against the code the previous
phase left, built by a fresh orchestrator, and verified before the next is refined. `refine` is
skipped for a one-unit phase.

| Plugin | Skill | Description |
|--------|-------|-------------|
| `workflow` (core) | `design` | Bound a change: verbatim intent, domain contracts, phases with provable outcomes; interactive or headless posture |
| `workflow` (core) | `refine` | Decompose the next phase into units and write one complete brief per unit against the current code; bounce the design if a contract, boundary, or outcome is missing |
| `workflow` (core) | `execute` | Build one phase: route briefs to rightsized workers, verify the outcome, record carried items and close with a trailer, then stop and report; terminal review and close-out after the last phase |
| `workflow` (core) | `comprehensive-review` | Independent review keyed to the design's phase outcomes; fixes mechanical findings in place, briefs structural ones |
| `workflow` (core) | `close-out` | End a plan: collapse the folder into one record file at `docs/plans/<NN>-<slug>.md`, promote durable contracts to `docs/design/`, delete the folder in one commit |
| `workflow` (core) | `post-build` | Pipeline stage against a PR: classify/right-size, review, bounded remediation for briefed findings, conditional QA + exact-SHA deploy proof, end-of-work required-checks gate, merge-readiness report (repo mechanics via a per-repo adapter skill) |
| `workflow-lab` | `setup` | Bootstrap `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` for a repo that lacks them |
| `workflow-lab` | `iterate` | Divergent candidates, judge, reconcile, extrapolate — for goals with no fixed spec, or for a design phase flagged approach-open |
| `workflow-lab` | `transcript-parser` | Extract cost metrics (agents, tool turns, context, wall time) from a session transcript |
| `workflow-lab` | `workflow-tuning` | Improve the workflow itself — design principles, lessons from retros and merged-PR outcomes, evals |

**Workflow Optimiser workspace:** research, goals, findings, and proposals for tuning this plugin live in [`docs/lab/`](docs/lab/) (maintained in-repo; separate from the interactive `workflow-lab` skills under `plugins/workflow-lab/`).

### Grok Bot / unattended driver

Skills from this plugin are **not** auto-visible to Grok Bot or other cloud drivers until the **consuming** repo bootstraps them. Cursor cloud boots from a prebaked image: bake core-only `install.sh` (`docs/lab/bootstrap/cursor-cloud-setup.sh`) into that image. Claude Code on the web: SessionStart hook (`docs/lab/bootstrap/session-start.sh`). The measurable loop is driver CLIs, not chat classify:

0. `python3 tools/driver/check_skills.py` — exit 0 when the six core skill directories are on disk for this harness
1. `python3 tools/driver/status.py <plan-folder>` — open phase from git trailers
2. `python3 tools/driver/run.py <plan-folder> --once` — one phase; provider by API key
3. `python3 tools/driver/assert_phase.py --state <compact-state.json>` — phase-boundary assert (Jev logged; deterministic pass/fail)

Repeat 1–3 until `done` or `unsuccessful`. Lab skills are not required. Details: [`tools/driver/README.md`](tools/driver/README.md) and paste template [`docs/lab/CONSUMING_REPO.md`](docs/lab/CONSUMING_REPO.md).

To trigger `post-build` from an external automation (e.g. a Cursor Automation), see
[`docs/automation/post-build.md`](docs/automation/post-build.md): one orchestrated automation
per stage, triggered once per build handoff, with repo mechanics supplied by a per-repo adapter skill.

## Quick install

```sh
git clone git@github.com:codyhamilton/workflow-plugin.git
cd workflow-plugin
./install.sh
```

The installer detects **Claude Code** and **Cursor** (and asks before installing into each). It does
**not** auto-detect OpenCode — use the OpenCode path below (`WORKFLOW_INSTALL_MODE=opencode` or
`./install.sh --opencode-skills`). Core and lab are separate prompts on the interactive path, so a
cloud build image can accept core only. No other config required for Claude/Cursor routes.

When run non-interactively (piped via `curl | bash`, or invoked by an agent's Bash tool, which
never has a TTY), the installer skips the prompts and auto-installs **core only** (never
`workflow-lab`). `WORKFLOW_INSTALL_MODE=cloud`, `claude-code`, or `interactive` forces that route
and wins over ambient variables.

- **Claude Code** (`CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, or `CLAUDE_CODE_REMOTE` detected — true
  for local Claude Code sessions and Claude Code on the web alike) → `~/.claude/skills/`. Personal
  scope: nothing is written into the repo working tree, so there's nothing to `.gitignore`.
- **Cursor cloud agent** (`CURSOR_AGENT`, `HOSTNAME=cursor`, or the cloud plugin manifest detected)
  → `<workspace>/.cursor/skills/workflow/`, since Cursor cloud only scans project-local skills.
  Add that path to `.gitignore`. Cursor loads those skills when the agent process starts. Bake
  `docs/lab/bootstrap/cursor-cloud-setup.sh` into the environment image; there is no session hook
  that reloads skills on the first turn.
- **OpenCode** (explicit only) → symlinks under `~/.config/opencode/skills/<skill>` pointing at
  `<checkout>/skills/<skill>`. See [OpenCode (partial compatibility)](#opencode-partial-compatibility).

`WORKFLOW_INSTALL_MODE=opencode` or `./install.sh --opencode-skills` runs only the OpenCode symlink
path (idempotent). Optional: `WORKFLOW_OPENCODE_INCLUDE_LAB=1` to link lab skills too;
`WORKFLOW_OPENCODE_SKILLS` overrides the destination root (default `~/.config/opencode/skills`).

`./install.sh --print-route` prints the chosen route, destination, and `core_only` as JSON and does
not copy files. After install, `python3 tools/driver/check_skills.py` exits 0 when the six core
skill directories are present for the detected harness (no network).

### Auto-install on Claude Code on the web

Claude Code on the web provisions a fresh container per session, so nothing installed in a previous
session's `~/.claude/skills/` carries over. To get core skills into every session automatically,
add a `SessionStart` hook to the *consuming* repo (not this one) that runs the installer.
The script below is checked in at `docs/lab/bootstrap/session-start.sh` (same bytes). Merge
`docs/lab/bootstrap/claude-settings-fragment.json` into `.claude/settings.json`:

```sh
mkdir -p .claude/hooks
cat > .claude/hooks/session-start.sh <<'EOF'
#!/bin/bash
set -euo pipefail
[[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]] || exit 0
# Redirect the installer's own progress output to stderr — stdout is
# reserved for the control JSON below, which Claude Code parses.
curl -fsSL https://raw.githubusercontent.com/codyhamilton/workflow-plugin/master/install.sh | bash >&2
# Skill discovery runs before SessionStart hooks finish by default, so
# skills installed above wouldn't be visible until the *next* session —
# which never comes in a one-shot cloud container. reloadSkills forces a
# rescan after this (synchronous, non-async) hook completes.
echo '{"hookSpecificOutput": {"hookEventName": "SessionStart", "reloadSkills": true}}'
EOF
chmod +x .claude/hooks/session-start.sh
```

Register it in the consuming repo's `.claude/settings.json` (merge if the file already has hooks):

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh" } ] }
    ]
  }
}
```

The installer detects `CLAUDE_CODE_REMOTE`/`CLAUDECODE` itself and installs to `~/.claude/skills/`
non-interactively — the `[[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]]` guard above just keeps the hook
a no-op on local clones of the consuming repo, where you'd rather run `install.sh` yourself.

## Which install is live?

There are two independent install paths, and **they update by different commands and drift apart
silently**. A skills plugin gives an agent no runtime signal that the prompt it is executing is not
the prompt in this repo, so before concluding "the skill is doing X", check the copy that is
actually loaded.

| | Path A — direct install | Path B — marketplace plugin |
|---|---|---|
| Installed by | `./install.sh` | `/plugin install workflow@workflow-plugin` |
| Lives at | `~/.claude/skills/<skill>/` (or `.cursor/skills/workflow/`, `~/.cursor/plugins/local/workflow`) | `~/.claude/plugins/cache/workflow-plugin/<plugin>/<version>/` |
| Source of truth | a copy made at install time | a git clone at `~/.claude/plugins/marketplaces/workflow-plugin`, pinned by `gitCommitSha` in `~/.claude/plugins/installed_plugins.json` |
| Skills appear as | `design`, `execute`, … | `workflow:design`, `workflow:execute`, … |
| Updates when | you re-run `./install.sh` | you run `/plugin update workflow@workflow-plugin` |

Neither path notices that the other exists, and neither notices that this repo moved on.

**To tell which is live**, look at how the skills are named in the harness's skill list: a
`workflow:`/`workflow-lab:` prefix means Path B, bare names mean Path A. Then read the file that
name resolves to — not this repo:

```sh
# Path B: what is pinned, and what the loaded copy actually says
grep -A6 '"workflow@workflow-plugin"' ~/.claude/plugins/installed_plugins.json
grep -rn "\[NEW\]" ~/.claude/plugins/cache/workflow-plugin/     # should return nothing

# Path A
ls ~/.claude/skills/
```

**To update Path B**, `/plugin update workflow@workflow-plugin` (and `workflow-lab@workflow-plugin`).
That refetches the marketplace clone, re-pins `gitCommitSha`, and repopulates the version-numbered
cache directory. Editing the cache by hand does not re-pin it and will be overwritten.

If you use both paths, pick one as canonical for local work and remove the other — a stale copy that
still resolves is worse than no copy at all.

## OpenCode (partial compatibility)

OpenCode can run the same **workflow skills** as Claude Code and Cursor, but the harness differs:
there is **no** OpenCode driver provider in `tools/driver/` yet, **no** Claude `SessionStart` hook,
and **no** live `PostToolBatch` signal path (that integration is Claude Code today; OpenCode only
has per-tool execute hooks unless you add a custom plugin). Unattended multi-phase loops remain
**Claude Code**, **Cursor cloud + driver**, or a human/coordinator dispatching `execute` per phase.

**Skills (preferred):** symlink each skill directory from your checkout into OpenCode's config tree so
edits in the repo are picked up without copying:

```sh
# From a clone of this repo (or set WORKFLOW_INSTALL_MODE=opencode anywhere install.sh is available)
./install.sh --opencode-skills
# Equivalent:
WORKFLOW_INSTALL_MODE=opencode ./install.sh
```

That creates `~/.config/opencode/skills/<name>` → `<checkout>/skills/<name>` (for example
`~/workspace/workflow-plugin/skills/design`). **Symlinks only** — the installer does not force
`~/.claude/skills` for OpenCode. OpenCode may also read Claude's personal skills directory on some
setups; the **preferred** layout for OpenCode is `~/.config/opencode/skills/` via symlink-to-checkout.

**Names and personas (do not conflate harnesses):**

| Topic | OpenCode | This plugin |
|-------|----------|-------------|
| Multi-phase delegation persona | Keep harness name **`orchestrate`** (delegation/orchestration) | Not a skill rename — workflow keeps skill names below |
| Phase runner (one phase per fresh context) | Map to skill **`execute`** | `execute` closes a phase with `Workflow-Phase:` and stops; there is no separate OpenCode-primary "phase-runner" skill |
| Planning | Built-in OpenCode command **`plan`** | Workflow skill **`design`** — different artifact (`DESIGN.md`, phases, outcomes). Leave OpenCode's built-in `plan` alone; use `design` for this workflow |
| Agent definitions | OpenCode agent personas / config | ≠ Claude agent markdown files, ≠ Cursor plugin agents under `.cursor-plugin/` |

**Assertions and cheap signals:** Jev-style soft signals are **advisory** where wired (Claude/Cursor).
**`assert_phase --deterministic`** remains the hard kill line for phase boundaries. On OpenCode, treat
`docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/run_proofs.sh` as the validated
stand-in unless you add a custom batching plugin.

**DeepSeek Flash (review gate):** When Flash agents **execute briefs / phase units** (build path),
follow [`docs/lab/GUIDANCE-flash-review-gate.md`](docs/lab/GUIDANCE-flash-review-gate.md):
Flash in the build path **mandates** a phase review gate — **no auto close-out**. Every Flash unit pass
is followed by **mandatory Sonnet 5.5** review of that work; then **hold** for **Claude Code or Grok**
to review the phase and sign off (`Workflow-Phase:`). Flash must not close the phase.
Pattern: Flash draft → Sonnet 5.5 review → Claude or Grok validation/sign-off.

Lab skills: interactive install can symlink `workflow-lab` too, or
`WORKFLOW_OPENCODE_INCLUDE_LAB=1 WORKFLOW_INSTALL_MODE=opencode ./install.sh`.

## Manual installation

### Claude Code

Copy core skills directly:

```sh
cp -r skills/* ~/.claude/skills/
```

Add the lab skills too, for local/interactive use:

```sh
cp -r plugins/workflow-lab/skills/* ~/.claude/skills/
```

### OpenCode

Prefer symlinks (see [OpenCode (partial compatibility)](#opencode-partial-compatibility)):

```sh
mkdir -p ~/.config/opencode/skills
for d in skills/*/; do
  name="$(basename "$d")"
  ln -sfn "$(pwd)/$d" "$HOME/.config/opencode/skills/$name"
done
```

Or run `./install.sh --opencode-skills` from the checkout.

Skills are available immediately. For marketplace-style install (so colleagues can
`/plugin install workflow@workflow-plugin`), register this repo in
`~/.claude/plugins/known_marketplaces.json`:

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

Then install either or both plugins:

```
/plugin install workflow@workflow-plugin
/plugin install workflow-lab@workflow-plugin
```

Skills become available as `workflow:design`, `workflow:execute`, `workflow-lab:iterate`, etc.

### Cursor

Clone the repo into Cursor's local plugins directory for the core plugin, then restart Cursor:

```sh
git clone git@github.com:codyhamilton/workflow-plugin.git ~/.cursor/plugins/local/workflow
```

For the lab plugin too, copy its subtree into a second local plugin directory:

```sh
cp -rL ~/.cursor/plugins/local/workflow/plugins/workflow-lab ~/.cursor/plugins/local/workflow-lab
```

Or run `./install.sh` and accept the Cursor prompts (core, then optionally lab).

## Structure

```
workflow-plugin/                    (repo root — the `workflow` core plugin)
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json            (lists both plugins)
├── .cursor-plugin/plugin.json
├── skills/                         (core plugin's skills)
│   ├── design/
│   ├── refine/
│   ├── execute/
│   ├── comprehensive-review/
│   ├── close-out/
│   └── post-build/                 (briefs/ for its workers)
├── docs/
│   ├── lab/                        (Optimiser research/ops: goals, findings, proposals)
│   └── automation/                 (operator guides for external automation triggers)
└── plugins/workflow-lab/           (lab plugin, its own manifests + skills/)
    ├── .claude-plugin/plugin.json
    ├── .cursor-plugin/plugin.json
    └── skills/
        ├── setup/
        ├── iterate/
        ├── transcript-parser/
        └── workflow-tuning/
```
