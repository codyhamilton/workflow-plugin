---
brief_id: 230
design_id: 209
---

# Brief: 6-01 — Skills and templates on the advisory surface

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its output closes phase 6; the
orchestrator runs the phase 6 grep outcome against it. Every later run of the design, refine and
execute skills follows what this unit writes.
Owned paths: `skills/design/SKILL.md`, `skills/design/templates/DESIGN.md`,
`skills/refine/SKILL.md`, `skills/refine/templates/brief.md`, `skills/execute/SKILL.md`, and
`skills/comprehensive-review/SKILL.md`, `skills/close-out/SKILL.md`, `skills/post-build/SKILL.md`
only if a grep below finds something in them; new
`docs/plans/09-workflow-binary/reports/6-01-skills-templates.md`. Touch nothing else: not
`plugins/` (the lab keeps its own vocabulary and is already clean), not `docs/lab/`, not any
existing plan's briefs or designs (their frontmatter is history), not `tools/`.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: phase 4 (the `artifact_feedback` tool exists). Runs alongside: 5-05 (disjoint paths;
stage only your own).
Budget: 10 files to read, about 150 lines changed, 35 tool turns. Past the budget, stop: write a
handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md` (done, not
done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — `### Phase 6` (the outcome, verbatim below).
2. `docs/design/04-advisory-surface.md` — the tool table (lines 20-26), `artifact_feedback`
   (lines 31-55, its states: queued, rejected, delivered, delivered at an older version, unknown,
   service unreachable, no config), and What changes in the skills (lines 79-91). Binding.
3. `docs/design/01-event-model-and-ingest.md` — Execution report (lines 81-118). Binding.
4. `tools/quality/checks/execution-report.json` — the report rubric wording, defined once.
5. The five owned skill files and two templates (each under 80 lines).

Read ranges and grep; do not re-read a file already in context.

## Goal

The skills stop telling agents to post or log anything. Writing the file is the submission; the
agent then asks `artifact_feedback` and acts on what it says. Each execute worker writes an
execution report beside its brief.

## Contract

Cited, binding (DESIGN.md Phase 6 outcome): "a grep of `skills/` (including templates) and
`plugins/` for `post_design`, `post_brief`, `patch_design`, `patch_brief`, `start_execution`,
`patch_execution`, `complete_execution`, `design_id`, `brief_id` and `[exec` returns nothing; the
execute skill requires each worker to write `docs/plans/<plan>/reports/<brief-name>.md` and names
`artifact_feedback`; `Workflow-Phase:` trailers remain."

Design 4, What changes in the skills: every bullet applies. Decisions made at refine (settled):

- **Ratings rule → feedback rule.** In `design` and `refine`, the "Ratings are obtained" bullet
  becomes: after writing the file, call `artifact_feedback(path)`; a rejection is fixed before
  moving on (the reason names a pattern and line, never the secret); a check flagged out of the
  tenant's norm is addressed or named; `queued`, `unreachable` or `no config` is reported in one
  line and the work continues. Never skipped silently. Ratings stay comparative: the outlier is
  the signal.
- **Hook backstop bullets** (`design` line 19, `refine` line 16) are deleted: capture is the hooks,
  and there is nothing to adopt.
- **Frontmatter.** Templates drop `design_id`/`brief_id`. If that leaves the frontmatter empty,
  remove the `---` block. The "Frontmatter carries identity only" rules become "No frontmatter
  fields for identity, status, scores or progress; the artifact key is the repo and path."
- **Execute.** The `start_execution`/`patch_execution`/`complete_execution` bullet and the
  `[exec <id>]` title bullet are removed. Add: each worker writes
  `docs/plans/<plan>/reports/<brief-name>.md` before its commit and includes it in the commit; its
  content follows design 1 (what was done against the brief verifiably, departures and why,
  unfinished work, known problems, nothing derivable), and the wording points to
  `tools/quality/checks/execution-report.json` as the rubric rather than restating it. The runner
  reads reports and does not rewrite them; a runner note is a separate file. Before closing a phase
  the runner calls `artifact_feedback` on each report and the phase's briefs and records flagged
  checks in `IMPLEMENTATION.md`. Commit titles are plain summaries. `Workflow-Phase:` trailer rules
  stay word for word.
- **Brief template.** If it has a commit-title or execution-id line, it becomes a plain title plus
  the report requirement.
- Any other mention of the `workflow-quality` service, `8765`, or posting in the owned files is
  rewritten to the advisory surface or removed.

## Done evidence

Identify the failing check first and report its output before and after:

- `grep -rnE 'post_design|post_brief|patch_design|patch_brief|start_execution|patch_execution|complete_execution|design_id|brief_id|\[exec' skills/ plugins/`
  → before: the 11 hits in 5 files; after: no output (exit 1).
- `grep -n 'artifact_feedback' skills/execute/SKILL.md` and
  `grep -n 'reports/<brief-name>.md' skills/execute/SKILL.md` → each at least one line.
- `grep -rn 'Workflow-Phase' skills/ | wc -l` → the same count as before (quote both).
- `grep -rnE 'workflow-quality|8765|QUALITY-SERVICE' skills/` → no output.
- Every relative link in the changed files resolves (check with a short loop over `](` targets).

Commit: title `[exec <execution_id>] Phase 6: skills and templates on the advisory surface` (the
orchestrator supplies the id; this run still logs through the legacy service, which this unit
retires for later runs), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/6-01-skills-templates.md` per design 1 and include it.

## Report back

Under 1,000 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` |
`over budget`. Then what changed, the grep output before and after, any deviation and why, and any
contradiction between this brief and the contracts it cites. Never resolve a contradiction
silently. Do not spawn agents.
