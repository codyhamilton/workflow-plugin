# Review: 03 — Eval System

## Outcome

Implementation reviewed against all six acceptance criteria. All criteria substantively met. Two medium and three low findings; all fixed before commit.

## Findings by Severity

### Medium (both fixed)

**Tool-use-turns inconsistency** — README cost-comparison schema said "total across all agents"; SKILL.md step 4 said "per agent." Two evaluators following different docs would record incomparable numbers. Fixed by documenting both in the schema: per-agent breakdown for diagnosis, total as a derived summary line in Delta.

**Baseline immutability not enforced by instruction** — SKILL.md step 6 said "if no baseline exists yet, populate" but gave no explicit guard against overwriting. Fixed by adding: "If `baseline/` is non-empty, do not overwrite — the baseline is fixed once set."

### Low (all fixed)

**Forward reference for baseline/ contents** — The `baseline/` description referred forward to the Results section ("contains the same artifacts as a `candidate/` folder") without enumerating them inline. Fixed by listing the artifacts directly (PLAN.md, IMPLEMENTATION.md, other created files).

**Context estimate fallback unspecified** — "tokens, if available" gave no guidance on what to write when unavailable. Fixed by specifying: write "not available (source: <reason>)".

**Timestamp format unspecified** — `results/<scenario>/<timestamp>/` used a placeholder with no format. Fixed by specifying `YYYYMMDD-HHMMSS` and adding an example.

**Variant testing misdirection** — SKILL.md said "cost and quality comparisons can be placed side by side in `quality-comparison.md`." Cost data belongs in `cost-comparison.md`. Fixed by directing each candidate to its own timestamped result folder.

## Residual Risks

- **Baseline variance.** A single first run anchors all future comparisons. An anomalously expensive or cheap run produces a misleading baseline. Acceptable for v1.
- **Reference freshness.** No guidance on when a reference should be refreshed. An old reference on an evolved repo may produce misleading quality comparisons. The Eval Patterns section in reference.md can absorb lessons about this as they are learned.
- **Human judgment required.** The quality lens has no automation. Consistent quality comparisons depend on evaluator discipline. The loose framing ("significant delta?" and "same ballpark?") reduces but does not eliminate evaluator variance.

## Final Assessment

All six acceptance criteria met. The eval pattern is documented clearly enough to produce consistent, comparable results across evaluators — provided the medium fixes (tool turns alignment, baseline immutability) are in place, which they are. Ready.
