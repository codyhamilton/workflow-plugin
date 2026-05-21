# Implementation: Workflow Improvements Program

## What Was Built

Three improvements to the workflow-plugin, implemented in sequence:

### Child 01 — Provenance Capture

**Files:** `skills/planning/templates/PROVENANCE.md` (new), `skills/planning/SKILL.md` (modified), `skills/planning/templates/PLAN.md` (modified)

Progressive provenance writing added to the planning skill. Three write points: (1) create PROVENANCE.md immediately after capturing the verbatim request, before reading stable docs; (2) append each Q&A turn on receipt; (3) append agent decisions before finalizing. Records intent in user's words — strips tone/filler, preserves phrasing only when it carries meaning a paraphrase would lose.

### Child 02 — Setup Skill

**Files:** `skills/setup/SKILL.md` (new), `skills/planning/SKILL.md` (modified)

New `workflow:setup` skill with six phases: reconnaissance, permission gate, consolidation (partial docs merged not duplicated), guided three-round conversation (broad purpose → components → current state/constraints), write docs (`docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`), planning hook. Planning skill step 2 now suggests setup when stable docs are absent.

**Scope extension:** OVERVIEW.md added to setup's output — required because planning reads it, and the original plan omitted it, which would have created a broken planning-to-setup loop.

### Child 03 — Eval System

**Files:** `evals/README.md` (new), `evals/scenarios/.gitkeep`, `evals/results/.gitkeep`, `skills/workflow-tuning/SKILL.md` (modified), `skills/workflow-tuning/reference.md` (modified)

End-to-end eval pattern: full plan+execute cycle on a fixture scenario (real repo at tagged commit), compared against baseline and reference on two lenses — cost (agents/model sizes/tool turns/context/wall time) and quality (narrative, loose — "significant delta?" and "same ballpark?"). Ships with empty fixture corpus and documented pattern. Workflow-tuning skill extended with Eval Capability section.

## Program Sequencing

Implemented in order: 01 → 02 → 03. Each child built on the previous: 01 was foundational (provenance), 02 benefited from provenance for its own planning record, 03 depended on both for faithful fixtures and stable doc examples.

## Dogfooding

This program was planned and executed using the workflow-plugin's own planning, execution, and review loop. The `docs/plans/[NEW]-workflow-improvements/` folder and its PROVENANCE.md are real examples of the correct output shape — usable as eval fixtures.
