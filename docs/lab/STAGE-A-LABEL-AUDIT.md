# Stage A label audit protocol (redirect / new_task negatives)

Purpose: replace my one-reader estimate (6/20 non-adjust labels arguably adjust) with an independent human estimate, and re-score Stage A on audited labels. Needs one person (not a model), about 60-75 minutes.

## What to do

Open `audit_sheet.csv` in the Stage A archive (`~/jev-lab-data/2026-10-03-stageA/analysis/`; local only, it holds real human prompts and is not in the repo). 128 items, shuffled, blind to the existing labels, Jev scores and splits. For each row read the previous human prompt, the agent's last tool calls, and the human's next message, then fill `verdict` (and `confidence_1to3`, 1 = unsure). Need more context? the `transcript` path is in `audit_items.json` (same item ids).

## Verdict rule (one of)

- `adjust`: the message takes the agent's work *as already done* and asks to fix, change, extend, or finish it, or reports something broken or missing in it (bug reports about the just-finished feature count).
- `question`: asks for an explanation or information, with no request to change anything.
- `approve`: accepts, or tells the agent to proceed or commit.
- `redirect`: chooses a direction or decision *before or instead of* work (answering the agent's question, adding input to a plan, changing approach to the task, "stop and do X").
- `new_task`: a distinct task, not about the agent's last work.
- `abort`: stop, undo, or abandon.
- `unclear`: cannot tell from what is shown.

Tie-break: if the message both reacts to the agent's work and adds new scope, choose `adjust` when the reaction is the main point. The same rules were given to the labelers; the audit tests whether they applied them.

## The sample (fixed, seed 20261003)

| group | n | how drawn | purpose |
|---|---|---|---|
| redirect | 60 | all 17 plan/ask-question context redirects, plus 43 random other redirects | hidden-adjust rate among redirects (60 gives about +-10 points at 90%) |
| new_task | 28 | all | same, for new_task |
| adjust control | 20 | 10 correct, 10 refine, random | confirms positives |
| other control | 20 | 10 question, 10 approve, random | calibrates the auditor against clear negatives |

The key (item to session, checkpoint, group, label) is `audit_key.json`; the auditor should not open it before finishing.

## Scoring

`python3 audit_score.py filled.csv` (in `analysis/`) reports, per group, the verdict mix and the share the auditor calls adjust with a 90% Wilson interval; control agreement; AUCs of turn, counters, master, Jev mean and ui-visual on original versus audit-corrected labels (audited items flipped, unaudited unchanged); and the ceiling of a predictor perfect on the current positives if the audited hidden-adjust rate holds across all redirect and new_task. Smoke-tested with simulated verdicts.

## Decisions it drives

- Hidden-adjust rate among redirect/new_task under 10%: noise is not the cap; the 0.7 ceiling is real; Stage A conclusion stands as written.
- 10-25%: audit the remaining 85 redirect/new_task items, relabel, re-run round 8/9 comparisons on corrected labels before any new signal round.
- Over 25%: labelers need new instructions (the rule above) and a relabel of all 501 before further analysis.
- Control agreement below 90% (of 40): the verdict rule is ambiguous; revise it before trusting the rest.
