# Data induction: what differs between troubled and clean briefs

Source: `outcome-proxies.jsonl` (130 briefs, garcia-music, open-pajero-maps, silver-chronicle), 15 troubled (T) and 15 clean (C) briefs of comparable churn size, their fix/amend commits, and plan 03 DESIGN.md/GATE-2.md in open-pajero-maps. Counts are k of 15 T vs k of 15 C unless noted. Features were found with crude regexes on pre-amendment brief text (text before any `## Amendment`).

## Proxy audit (read first)

The proxies are weak. Treat every count below as a lead, not a result.

- `fixchurn_60d` uses the regex `\b(fix|revert|regress|hotfix|remediat|repair|broken|bug)\w*`, which also matches "fixture", "fixers", "regression". Much of the signal is lexical.
- Hot shared files (en.ts/es.ts, apps/web) inflate churn for any brief that lists them.
- qa-assess briefs are themselves landed as "fix:" commits, so they look troubled by construction.
- A single shared test-repair commit in silver-chronicle is counted against many briefs.
- Garcia `first_commit_ts` is a bulk import (1785553068). The original text of garcia briefs is not recoverable, so for garcia T briefs only the post-amendment text and the amendments exist. Garcia has no clean control group.
- Non-path tokens in backticks are parsed as owned paths.
- I recomputed a strict version (cold paths only, fix verbs on subject, no fixture/regression). It shrinks the troubled set but the rankings mostly held. Pre-amendment comparison covers only 10 of 15 T briefs.
- Project is confounded with outcome: T is mostly garcia and open-p, C is mostly silver and open-p.
- No downstream-defect ground truth exists. "Troubled" means "git touched these paths with fix-like words", not "the brief caused a defect".

## Result on Cody's hypothesis (unproven assumptions, arbitrary thresholds)

- Brief level, open-pajero-maps only: no separation. About 3 of 9 troubled vs 6 of 15 clean open-p briefs cite a basis (measurement, prior run, contract, source) for their thresholds or load-bearing assumptions. Thresholds appear in few briefs at all. The data does not support the hypothesis at brief level.
- Counter-evidence at brief level: 3-07 cites R evidence for its bar and was still amended. 2-08 pre-states 13 thresholds (`MARGIN_MATCH = 1.5`, `AXIS_COVERAGE_MIN = 0.75`, `CLIP_EXACT_MIN = 0.9`, ...) with only "chosen at refine time so the discrimination cannot be produced by the cell spread", and the proxies scored it clean. So the proxies are blind to this failure.
- Design level, plan 03: the hypothesis is supported in one case. Phase 2 gate post-mortem (DESIGN.md amendments, GATE-2.md): of the gate criteria that were worker-picked statistical proxies, 3 of 4 failed; the 1 grounded criterion passed. Criterion 5 ("at least 99%") is called arbitrary in the text. The 0.75 axis-coverage threshold was retired because the geometric ceiling is 9/16. Phase 2 restarted twice. This is one plan, so n=1.
- Net: plausible and consistent with the one design post-mortem, not demonstrated by the brief proxies. See C2.

## Candidates

### C1: Done evidence is runnable by the worker; browser or staging checks are deferred and owned
- subject: brief
- claim: Every Done-evidence item can be executed by the worker in its sandbox (a command with an expected result). Anything needing a browser, device, or staging is listed separately as deferred, with a named owner and where it will be run.
- failure_prevented: A brief reports done on unit tests while the user-visible behaviour is unverified; the gap surfaces later as a fix or QA-assess commit.
- evidence: 4 T vs 0 C of the pre-amendment briefs put browser/staging verification inside Done evidence. Garcia amendments for briefs 1, 3, 4 and 5 say "browser QA deferred". Plan 15 qa-assess-002/005/007 exist to catch what the earlier briefs could not verify.
- checkable_by: jev
- check_recipe: L0 no Done-evidence items are commands, only prose. L1 some commands, but at least one item needs a browser or staging with no owner. L2 all items are commands or explicitly deferred, but deferred items have no owner. L3 all items are commands or deferred with a named owner and run location.
- counterexample: Silver briefs with only command-based evidence were still followed by test-repair commits (see C10), so runnable is necessary at most, not sufficient.
- confidence: medium

### C2: Each acceptance threshold or load-bearing assumption names its evidence or is marked as an unproven assumption to be tested first
- subject: both
- claim: Every numeric bar, tolerance, or "X is true" assumption the work rests on cites a measurement, prior run, contract, or source, or is labelled "unproven, test first" with the test as the first step.
- failure_prevented: Work built on an assumption that turns out false, or a gate that fails because its number was picked without a basis; the work is redone.
- evidence: Design-level only. Plan 03 DESIGN.md amendments and GATE-2.md: 3 of 4 worker-picked statistical gate criteria failed; criterion 5 "99%" called arbitrary; 0.75 axis coverage retired (ceiling 9/16); `MATCH_MIN 0.8`; 2-08 pre-stated thresholds with no basis; Phase 2 restarted twice. Brief level: no separation (about 3/9 T vs 6/15 C with sourced thresholds).
- checkable_by: jev
- check_recipe: L0 thresholds or assumptions present with no basis and no flag. L1 some name a source, others are asserted. L2 every threshold names a source, but the source does not actually support the number. L3 every threshold and assumption names evidence that supports it, or is flagged unproven with a first-step test.
- counterexample: 3-07 cites R evidence yet was amended anyway. 2-08 disclosed its thresholds were chosen after seeing the first run's numbers, which is a basis of sorts, and the proxies rated it clean.
- confidence: medium at design level, low at brief level

### C3: Scope closure, importers and shared files inside owned paths are listed or handed off
- subject: brief
- claim: For each symbol or file the brief changes, the callers, importers, tests and shared files that change with it are either in Owned paths or explicitly assigned to another brief.
- failure_prevented: The brief lands, then a follow-up fix touches the files it left out (broken imports, failing tests elsewhere).
- evidence: Post hoc. In 6 T vs 1 C, a fix/amend commit touched a file that a plain grep of the changed symbol shows was outside Owned paths. This is circular (the proxy is built from owned paths), so the count is inflated.
- checkable_by: deterministic
- check_recipe: For each exported symbol or renamed path in Changes, grep the repo at the base commit for references; fail if any referencing file is neither in Owned paths nor named in Keep untouched/Depends on.
- counterexample: Hot shared files (en.ts, es.ts) always show up as references; a literal check will over-fail on them unless allowed by an explicit shared-file rule.
- confidence: low

### C4: Anchors are symbols, not line numbers, and referenced files exist
- subject: brief
- claim: Code references name a function, type, or test title, not `file:line` ranges, and every referenced path exists at the base commit.
- failure_prevented: Workers act on stale line numbers or wrong paths and mis-edit or report the wrong target.
- evidence: Briefs with at least 3 line refs: 5 T vs 3 C. At least 5 line refs: 5 T vs 1 C. Garcia amendments correct stale refs; one cites `catalog.ts` and one a wrong test path. Generic path-existence regex was too noisy to use (see Does not work), so the path half is anecdotal.
- checkable_by: deterministic
- check_recipe: Count `\S+:\d+(-\d+)?` references; flag above a threshold. For each backticked path expected to exist, `git cat-file -e <base>:<path>`; the brief must mark new files as new.
- counterexample: Line refs are fine when pinned to a commit and accompanied by the symbol name.
- confidence: low

### C5: Every named type or contract is defined in the brief or points to where it is defined
- subject: brief
- claim: Any type, error, or interface the Contract section names (e.g. `PlaybackError`) is given a shape, or a path where it is defined.
- failure_prevented: Parallel workers each invent their own shape and the pieces do not meet.
- evidence: One garcia case (PlaybackError named but not defined). No count across groups.
- checkable_by: jev
- check_recipe: L0 names undefined types. L1 some defined. L2 all defined but inconsistent across briefs. L3 all defined once and referenced consistently.
- counterexample: Types already in the repo do not need redefinition, only a pointer.
- confidence: low

### C6: Pinned values that depend on upstream work are flagged for re-derivation
- subject: brief
- claim: Hashes, baselines, paths, or counts taken from an earlier brief's output are marked "re-derive after <dep> lands" and not pasted as constants.
- failure_prevented: The upstream brief changes, the pinned value goes stale, and the downstream brief fails or tests the wrong thing.
- evidence: Two cases in open-p: the 3-02 baseline shas and the spool path, both amended. Pinned hashes in general do not separate groups (2 T vs 6 C), so only pinned-and-upstream-dependent values matter.
- checkable_by: jev
- check_recipe: L0 pinned upstream values with no note. L1 noted as pinned. L2 flagged but no re-derivation step. L3 flagged with an explicit re-derive step in Changes.
- counterexample: Pinned hashes in a brief with no upstream dependency are harmless and common in clean briefs.
- confidence: low

### C7: A failing check is named before the change and expected to pass after
- subject: brief
- claim: Done evidence states which test fails before the change and passes after, and says to report both.
- failure_prevented: A test that passes both before and after proves nothing.
- evidence: Weak. 10 of 10 checked T vs 15 of 15 C use some form of it, so it does not separate. It is listed only because 2-05 states it well ("fails before (stub) and passes after (report both)").
- checkable_by: deterministic
- check_recipe: Regex Done evidence for "fails before" / "before and after" near a command.
- counterexample: Does not distinguish the groups at all; present in all clean briefs.
- confidence: low

### C8: Design invariants are placed within the owning unit's scope
- subject: design
- claim: Each invariant stated in the design names the one brief or unit that must enforce it, and that unit's owned paths cover the code where it is enforced.
- failure_prevented: An invariant is stated globally and no brief owns it, so each brief assumes another does.
- evidence: Garcia briefs 05 and 06 (occluded): the invariants lived in a design section, the code lived in another brief's paths.
- checkable_by: jev
- check_recipe: L0 invariants have no owner. L1 owner named loosely ("player work"). L2 owner brief named but its owned paths do not cover enforcement. L3 owner brief named and covers it.
- counterexample: Cross-cutting invariants (lint rules, types) legitimately have many enforcers.
- confidence: low

### C9: Environment and machine constraints are stated
- subject: brief
- claim: If the work needs a resource limit (heavy lock, /tmp quota, memory, ports), the brief says so and says what to do when it is missing.
- failure_prevented: Workers stall or fail on the machine, not on the code, and the failure is logged as a fix.
- evidence: Anecdotal: /tmp quota and heavy-lock failures in amend commits. No count.
- checkable_by: human-only
- check_recipe: A reviewer asks whether the work runs anything heavy and whether the brief says how.
- counterexample: Most briefs need none.
- confidence: low

### C10: Proof includes a real boundary, not only mocks
- subject: brief
- claim: At least one Done-evidence item exercises the real boundary (real file system, real signer, real route) the code crosses, and the brief says which parts are mocked.
- failure_prevented: Mock-only tests pass while the real integration is broken, later repaired.
- evidence: Silver test-repair commits that touched many briefs. Mocks mentioned in 4 T vs 1 C pre-amendment text (e.g. `MiniPlayer.test.ts:32-34` mocks the store wholesale; the stub `matchMedia` in brief 5 hid the intended fade work). Mentions alone are not a measure of the lack of a real boundary test.
- checkable_by: jev
- check_recipe: L0 all evidence is against mocks with no statement. L1 mocks stated, no real-boundary item. L2 one real-boundary item but not for the main path. L3 main path exercised at the real boundary and mocks listed.
- counterexample: Some boundaries cannot be run in a worker (paid APIs); C1's deferral applies.
- confidence: low

## Does not work

These were tried and showed no separation or were unreliable.

- Path-existence regex: too many new files and bare filenames.
- Sibling file overlap between briefs: 14 T vs 15 C.
- Section presence (all required sections): everything has them.
- Length: T mean 1311 words vs C mean 1488.
- Hedge words ("should", "probably"): no separation.
- Pinned hashes: 2 T vs 6 C, the wrong direction.
- Numeric budgets: no separation.
- The `fixchurn_60d` proxy itself as a quality signal, per the audit.

## Gaps

- Garcia original brief text is unrecoverable; its T counts use post-amendment text for 5 briefs, and there is no garcia clean control.
- Project confound: outcome tracks project and plan era.
- Bulk-import timestamp makes the 60-day window wrong for garcia.
- Proxy noise (lexical, hot files, shared repair commits, qa-assess landing as fix:).
- n=15 per group; all differences here are within noise except possibly C1 (4 vs 0) and line refs at 5+ (5 vs 1), and those are post hoc.
- No downstream-defect ground truth; nothing here shows a brief property caused an outcome.
- Regex features are crude; jev-checkable candidates (C1, C2, C5, C6, C8, C10) were not run through jev, so the check recipes are untested.
- The open-p hypothesis is tested at brief level only on a handful of thresholds; the supporting evidence is one plan's post-mortem.
