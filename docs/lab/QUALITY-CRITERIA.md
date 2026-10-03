# Quality criteria for briefs and designs

Status: theorised unless a row says otherwise. Source of truth for the criteria is `tools/quality/criteria.json` (version `1`); each criterion there carries its `basis` and any observed `evidence`.

## Purpose

Every brief and DESIGN.md is scored when written, logged to a SQLite ledger, and tagged as part of the workflow. The score is informational and deterministic in shape (a fixed criteria set, 0-1, higher is better). It is returned to the calling agent as a relative rating (percentile against the latest score of every other logged artifact of the same kind). The use is comparative: trends over time, and which projects and kinds of work score better or worse relative to each other. No absolute pass mark is claimed.

## Design rules for the criteria

1. **Criteria-matching, not holistic judgement.** Stage A showed Jev is strong at matching concrete, text-checkable criteria ("does the brief cite a contract by name?") and weak at "is this a good brief?". Every Jev criterion therefore has anchored levels describing concrete text content.
2. **Deterministic first.** Anything checkable without a model (sections present, owned paths resolve, budget parseable) is computed deterministically. Jev adds only what needs reading.
3. **Stable.** Test-retest Spearman rho >= 0.96 across the Jev criteria in the Stage A repeat run.
4. **Grounded.** Each criterion names its public or workflow-design basis: Anthropic's multi-agent research write-up and effective-agents guidance (explicit objectives and boundaries, scarce context), the OpenAI review of SWE-bench Verified (underspecified tasks, tests not matching the spec), Cognition's share-context point, Parnas information hiding, ADR / design-doc practice (alternatives, non-goals), acceptance criteria / Definition of Done, and the plugin's own refine and design skills.

## Acceptance rule for promoting a criterion from "theorised" to "validated"

- test-retest rho >= 0.9;
- AUC against a later outcome (rework, defects, process trouble) with 90% CI above 0.5 on at least two projects;
- adds signal beyond the size / new-files zero-call counters.

Criteria that fail stay logged (all data is kept) but are marked as not predictive.

## Observed so far (Stage A, one project each, descriptive)

| Criterion | Result |
|---|---|
| `b.discovery_free` | AUC 0.84 for process trouble (0.89 with the new-files counter); best single criterion. Needs replication on a second project. |
| `b.contract_cited` | AUC 0.73 alone, weak. |
| `b.fail_first`, `b.keep_untouched`, `b.changes_concrete` | 0.52-0.61, no usable signal yet. |
| `b.owned_paths_resolve` | owned_new_files count AUC 0.76 for process trouble. |
| `d.outcomes_checkable` | Case 4: the phase-level analogues (`rework`, `failed_gate_open`) predict phase outcome; record-quality criteria do not. This upstream design criterion is untested. |
| Template-compliance criteria (`*.sections`, `*_complete`) | Mostly do not predict trouble; kept as hygiene, expect them to saturate. |

## Known confounds

- **Format eras.** Older DESIGN.md files lack `### Domain:` / `### Phase N` headings, so `d.domains_complete` and `d.phases_complete` read 0 for them. Compare within a format era, or via `facts` recorded with each row.
- **Size.** Longer briefs mechanically satisfy more criteria; check any finding against size-stratified results.
- **Project mix.** A project's score reflects its work as much as its authors; hence relative, not absolute, reading.

## Outcome linking

The `links` table records later events against earlier artifacts: `rework`, `missing_scope`, `defect`, `supersedes` (manual: `quality.py link` or the `link_artifacts` MCP tool) and `derived_from`, `overlaps_prior` (automatic). These are the outcome labels that let criteria be validated against the rule above.
