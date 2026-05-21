# Review: 01 — Provenance Capture

## Outcome

Implementation reviewed against all seven acceptance criteria. One high-severity defect found and fixed. Three medium and two low issues found and fixed. One low issue (stray DESIGN.md template) deferred — out of scope for this child plan.

## Findings by Severity

### High

**"verbatim" label contradicts stripping instruction** (fixed)
Template had `**User responded (verbatim):**` but the skill rules say to strip tone and filler. An agent would follow the label and copy everything said. Fixed by removing "verbatim" and adding `(substance in their words — strip tone and filler)` note.

### Medium (all fixed)

**Step 1 vs. step 1a ordering** — Step 1 said "capture the user's request verbatim in the plan" implying PLAN.md was written to disk at step 1, before the directory existed. Step 1a then created the directory. Clarified that step 1 means capture in context (not write to disk), and that the first disk write happens at step 1a. PLAN.md is written at step 11.

**Two-layer agent decisions unexplained** — Template had per-turn `Agent decisions:` inside `### Turn N` AND a final `## Agent Decisions` section with no explanation of the relationship. An agent would duplicate content or drop one layer. Added explanation: per-turn captures immediate choices; final section captures cross-cutting decisions not obvious from PLAN.md.

**User-volunteered turns** — Template's `Agent asked:` field implied all turns were agent-initiated. Real planning conversations include user-volunteered directions without a preceding question. Fixed by marking `Agent asked` as optional and noting it can be replaced with `User clarified` or omitted.

### Low (all fixed)

**"If in doubt, omit" not in rules** — This principle was in the child PLAN.md scope section but not in SKILL.md where executing agents read it. Added to the provenance rule.

**Empty Planning Conversation** — No guidance on what to do when no Q&A turns occurred. Added "If no Q&A turns occurred, write 'None.'" note to the template.

### Out of scope (deferred)

**Stray `templates/DESIGN.md`** — File exists in the templates directory but is not referenced in SKILL.md. Not a defect in provenance capture; deferred to a future tidy-up or a new plan.

## Fixes Applied

All in-scope findings were fixed before commit. See IMPLEMENTATION.md for details.

## Residual Risks

- **Compliance-dependent timing.** All three write points rely on ordered step execution. No structural mechanism forces a write at each point — an agent could batch at the end. The eval system (child 03) is the right place to measure this empirically once available.
- **Turn numbering drift across sessions.** PROVENANCE.md has no mechanism to handle session boundaries in a resumed planning conversation. "Turn N" will restart. Accepted for current scope.
- **Variable "substance" extraction.** The intent-over-transcript guidance requires model judgment. Outputs will vary. The eval system can validate quality once child 03 is complete.

## Final Assessment

All seven acceptance criteria met. The three deferred risks are accepted for the current implementation scope. The implementation is committed and the completion artifacts are in place.
