# Next experiment — after H5 failed

**Status:** plan. **Confidence: not high.** H5 failed. No Jev sweep, no hook change, no Sonnet re-label in this revision.

**Primary experiment:** **(b)** re-label the Sonnet seat on the same 21 P0 prefixes after the draft rubric delta. Success is a new 3×21 table that can make `A0` non-null on `92a48e004519` without checkout on the unanimous `not_yet` prefixes.

Alternate targets already computed from the signed JSONL: [`proofs/validated/gold/p0-alt-gold-targets-20261001.json`](proofs/validated/gold/p0-alt-gold-targets-20261001.json). They are recorded. They are not the fit target.

## Hard numbers this choice uses

Sources: the three signed JSONLs, [`p0-panel-agreement-20261001.json`](proofs/validated/gold/p0-panel-agreement-20261001.json), the alt-targets file, and the committed ubuntu-raw thrash table `SUMMARY-ubuntu-raw-dry-run-20261001-194107.json`. Flash drafts are excluded (21 draft rows, 0 used).

| Fact | Number |
|------|--------|
| Prefixes | 21 (15 on `92a48e004519`, 6 on `bb6165018de0`) |
| Sonnet `checkout_recommended` | **0 / 21** |
| Composer checkout cps | **3** (180, 195, 210), all on `92a48e004519` |
| Grok checkout cps | **8** (105–210), all on `92a48e004519` |
| A0, both workers | **null** |
| Krippendorff α (nominal, 3×21) | **0.1189** (H5 floor 0.40) |
| Cohen κ, Composer ↔ Grok | **0.4262** |
| Cohen κ, Sonnet ↔ either other seat | **0** |
| **A_maj** (2 of 3) earliest | **180** / **null** |
| **A_gc** (Grok ∩ Composer) earliest | **180** / **null** |
| Checkpoints where `majority_label` = `gc_label` | **21 / 21** |
| Majority-checkout checkpoints | **3 / 21** |
| Grok-only checkpoints (105, 120, 135, 150, 165) | **5** |
| Unanimous `not_yet` | **13** (7 on `92a48e004519`, 6 on `bb6165018de0`) |
| Ubuntu-raw Jev `missing_rate` on both guns | **1.0** (`decision=missing`, `reason=dry_run`) |

`A_maj` equals `A_gc` on both workers, and the per-checkpoint labels match at all 21 rows, because Sonnet never supplies a second vote. Majority is Grok and Composer both saying checkout. That happens only at 180, 195, and 210. At 225, 240, 255, 270, and 285 both of those seats return to `not_yet`, together with Sonnet.

The thrash table shows why that return is the same shape as the labels, not a flicker:

| `92a48e004519` cps | `assistant_text_chars` | `new_read_paths` | Edit/Write in histogram | Re-read tops |
|--------------------|------------------------|------------------|-------------------------|--------------|
| 75–210 | **36** at every cp | **[]** on every delta from 90 through 210 | none (Bash/Read only) | `_cenc.c` 10→26, `divide.py` 7→20, `_e2.c` 6→16 |
| 225 | 68 | first new path, `parts/p1.c` | none | climb stops |
| 240, 255, 270, 285 | 195, 235, 365, 562 | [] | none | frozen at 26 / 20 / 16 |

`bb6165018de0` is the other shape: assistant text **2174** already at cp 75, a Write in the histogram, the spec PDF at 3 reads, compactions 0 until cp 135. All three seats stay `not_yet` on all 6 cps. The signed Sonnet rationales on `92a48e004519` through cp 210 correct every Flash checkout with the same three vetoes: Bash may hide an edit, re-reads of brief files after compaction are ordinary, empty excerpts are thin evidence. From cp 240 the same seat cites named cleanup (grep gate, ctest, struct rewrite, brief amendment), which is where Composer and Grok are also `not_yet`.

## Why (b) is the primary measurement

H5's pre-registered consequence is to revise the rubric or the bundle and re-label, and to leave H1–H4 and H6–H7 uninterpreted ([`HYPOTHESIS.md`](HYPOTHESIS.md)). The 0/21 Sonnet column is the whole of the A0 null and almost the whole of α = 0.1189. Composer and Grok already clear a pairwise 0.40 on the packs (κ = 0.4262). The missing measurement is whether one paragraph moves Sonnet onto the three checkpoints where a second vote already exists, and off the 13 checkpoints where every seat said `not_yet`.

**(a) stays deferred.** Adopting `A_maj` or `A_gc` as a fit target adopts one number twice: both earliest exits are 180 and null, and both per-cp labels agree 21/21. The positive set is 3 checkpoints on one worker. Earliest-exit scoring would then treat cps 225–285 as after gold, while `majority_label` at those five checkpoints is `not_yet` and the thrash stats have left the frozen window (text 36→68 and the first new path at 225; text 562 by 285). Ubuntu-raw has no Jev decision to score (`missing_rate` 1.0 on both guns). A stats-gate sweep against that island would be a fit on n = 1 positive worker, which is the fit H5 forbids.

**(c) stays the follow-on after a pass, not the next run.** The reliability failure on these 21 rows is one constant seat, and the corpus for a label already exists. TUNING-PLAN still marks H1 underpowered while the only `T >= 75` gold rows are these two workers. That constraint blocks a sweep after (b) passes. It does not block re-labeling the 21 prefixes already in git.

## Protocol

1. Fresh Sonnet session. Prompt is the current [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) body plus the draft delta at the bottom of that file. Omit this scorecard, worker nicknames, other seats' labels and rationales, and the sentences in the rubric that state 296, 154, or 130k (the split already required by [`TUNING-PLAN.md`](TUNING-PLAN.md)).
2. Same 21 prefixes, same schedule `75:15`. Input bundle is the gold-bundle family Sonnet already signed (`*-gold-bundles-20261001-194107.jsonl`, gitignored under `proofs/validated/ubuntu-raw/`). Hold that bundle fixed. The hybrid_v0 packs are a different factor: at cp 255 the pack tail has 0 nonempty excerpts, while the signed Sonnet rationale cites named cleanup across turns 236–255.
3. If that gold-bundle file is not on the machine, record **blocked**. Do not substitute the packs in the same run.
4. Write a new JSONL. Leave `p0-checkout-verdicts-20261001.jsonl` untouched. Flash stays excluded. Composer and Grok rows stay the committed ones.
5. Recompute A0, the 3×21 nominal Krippendorff α (same binary `checkout_recommended` setup as the panel file: 3 coders, 21 units), and the Sonnet positive set. No `--call-jev`. No hook, `settings.json`, or `install.sh` edit.

A `checkout` with an empty pattern list is invalid and dropped, per the existing rubric. A dropped label on a required checkpoint counts as a miss.

## Scorecard

| Set | Checkpoints | Rule |
|-----|-------------|------|
| Required Sonnet checkout | `92a48e004519` at **180, 195, 210** | All three true. Composer is true only here, and Grok is already true, so this is where A0 can leave null |
| Hold-out, Sonnet stays `not_yet` | `92a48e004519` at **75, 90, 225, 240, 255, 270, 285** (7) and `bb6165018de0` at **75, 90, 105, 120, 135, 150** (6) | **13** prefixes. Zero Sonnet checkouts |
| Reported either way | `92a48e004519` at **105, 120, 135, 150, 165** | The 5 Grok-only cps. Publish the count. It does not pass or fail on its own |

**Pass** when all three hold:

1. Sonnet `checkout_recommended=true` at 180, 195, and 210.
2. Sonnet checkout count on the 13 hold-out prefixes is **0**.
3. Recomputed α **≥ 0.40**.

On a pass, A0 for `92a48e004519` is **180** (the earliest required cp; Grok and Composer are already true there). A0 for `bb6165018de0` stays **null**. Confidence stays **not high**. H1 stays underpowered at n = 2.

## Stop rules

1. **Over-fire.** One or more Sonnet checkouts on the 13 hold-out prefixes. Discard the new rows as gold. Do not start a Jev or stats sweep. Do not adopt `A_maj`.
2. **No bite.** Sonnet remains 0/21. Do not paste the same paragraph into a second Sonnet run. The next change, if any, is a bundle change (a Bash-argument excerpt), and that is a separate experiment.
3. **Island missed.** Sonnet is false at any of 180, 195, 210. A0 stays null. Do not sweep, including when Sonnet did checkout on some of 105–165 and α rose.
4. **α still under the floor.** New α < 0.40. H5 remains failed. H1–H4 and H6–H7 stay uninterpreted.
5. **Pass, then corpus.** After a pass, label **at least two more** `T >= 75` sessions under the same revised rubric before any fit. Pooled α on the enlarged panel must still be ≥ 0.40. Until that lands, do not run the Jev/stats sweep in (a).
6. **Blocked bundle.** Gold-bundle JSONL absent. Status is blocked, not a failed rubric. Packs stay out of this run.
7. **No behaviour ship.** This experiment does not install a hook, edit plugin code, or call Jev.

## Draft rubric delta

Judge-facing text, canonical in [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) under “Draft delta — not in force (2026-10-01)”. Short form the re-label must match:

`checkout` is a parent-pull even when the worker still looks busy. If `runaway` is already in the prefix (a path read ≥ 3 times) and the latest interval adds no new path and no Edit/Write, do not treat hidden Bash edits, on-brief re-reads, post-compaction recovery, or empty excerpts as a veto. Mark `runaway` and `low_progress`. The first labeled turn has no delta and is not a frozen interval. The first checkpoint whose delta is frozen (no new path, no Edit or Write) stays `not_yet`. `checkout` starts on the next labeled turn when that turn's delta is frozen too. Stay at `not_yet` when the tail names a checkable step, a new path appears, assistant text has grown, or the worker is waiting on a named job that reports milestones and the histogram already has Write or Edit. Turn count, peak, and compaction count stay insufficient alone.
