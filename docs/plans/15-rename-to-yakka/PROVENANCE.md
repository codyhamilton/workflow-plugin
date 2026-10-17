# Provenance: Rename to yakka

The design this conversation produced was folded into `docs/plans/13-monorepo-restructure/`. This file is the record of the conversation, not a second plan.

Interactive posture only. Headless runs carry intent, the assumption ledger, and decisions in `DESIGN.md` alone.

## Session

- Session: Initial design (October 17, 2026)
- Timestamp: 2026-10-16T15:10:13Z
- CWD: /home/codyh/workspace/workflow-plugin

## Initial Request (verbatim)

> Help come up with a better name for this app. We've got `workflow` which is terribly generic. `miniflow` was another thought. It's all about the plan/design/refine/execute SDLC workflow

## Design Conversation

### Turn 1

**Agent asked:** Naming candidates (keel, plumb, foreman, …), then regional synonyms for foreman.

**User responded:** "foreman is nice. Synonyms or slang? scottish or irish or aussie?" then "gaffer and yakka are fun, and gaffer has wide usage for its 'do all tape'".

**Agent decisions:**

- Shortlist narrowed to `gaffer` and `yakka`; namespace checked on GitHub, npm, PyPI, crates.io. `gaffer` is crowded on GitHub (gchq/Gaffer, GafferHQ); `yakka` is near-empty; bare npm/PyPI names for both are taken by inactive packages.

### Turn 2

**Agent asked:** (proposed) `yakka` for the product, `gaffer` for the binary/service.

**User responded:** "yakka feels more like a name, while gaffer is a proper title. in a way gaffer is more appropriate for the service (an entity) rather than a product name" — then "It makes more sense to keep yakka for both".

**Agent decisions:**

- One name, `yakka`, for every surface: plugin, skill prefix, binary, MCP server, Go module, env vars, trailers, directories.

### Turn 3

**Agent asked:** Four scope questions: when to sequence the rename relative to plans 13 and 14; whether to rename the GitHub repo and marketplace; how much backward compatibility to keep for env vars and on-disk state; whether to rename the commit trailers and the report fence.

**User responded:** After 13 and 14. Rename the repo and marketplace to yakka. Hard break for env vars and on-disk state. Rename the trailers and fence, but keep reading both forms.

**Agent decisions:**

- Surfaces are named on the post-plan-13 layout (`packages/workflow`, `packages/hooklog`, no lab plugin).
- `WORKFLOW_*` becomes `YAKKA_*` with no fallback. Default paths move, existing data is not migrated, and the CHANGELOG carries the manual steps.
- Writers emit `Yakka-Plan:`, `Yakka-Phase:` and a ```` ```yakka-report ```` fence. Readers accept both forms permanently, because git history and old transcripts cannot change.
- The GitHub repo rename is a maintainer action. The plan changes every in-repo reference so it lines up with that rename.

### Turn 4 (checkpoint)

**Agent asked:** For sign-off on the design. Flagged three things: keeping the analytics `localStorage` keys as `workflow-analytics-*`, superseding plan 13's bootstrap-URL contract with no stub, and the maintainer actions outside the repo.

**User responded:** "analytics there's no users with saved views etc, can safely rename. design is ok"

**Agent decisions:**

- The `localStorage` keys are renamed to `yakka-analytics-*`, and the scan exception for them is removed.
- The design is signed off with that change.

## Agent Decisions

- **Legacy quality service out of scope**: `tools/quality`, its systemd unit, its `WORKFLOW_QUALITY_*` variables, its data directory and its `workflow_*` schema columns keep their names. Rationale: plan 13 keeps it only as a lab legacy until the maintainer stops it, and renaming would orphan the running service's data for no product benefit.
- **History is not rewritten**: closed plan records, `docs/lab/`, `docs/analysis/`, earlier CHANGELOG entries and `evals/results/` keep `workflow` names. Rationale: they record what was true when they were written.
- **Plan 13's bootstrap-URL contract superseded**: there is no forwarding stub, consistent with the hard-break answer.
- **The word "workflow" stays where it is the noun**: for example "the design → execute workflow". Only identifiers and product names change.
