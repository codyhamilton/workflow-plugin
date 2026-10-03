# Use cases 2-4: what Stage A discipline requires, and what data exists (2026-10-03)

Source of the cases: [use-cases-cody-locked.md](RESEARCH/2026-09-30-jev-cheap-judgement-signals/use-cases-cody-locked.md). Case 1 is covered by [STAGE-A-WRITEUP.md](STAGE-A-WRITEUP.md). The objection that settled case 1 ("a counter does the same job, so why check") is weaker here: the input is text a counter cannot read. It is not absent: each case has a zero-call baseline that must be beaten first.

| Case | Jev judges | Zero-call baseline | Outcome label (not the model's own opinion) |
|---|---|---|---|
| 2. After refine | brief complexity, to review largest before dispatch | brief line/char count, number of files or acceptance items named | unit later exceeded its budget: worker turns, cost, "done with concerns", splits or re-briefs |
| 3. Unit complete | does the closing record need review? | trailer present, headings, verifier exit code | review or rework found real defects after the unit; a later fix commit touching the same files |
| 4. Phase complete | does the report align with phase intent? | `tools/driver/phase_assert.py --deterministic` | later rework of the phase, or a plan-level revision |

## Data inventory (found, not yet analysed)

- About 133 distinct brief files (md5-unique) across real consumer repos in `~/workspace` (open-pajero-maps, garcia-music, silver-chronicle, chm-briefs, corpus-ops, free-frontier), after excluding workflow-plugin's own worktrees and the many clones of the same repos.
- Unit outcomes in git: e.g. open-pajero-maps has 338 commits with unit-level subjects ("Plan 04 Phase 3 unit 3-14 ... done with concerns", merges), and per-plan `IMPLEMENTATION.md` files.
- Driver run records (`tools/driver/.run-record.jsonl`) hold provider cost/turns and the last workflow-report per invocation, where runs were made.
- Worker transcripts per brief exist for projects with Claude/Cursor sessions (the Stage A corpus partly covers them).

## Caveats to settle before any measurement

- Many briefs are duplicated across worktrees and clones: split by brief id (content hash), never by directory, or the held-out set leaks.
- Outcome labels need to be derived mechanically from git/driver data first (turns, cost, "concerns", follow-up fixes) and hand-checked on a sample, as Stage A showed label error is one-sided and caps AUC.
- Case 4's baseline already exists and is authoritative; the Jev question there is only whether it flags drift the assert passes.
- Held-out for these cases is separate from Stage A's and stays sealed until a dev-replicated result exists.

## Proposed order

1. Case 2 first: most data (133 briefs), cleanest mechanical outcome (budget overrun), and a trivial baseline (length).
2. Case 3: derive "later fix to same files" from git; needs more care on label noise.
3. Case 4: fewest samples; likely a descriptive section, not a test.
