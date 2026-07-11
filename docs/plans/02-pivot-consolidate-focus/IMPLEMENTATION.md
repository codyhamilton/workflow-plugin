# Implementation: Pivot, Consolidate, Focus

## Session

- Tool: Claude Code (remote/cloud session)
- Session: https://claude.ai/code/session_01SL8xCbPvWmo5qoxNEnk6SD
- Started: 2026-07-11T18:20:00Z

Written progressively during execution, per the model this plan defines.

## Execution shape

- Orchestrator (this session) authored dispatch briefs into `briefs/` and routed them verbatim to implementation workers — dogfooding the briefs invariant.
- Phases 1–3 dispatched in parallel (disjoint file ownership: `skills/plan/`, `skills/execute/`, `skills/comprehensive-review/`); Phase 4 dispatched after 1–3 complete (manifests, iterate, setup, transcript-parser, stable docs).
- Deviation from plan wording: all four phases land on this branch/PR rather than one PR per phase — user directed a single execution pass in this session.
- Deviation from the execute skill: the mandatory comprehensive-review pass is **deliberately skipped** — the user (the invoker) directed "complete execution, don't move on to review." Review posture is the invoker's call under the new model.

## Progress log

- [x] Briefs authored and committed (`briefs/phase-1..4`)
- [x] Phase 1: plan skill revision
- [x] Phase 2: execute skill revision
- [x] Phase 3: comprehensive-review revision
- [x] Phase 4: partition and re-composition

Execution complete. Comprehensive review deliberately not run — the user (invoker) declared execution-only for this session; the downstream pipeline stage owns the deep review of this PR.

## What was built

### Phase 3 — comprehensive-review (worker report, condensed)

SKILL.md revised (71 → 114 lines): explicit Inputs section (marker-located plan folder, diff, verbatim intent + assumption ledger; local-run variant); output placement (REVIEW.md in the plan folder keyed to acceptance criteria; structural findings become self-contained `briefs/remediation-<NN>.md`, trivial findings stay inline); new "Intent and assumptions" lens ordered second; plan-sufficiency judgment with the one-way workflow-tuning flow stated; RECOVERED-INTENT.md fallback for artifact-less PRs. Right-sizing rules, lens structure, and one-external-loop posture retained. No reference.md created — the worker judged the original had no persuading-why prose to relocate (brief permitted this). No contradictions with DESIGN.md found; QA.md correctly left to the pipeline's QA stage.

### Phase 2 — execute (worker report, condensed)

SKILL.md revised; new `skills/execute/reference.md`. Removed: ROADMAP sync, `[NEW]-` checks, parent-renaming ceremony, STATUS.md (progressive IMPLEMENTATION.md is the recovery mechanism), the mandatory-subagent rule, and the per-harness model tables + session-ID formulas (→ reference.md, with consumer note). Added: Brief-Based Dispatch section (invariant stated once + mechanics + ceremony guard), delegation-as-judgment, Review Posture section (terminal vs pipeline, declared not inferred), One-Shot Composition note (cold read is load-bearing), progressive IMPLEMENTATION.md with run identity, PR completion with the `Workflow-Plan:` marker. Sizing ladder and lean-orchestrator rules carried over near-verbatim. Grep for dead conventions returns only the permitted explanatory line in reference.md.

### Phase 1 — plan (worker report, condensed)

SKILL.md restructured from the numbered-with-insertions checklist into six named phases (Capture → Ground → Resolve → Write → Challenge → Checkpoint; Resolve and Checkpoint branch by posture). Backlog taxonomy fully removed. Added: Postures section (interactive default / headless declared, never inferred), plan-folder convention section (slug unique, `NN` best-effort, folder-on-branch = being/was built, multi-PR programs as design-intent doc + runs, `Workflow-Plan:` marker), QA-drivable acceptance criteria. New `skills/plan/reference.md` holds the relocated persuading-why with a consumer note. Templates: PLAN.md gained the Assumption Ledger and split user-facing/non-user-facing criteria; PROVENANCE.md marked interactive-posture-only. Question discipline, pivot detection, stable-docs grounding, and the anti-mechanical-template rule carried forward. No contradictions with DESIGN.md reported.

### Phase 4 — partition and re-composition (worker report, condensed)

Partition layout: core skills stay at repo root `skills/` (already the marketplace's `source: "./"`); lab skills moved to `plugins/workflow-lab/skills/` with their own `.claude-plugin` and `.cursor-plugin` manifests; `marketplace.json` lists both plugins; `workflow` bumped to 2.0.0 (breaking), `workflow-lab` at 1.0.0. iterate: `[NEW]-<goal>` convention replaced with plain `<NN>-<slug>` (keeping `iteration-NN/`), every plan/execute dispatch now declares posture (headless plans; terminal candidate builds; pipeline consolidation/refine builds with harden as the downstream review), Reasoning section moved verbatim to `reference.md` with one-line orienting hooks kept on the two invariants that leaned on it. setup: no longer creates `docs/ROADMAP.md`; legacy ROADMAPs are salvage material; Non-Goals folded into the ARCHITECTURE template. transcript-parser: both Python snippets extracted to `scripts/parse_session.py`; fixed a pre-existing `OPENCODE` → `OPENCODE_RUN_ID` bug. workflow-tuning: gained the pipeline-outcomes harvest (merged-PR REVIEW.md/QA.md/remediation briefs as eval corpus); stale ROADMAP rule fixed; old parent-program lesson kept with a superseded-mechanism caveat. `install.sh` asks separately for core vs lab; invalid trailing comma in `.cursor-plugin/plugin.json` fixed. `docs/OVERVIEW.md`/`docs/ARCHITECTURE.md` rewritten for the seven-skill/two-plugin model — ARCHITECTURE is now the durable home of the seam/taxonomy/postures contract (DESIGN.md becomes historical after merge). README: skills table split by plugin, breaking-change callout, updated installs; hypotheses/variants sections untouched.

## Tradeoffs and deviations

- **Pipeline posture and REVIEW.md** (Phase 2 worker judgment, endorsed by orchestrator): under pipeline posture execute does not write REVIEW.md — DESIGN.md assigns REVIEW.md ownership to the pipeline stage; execute's pre-flight self-verification results land in IMPLEMENTATION.md instead. The Phase 2 brief hadn't specified where pre-flight results land; this resolution follows the seam ownership contract.
- **Posture on all iterate dispatches** (Phase 4 worker judgment, endorsed by orchestrator): DESIGN.md only explicitly requires iterate's plan dispatches to declare posture; the worker extended declared-not-inferred to iterate's execute dispatches too (terminal for candidates, pipeline for consolidation/refine where harden is the downstream review). Consistent application of the same invariant; terminal was already the de facto default.
- **Durable contract home** (Phase 4 worker judgment, endorsed by orchestrator): the seam/taxonomy/postures contract now lives durably in `docs/ARCHITECTURE.md`, since plan-scoped DESIGN.md becomes historical provenance after merge; workflow-tuning's citation points there.
- **Single PR, phases as commits**: the plan's "each phase produces its own PR" was overridden by the user's direction to complete execution in this session; phases landed as sequential commits on this branch (phase 3 → 2 → 1 → 4, in completion order).
