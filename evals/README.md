# Evals

An eval is a full end-to-end run of the workflow — plan then execute — on a fixture scenario. Evals measure whether a proposed change to the workflow produces meaningfully better outcomes than the baseline, compared against a known reference implementation.

Evals are not unit tests. There is no absolute pass/fail. The question is: **does a proposed change produce meaningfully better outcomes than the current baseline, and are those outcomes in the same ballpark as the known reference?**

## Two Lenses

**Cost** (objective): agents spawned and their model sizes, tool use turns per agent, estimated context tokens, wall time. Use to detect regressions (change costs significantly more without quality gain) and improvements (same or better quality at lower cost).

**Quality** (relative): how close are the candidate's artifacts to the reference implementation? Are there significant regressions or improvements versus baseline? No exact rubrics — judgment is "significant delta?" and "same ballpark as reference?"

## Scenario Format

Each scenario lives in `scenarios/<name>/`:

```
scenarios/<name>/
  source.md          — repo URL, tagged commit, task description, reference notes
  reference/         — known-good solution artifacts or description (git diff, prose summary, or IMPLEMENTATION.md from the original solve)
  baseline/          — populated on first eval run from the current workflow; becomes the comparison point for future candidate runs
```

### `source.md` schema

```markdown
# Scenario: <name>

## Repo

- URL: <git clone URL>
- Commit: <tagged commit or SHA>

## Task

<description of the task to perform on this repo — what a plan session would receive as its request>

## Reference Notes

<what the reference implementation achieves; what a successful outcome looks like; known constraints or edge cases>
```

### `reference/`

Contains artifacts or a description of the known-good solution. May be:
- A git diff (`solution.diff`)
- An `IMPLEMENTATION.md` written during the original solve
- A prose summary (`SUMMARY.md`) if artifacts are not available

### `baseline/`

Populated on the first eval run using the current workflow. Contains: `PLAN.md`, `IMPLEMENTATION.md`, and any other files produced during execution — the same artifacts as a `candidate/` folder. Once populated, baseline is **never overwritten** — it is the fixed comparison point for all future candidate runs on this scenario. If you are unsure whether a baseline exists, check whether `baseline/` is non-empty before proceeding.

## Results Format

Each eval run produces a folder at `results/<scenario>/<timestamp>/`. Use `YYYYMMDD-HHMMSS` format for timestamps (e.g. `20260521-143200`).

```
results/<scenario>/<timestamp>/
  candidate/             — all artifacts produced by the candidate workflow run
    PLAN.md
    IMPLEMENTATION.md
    (any other files created during execution)
  cost-comparison.md     — objective cost metrics, baseline vs. candidate
  quality-comparison.md  — narrative comparison: candidate vs. baseline, candidate vs. reference
```

### `cost-comparison.md` schema

```markdown
# Cost Comparison: <scenario> / <timestamp>

## Baseline

- Agents spawned: <count and model sizes, e.g. "3 × sonnet, 1 × haiku">
- Tool use turns (per agent): <agent-1: N turns, agent-2: N turns, ...>
- Tool use turns (total): <sum>
- Context estimate: <tokens — if unavailable, write "not available (source: <reason>)">
- Wall time: <minutes:seconds>

## Candidate

- Agents spawned: <count and model sizes>
- Tool use turns (per agent): <agent-1: N turns, agent-2: N turns, ...>
- Tool use turns (total): <sum>
- Context estimate: <tokens — if unavailable, write "not available (source: <reason>)">
- Wall time: <minutes:seconds>

## Delta

- Tool use turns: <total baseline vs. total candidate — higher / lower / similar>
- Cost change: <higher / lower / similar — note significant differences>
- Notable changes: <anything that explains a cost difference>
```

### `quality-comparison.md` schema

```markdown
# Quality Comparison: <scenario> / <timestamp>

## Candidate vs. Baseline

<Narrative comparison. What changed? Are there significant improvements or regressions? What is better, what is worse, what is the same?>

## Candidate vs. Reference

<Is the candidate in the same ballpark as the reference implementation? Where does it fall short or exceed?>

## Summary

<One-sentence verdict: significant improvement, regression, or no meaningful change.>
```

## How to Run an Eval

1. Clone the scenario repo at the specified commit into a temporary working directory.
2. Run the full workflow on the task: `plan → execute`.
3. Capture the cost metrics during the run (agents, model sizes, tool turns, context, wall time).
4. Copy all output artifacts into `results/<scenario>/<timestamp>/candidate/`.
5. If no baseline exists yet, copy the candidate artifacts into `scenarios/<name>/baseline/` — this becomes the baseline for future runs.
6. Write `cost-comparison.md` comparing candidate to baseline (or note "first run, no baseline" if this establishes baseline).
7. Write `quality-comparison.md` comparing candidate artifacts to baseline and reference.

## How to Interpret Results

Ask two questions:

1. **Is there a significant cost regression?** — More agents, more tool turns, significantly more context or time, with no quality gain. If yes, the change is not worth it.
2. **Is the quality in the same ballpark as the reference?** — Not identical, but achieving the same goal at similar fidelity. If the candidate is significantly worse than the reference, the change needs work. If it is significantly better, that is strong signal.

Small differences in cost or quality within normal variance are not meaningful — baselines themselves have variance across runs. Only significant deltas (clearly more expensive, clearly worse outcomes, clearly better outcomes) should drive decisions.

## Fixture Corpus

Scenarios are built up over time from repos where the workflow has already been used and the outcomes are known. The initial corpus is empty. Add scenarios by:

1. Identifying a repo and task where you have a known-good reference outcome
2. Creating `scenarios/<name>/source.md` with the repo URL, commit, task, and reference notes
3. Adding the reference artifacts or description to `scenarios/<name>/reference/`
4. Running the eval once to establish the baseline

The system ships with the pattern, not the fixtures.
