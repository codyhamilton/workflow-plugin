# Gold-label rubric — when continuing was a mistake

**Status:** protocol. **Confidence: not high.** The P0 prefixes were labeled on 2026-10-01 under the rules above the draft delta at the end of this file. That delta is not in force and was not shown to those seats.

Judges apply this rubric to a prefix bundle. They do not apply the Jev question text in [`TERMS.md`](TERMS.md) §6. Sharing the Jev wording with the judges would make the gold a copy of the instrument. The axes match, because both are trying to name the same event. The sentences do not.

## The decision

At labeled turn `c`, the judge answers one question:

> Has continuing this worker past turn `c` already become a mistake?

| Answer | When |
|--------|------|
| `not_yet` | The prefix still supports more work by this same worker, or the evidence is too thin to call a mistake |
| `checkout` | A fresh worker with a narrower brief, or a stop, is the warranted next step. Another interval of the same pattern is the likely future of this one |

`checkout` is the exit hatch. It is not a comment that the worker is large. Turn count is the schedule’s job. A judge who checks out because `c >= 75`, or because the file is famous, has left the rubric.

The judge also marks which patterns are present, zero or more:

| Pattern | Present when |
|---------|----------------|
| `runaway` | The prefix shows repeated cycles that do not change the artifact or the decision: the same paths read again, poll or sleep, the same edit retried without a new fact |
| `low_progress` | Since the previous labeled turn (or since the start, at turn 60), there is no checkable step: no edit, no test result that changed the plan, no decision that narrows the brief |
| `context_thrash` | Compaction markers are accumulating, or the worker is re-reading in order to refill a context that is already near the compaction ceiling. Peak context in the 125k–147k band is the maps signature of that ceiling. The peak alone is not thrash. Thrash is the cycle of compact and re-read |
| `scope_drift` | The latest turns pursue a different task from the brief anchor |

And a rationale of at most 120 words naming the turns inside the prefix that justify the answer. The rationale is for adjudication when alpha is low. It is not shown to other judges.

`checkout` requires at least one pattern. A checkout with an empty pattern list is an invalid label and is dropped, not coerced to `not_yet`.

Thin evidence is `not_yet`, not a third button. Fail-open lives in the Jev policy. The gold question is binary so that alpha has one table.

## What the judge is shown

The bundle for turn `c` is built from `prefix(c)` only.

1. `brief_anchor`: first user text, 500 characters, or `missing`.
2. Cumulative stats, the same fields as hybrid v0 in TERMS §5, computed on the prefix.
3. The last **30** assistant turns, each excerpt 700 characters, tool names included, tool results omitted.
4. A one-line note of how many assistant turns exist in the prefix (`api_turns = c`). That line is the length of the prefix, not a hint that the file continues.

Cap: **60_000** characters on the serialized bundle. Shrink by dropping the oldest of the 30 turns first, then cutting excerpts to 350. If the cap still fails, the prefix is `unlabelable` and is left out of alpha. Do not silently show different judges different bundles.

The judge is not shown: later turns, another judge’s label, any Jev answer, the worker’s nickname in this pack (“smoking gun”), or the maps flags as a pre-filled verdict. Stats the judge can recompute from the prefix (re-read counts, compaction count, peak) may be in the bundle because they are functions of the prefix. A banner that says `OVER_TURNS` is not a function of the prefix; leave it out.

## Patterns, tied to the maps evidence

The maps write-up describes **finished** files. A prefix judge must not be told the ending. The notes below say what a prefix would have to contain for each pattern. They are calibration examples for the people who audit labels, and they are the text the judges receive as examples. Where an example depends on the ending, it says so and is marked **hindsight illustration**. Judges are told not to require the hindsight numbers.

### Runaway

**Hindsight illustration, `92a48e004519`.** The finished file has 296 assistant calls, six paths re-read at least three times, and about three sleep/poll bash calls (`evidence-maps-claude-5h.md`). A prefix shows `runaway` when those repeated reads are already in *that prefix*, not because the file eventually reached 296. Three reads of one path inside the prefix meet the “at least three” shape. A single re-read does not.

**Not runaway.** A long investigation that reads many distinct files once each, then edits. Length is not repetition.

### Low progress

**At the first labeled turn (60).** Compare to the brief anchor only. A worker that has spent 60 turns reading and has not edited, tested, or narrowed the task is `low_progress`. A worker that has landed a partial edit and a failing test it is responding to is not.

**At later labeled turns.** Compare to the previous labeled turn, 15 turns earlier. Fifteen turns of reads with no edit and no new decision are `low_progress` even if the first 60 turns were productive.

**Not low progress.** A slow but monotonic implementation: each interval contains an edit or a test that changes what the worker does next.

### Context thrash

**Hindsight illustration, `92a48e004519`.** About sixty compact-ish events and a 130k peak on the finished file. **`bb6165018de0`** finished at 154 calls with a 125k peak and a JSONL of about 3.3MB. Maps treats the 125–147k band as the compaction ceiling, and treats peak, not the final context, as the sizing signal.

A prefix shows `context_thrash` when compaction markers in that prefix are recurring and the worker re-reads material the compaction dropped. One compaction after a large read is not thrash. Peak context at 125k with continuing distinct work is the ceiling, not thrash.

**Not thrash.** A transcript that is large because tool output is verbose, while the assistant turns still advance the brief. Verbosity is a cost problem the field note already separates from turn count. This rubric does not checkout for bytes alone.

### Scope drift

**Example shape.** The anchor says to implement one API surface. The latest turns are refactoring an unrelated package, or writing a research note, or re-planning the whole phase. That is drift.

**Not drift.** Reading a neighbouring file to implement the anchor. Opening the test that the brief named. A refine-shaped worker such as `6c87c96bd9bb` (70 turns, “Refine Phase 3C”) is doing the task it was given if the anchor is refine. That file is below 75 turns and is not in the gold corpus. It is the negative picture: a worker inside the band, with no published thrash flags, is the kind of prefix that should be `not_yet` if it were labeled by mistake.

### Several patterns at once

The finished `92a48e004519` file, read with hindsight, is the picture the rubric was written to catch: repetition, compaction, and a run that continued far past any checkable need visible in the public summary. A prefix-causal checkout might land well before 296, or the early prefixes might be `not_yet` because the thrash had not started. Both outcomes are allowed. The rubric does not contain a target turn for this worker. Putting 76, 85, or 100 into the rubric would copy the old gate into the gold.

`bb6165018de0` is priority corpus because it is long, not because the rubric already says it should have stopped. The panel may return null. A null gold with a Jev checkout is `false_early`. That is a successful use of the rubric.

## Invalid labels

| Condition | Treatment |
|-----------|-----------|
| `checkout` and no pattern | Drop the judge’s label at that prefix |
| Rationale cites a turn `> c` | Drop. The bundle leaked or the judge used outside knowledge |
| Rationale’s only reason is the turn count or the ideal band | Drop |
| Two judges in one session, or a judge shown another rationale | Discard the whole worker’s panel and re-run |

Dropped labels can push a worker under the three-judge minimum. The worker then becomes `underpowered` rather than filled in.

## Aggregation reminder

The default gold turn is the earliest labeled turn where every remaining judge said `checkout` ([`TERMS.md`](TERMS.md) §7, rule `A0`). One judge’s early checkout does not set the gold. That is deliberate: R-Judge and the LLM-as-judge literature both say trajectory and preference judgements move around (see [`LITERATURE.md`](LITERATURE.md)). Unanimity is how this protocol refuses to treat one model’s first twitch as the truth.

Each judge’s own first checkout turn is still stored. The spread across judges is reported before Jev is tuned. If the spread on a smoking gun is the whole file (one judge at 60, another never), the rubric is not yet stable on the example that matters most, and H5 should be read together with that spread rather than as a single pooled alpha.

## Hindsight pass

After the prefix labels are stored, each judge may see a full-file bundle, capped at the same 60_000 characters with the same shrink rule, and name one first checkout turn or null. This pass is `gold_exit_turn_hindsight`. It exists to measure how much the ending moves the call. Parameters are not chosen from it.

The hindsight pass is where the public maps summary is most tempting. Judges on that pass are still not given the maps paragraph. If their hindsight turn clusters on the same number the maps flags suggest, the lock memo should say that the ending is legible from the transcript itself. If they only cluster when the maps paragraph is in the prompt, a later experimenter has contaminated the label.

## Draft delta — not in force (2026-10-01)

The signed P0 rows used the rubric above. This section was the extra paragraph for experiment **(b)** Sonnet re-label (`parent-pull-v1`) in [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md). **(b) failed** (over-fire); these rows were **discarded as gold**. The section stays **not in force**. Next labeling uses the original rubric only (**(c)** `corpus-expand-hybrid-panel-original`). Do not paste the experiment scorecard, other seats' labels, or target turns into the judge prompt.

`checkout` means a parent-pull: hand the parent a narrower brief, or stop. The worker does not have to look idle. A Bash/Read cycle on files named in the brief can still be `checkout`.

When the prefix already shows `runaway` (a path read at least three times) and the interval since the previous labeled turn adds no new path and no Edit or Write, the following are not reasons to stay at `not_yet`:

- Bash might be editing through sed, a heredoc, or a shell redirect.
- The re-read files are the ones in the brief.
- A compaction would force a re-read, so the re-read is ordinary recovery.
- The tail excerpts are empty, so the call feels thin.

Empty excerpts plus that shape are enough. Mark `runaway` and `low_progress`. One such interval can still be the brief's long gate. A checkpoint with no delta (the first labeled turn on this schedule) is not a frozen interval. The first checkpoint whose delta adds no new path and no Edit or Write is the first frozen interval and stays `not_yet`. `checkout` starts on the following labeled turn when that turn's delta is frozen as well.

Stay at `not_yet` when any of these is true: the tail names a checkable step (a fix, a test, a gate, an artifact); a new path appears; assistant text has grown since the previous labeled turn; the worker is waiting on a named in-flight job that reports milestones and the histogram already contains Write or Edit. Turn count, peak context, and compaction count remain insufficient on their own.
