# Report: 6-01 skills and templates

Done against the brief. The design, refine and execute skills and the two templates no longer mention posting, ids or execution logging. The comprehensive-review, close-out and post-build skills had no grep hits and were not touched.

- design and refine: the "Ratings are obtained" bullet is now a feedback rule built on `artifact_feedback(path)`. The hook backstop bullets are deleted. The frontmatter-identity rules now say there are no identity, status, score or progress fields.
- execute: the logging and `[exec <id>]` bullets are replaced by the report requirement (`docs/plans/<plan>/reports/<brief-name>.md`, rubric pointer, runner calls `artifact_feedback` before closing the phase) and a plain-summary commit title rule. The `Workflow-Phase:` text is unchanged (count 3 before and after).
- Templates: frontmatter blocks removed. The brief template gained a Report line.
- Checks: the id and `[exec` grep over `skills/` and `plugins/` returns nothing (exit 1). The `workflow-quality|8765|QUALITY-SERVICE` grep over `skills/` returns nothing. No relative link is broken.

Departures: none. One count mismatch: the brief says 11 hits in 5 files, and I saw 9 lines in 5 files (several lines carry more than one term).

Unfinished: none. Known problem: phase-5 and earlier briefs still carry `brief_id` frontmatter, which is history by design.
