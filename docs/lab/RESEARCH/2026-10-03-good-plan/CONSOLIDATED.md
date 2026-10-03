# Consolidated candidates (stage 4 draft, before adversarial review and validation)

Seven independent sources (S): requirements (req), design docs (dd), agent specs (as), plan failure (pf), blind Codex (cx), data induction (data), Cody's observation (U1). Convergence among LLM-written sources is weak evidence: shared training priors, not independent confirmation. Only validation against outcomes counts. "Reg" = relation to registry 1.1.

| # | Cluster | Subject | Check | Sources | Reg 1.1 | Note |
|---|---|---|---|---|---|---|
| K1 | Done evidence is a runnable command/observable with expected result | brief | det | req dd as pf cx data (6) | `b.done_runnable` | data: browser/staging checks inside Done evidence, 4 troubled vs 0 clean; deferral needs a named owner (K18) |
| K2 | Done check fails before, passes after | brief | jev | as pf data | `b.fail_first` (weak, 0.52-0.61) | data: present in all clean briefs, no separation |
| K3 | Phase outcome observable, and one is end-to-end across the units | design | jev | req dd as pf cx (5) | `d.outcomes_checkable` (saturated) | split into levels: activity / observable per unit / end-to-end across units |
| K4 | Boundary contracts as shapes, with producer, consumer, failure behaviour | design | jev | cx dd as pf req data (6) | `d.contracts_citable` | add failure/absent behaviour (STPA prompts) |
| K5 | Intent traced both ways (each ask to a phase, each phase to an ask) | design | jev | req dd as pf cx (5) | `d.problem_covered` (saturated) | two-way trace is harder than coverage |
| K6 | Assumptions/unknowns carry a verification status or owner; none dangling | both | jev+det | req dd as pf cx data U1 (7) | `d.risks_open_marked` | det part: no bare TBD/"either X or Y" |
| K6a | Each threshold/bar names its evidence or is an unproven assumption to test first | both | jev | U1 data pf | none | brief-level data: no separation (3/9 vs 6/15); design-level post-mortem (plan 03): 3 of 4 worker-picked gate proxies failed |
| K7 | Non-goals real, adjacent items named | both | jev | req dd pf as cx (5) | `d.nongoals_real` (saturated 0.99), `b.keep_untouched` (weak) | demote to hygiene |
| K8 | Owned paths explicit; siblings disjoint; changes map to owned paths; callers/importers handled | brief | det | dd as req data cx | `b.owned_paths_resolve` | new: sibling disjointness, closure; data: closure 6 vs 1 but circular |
| K9 | Reading named, specific, purposeful (no discovery needed) | brief | det+jev | req dd as pf cx (5) | `b.reading_specific`, `b.discovery_free` (validated) | keep |
| K10 | References resolve; symbols not line numbers | brief | det | req dd data | partly | data: >=5 line refs 5 vs 1 |
| K11 | Dependencies explicit and acyclic; no unproduced input | design | det | req pf cx | none | cheap |
| K12 | Budget and stop condition | brief | det | req as cx pf | `b.budget_complete` | data: no separation on numeric budgets |
| K13 | Single bounded unit / singular assertions | brief | jev | req cx | `b.single_session` | |
| K14 | Vague-term density low | both | det | req | none | data: hedge words did not separate |
| K15 | Alternatives rejected for a stated constraint; decision consequences | design | jev | dd | `d.alternatives_recorded` | |
| K16 | Failure modes with detection/mitigation | design | jev | dd pf cx | `d.risks_open_marked` partly | |
| K17 | Upstream context carried in the brief, no repo boilerplate | brief | jev | as | none | |
| K18 | Proof reaches a real boundary, not mocks only; deferred checks have an owner | brief | jev | data | none | data: 4 vs 1 weak |
| K19 | Pinned values from upstream work flagged for re-derivation | brief | jev | data | none | n=2 cases |
| K20 | Verification not left to worker judgement | both | det | as | none | |
| K21 | Consumer and handed-back deliverable named | brief | det | cx as | `b.consumer_and_owned` | |
| K22 | Intent verbatim, separate from interpretation | design | det | req dd pf | `d.intent_verbatim` | |
| K23 | Acceptance includes a negative/edge case | both | jev | req pf | none | |

## Read of the field
- Registry 1.1 already covers most clusters. The research mainly confirms its direction and gives reasons.
- Genuinely new: K3 hard levels (end-to-end), K5 two-way trace, K6a evidence basis, K8 disjointness/closure, K10 line refs, K11 acyclic, K14 vague terms, K18, K19, K23, K17.
- Saturated in the real ledger (little information): `d.ledger_complete`, `d.nongoals_real`, `d.outcomes_checkable`, `d.problem_covered`. Harder anchored levels (K3, K5) may restore variance.
- Weak evidence overall. No source ties any criterion to measured rework for LLM-agent plans; the data proxies are noisy (n=15 per group). Validation, not literature, decides.
