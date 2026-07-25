# Case Study: Is the `iterate` skill worth its cost?

## 2026-06-26 — Deep analysis of the garcia-music player/stem run

This builds on the process trace in [`2026-06-25-garcia-music-iterate.md`](./2026-06-25-garcia-music-iterate.md).
That document answered *what happened* and *where alignment broke*. This one answers the
questions that determine whether the skill is worth keeping: **did it produce qualitatively
valuable output, what did it cost, and how hard was it to find out?**

- **Session**: `87e55915-f481-4dcc-8b6a-54c69392fcf9` — `~/workspace/garcia-music`
- **Skill**: `iterate`, autonomous run, 4 cycles, 10h 58m, 67 subagents, 11 candidates built
- **Artifacts read for this study**: the six candidate branches' registry, all four cycles'
  `JUDGEMENT.md` / `NEXT.md`, the living `OUTCOMES.md`, and the in-window slice of
  `usage-events-2026-06-26.csv`.

---

## Verdict

**The skill earned its cost on output quality, and the run is reproducible end-to-end from the
toolkit. The weak link is *cost attribution*, not the skill: there is no join key from a usage
event to a session, and no dollar figure exists at all.** The expensive failures the prior
analysis flagged were all front-loaded in cycle 01 *before the briefs were added to the skill
mid-run* (see [§5, the briefs natural experiment](#5-the-briefs-natural-experiment)); cycles 02–04
ran clean. The judgement, harvest, and outcome artifacts are real design reasoning, not ceremony —
this is the part a process-only trace cannot see, and it is the part that justifies the 82M tokens.

One unresolved integrity note (see [Discrepancies](#discrepancies)): `iteration-01/JUDGEMENT.md`
states the cycle was instructed to *stop after synthesis*, yet a consolidation commit
(`0205798`) exists. The artifact and the git history disagree about what the orchestrator was
told.

---

## 1. Did it produce qualitatively valuable output?

Yes — and this is the headline the process trace missed by staying above the artifacts. Four
pieces of evidence, each checkable:

**The synthesis judgement is design-altitude, not code review.** `iteration-01/JUDGEMENT.md`
selects `c08` (the page-architecture restructure) over five rivals on *one-way-door* grounds —
"sleeve sanctity," "page-architecture headroom," "metaphor durability across 500 listens" — and
explicitly rejects the more spectacular candidates (`c02` orbit, `c04` peel) *because* their
novelty fatigues. That is exactly the "rough build of a superior approach beats a polished build
of a dead end" altitude the skill's Reasoning section demands. It then harvests six concrete ideas
from losing branches, each with a **file + line-range code pointer** (e.g. c05's solo/restore at
`StemChamber.svelte:80–130`). A reviewer can act on this directly.

**The yardstick actually moved.** `OUTCOMES.md` is revised every cycle and the revisions are
substantive, not cosmetic: 7 emergent criteria after cycle 01 → editorial-vs-annotation split
added in cycle 02 → transmedia-bridge criteria (§13–§18) in cycle 03. The "criteria are discovered,
not declared" thesis is observable in the diff of a single file across four commits. The cycle-03
revision even re-frames the long horizon ("from 'the rail annex is the attachment point' to a
sharper posture about linkage granularity") — the spec sharpening against built reality, as designed.

**The divergence bar rejected real work.** Two challenger plans (`c06` Stem Underline, `c07` Stem
Weft) were gated out as "safe union" with already-built candidates and never built — the registry
records the disposition and the harvest. The bar's intended teeth ("I cannot find a genuine fork
is the valid answer") fired in production, twice, and prevented two redundant build cycles.

**The loop terminated cleanly.** `iteration-04/NEXT.md` declares the program stop explicitly,
auto-selects nothing, and leaves three separable, genuinely-next steps (Gallery bridge,
audio/video coexistence, Session-tab gating) measured against `OUTCOMES.md` rather than the
original prompt. No infinite loop, no invented winner. Judgement depth *increased* across cycles
(176 → 198 → 253 lines), so quality did not decay as context grew.

**Caveat on realized value:** all eleven candidates and four consolidations live on
`iterate/player-stem-c08` and sibling branches. **None of this has merged to `master`.** The
output is valuable as *reified design provenance and a chosen foundation*; it has not yet been
cashed as shipped product. That is consistent with the skill's "losing branches are never deleted"
provenance model, but a reader weighing cost-vs-value should know the 82M tokens bought a
decided direction and six preserved alternatives, not a deployed feature.

---

## 2. What did it cost — and can you find out easily?

Short answer: **token volume is recoverable to ~97% confidence by timestamp; dollar cost is *not*
in the CSV but is reconstructable from published per-model rates (`pricing.json`); and there is no
programmatic link from the bill to the session.**

### The numbers (in-window slice, 06-25 12:37–23:37)

| Model | Tokens | Events |
|-------|--------|--------|
| composer-2.5 | 46.3M | 65 |
| glm-5.2-high | 23.6M | 57 |
| claude-4.6-sonnet-high-thinking | 10.0M | 7 |
| composer-2.5-fast | 2.1M | 2 |
| gemini-3.5-flash | 0.5M | 1 |
| **In-window total** | **82.5M** | **132** |

Only `composer-2.5-fast` and `gemini-3.5-flash` (3% of window tokens) are *not* models the iterate
session used per the transcript. So for a run this size, the 11-hour timestamp window is a
**clean-enough proxy** — the prior analysis was over-cautious calling the per-model totals
"approximate." Roughly **7.5M tokens per built candidate**, or ~20M tokens per cycle.

### What it would actually meter at (Cursor published rates, `pricing.json`)

The subscription hides the bill, but `cost_window.py --pricing` reconstructs it. The whole 11-hour
run would meter at **~$29.50**, and the split is the real story — cache read, the cheapest-priced
bucket, is **65–70% of the dollar cost** on the two bulk models:

| Model | $ total | cache_read | fresh_in | output | cache_rd % | output % |
|-------|--------:|-----------:|---------:|-------:|:----------:|:--------:|
| composer-2.5 | 12.26 | 8.55 | 2.02 | 1.69 | **70%** | 14% |
| glm-5.2-high | 8.71 | 5.65 | 2.29 | 0.76 | **65%** | 9% |
| sonnet-thinking | 6.80 | 2.80 | — | 1.85 | 41% | 27% |
| **Total** | **29.50** | | | | | |

The thing you *want* (output) is 9–14% of spend; the thing you're paying for is re-reading
accumulated context. This confirms the §1 verdict from the cost side: model selection should be
driven by **cache_read price**, because output is ~1% of token volume everywhere and so output
price almost never moves the bill. The lever is built into the tool — running GLM's tokens at
`kimi-k2.5` rates (`--substitute glm-5.2-high:kimi-k2.5`, cache read $0.26→$0.10/Mtok) cuts that
line **58%** ($8.71→$3.67) and the session 17% ($29.50→$24.47), with no quality cost on a role
(orchestration) whose output doesn't matter.

### Three structural facts that make cost-tracing hard

1. **No join key.** The CSV's `Cloud Agent ID` and `Automation ID` columns are **100% empty**
   across all 230 rows. There is no field that links a usage event to session
   `87e55915`, to a cycle, or to a subagent. Timestamp correlation is the *only* method, and it
   degrades the moment two sessions overlap in time.

2. **No dollars in the export.** The `Cost` column is `Included` (197 rows) or `Free` (31 rows) —
   never an amount; the subscription doesn't meter you. But the dollar figure is *more* valuable
   than a CSV total would be: computing it from published per-model rates (`pricing.json`) splits
   spend into cache_read / fresh_in / cache_write / output, which is what tells you *where* the
   money goes (cache read) and *which knob moves it* (model cache_read price, not output price).
   `cost_window.py --pricing` does this; rates are edited in one JSON as Cursor changes them.

3. **Event count ≠ agent count.** glm-5.2-high shows **57 billing events** but the transcript has
   only **5 glm task calls** (the synthesis/orchestrator agents). One agent emits many usage events
   (one per turn), so you cannot map events→agents 1:1. Per-model *token totals* survive this;
   per-agent attribution does not.

The honest summary a reader needs: *this run consumed ~82M tokens over ~11 wall-clock hours under
a subscription that did not meter it in dollars; you can attribute that to the session by
timestamp with ~97% confidence only because it was the day's dominant activity.*

---

## 3. How good is the tooling we built for this?

**Strong on the transcript side, silent at the cost boundary.** The case study above was produced
almost entirely from three commands, with no bespoke parsing:

```bash
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music > session.json
cat session.json | python3 tools/cursor/stats.py
cat session.json | python3 tools/cursor/iterate_analysis.py
```

What worked with zero friction:
- `find.py` → `extract.py` → `stats.py`/`iterate_analysis.py` is a clean pipe; the extract JSON is
  a good primitive (cache once, analyze many).
- `iterate_analysis.py` phase classification and cycle detection matched the artifacts on the
  ground — the 4 cycles, the gate rejections, the prompt-degradation curve all reproduced exactly.
- It correctly surfaced the alignment issues (orchestrator-absorbed planning, wrong models,
  synthesis-repeated) that pointed me at the right places in the transcript.

Where it left manual work — all of it at the **cost boundary**:
- **No cost tool.** Nothing in `tools/cursor/` touches the usage CSV. Bridging session→tokens was
  hand-written awk/python against a window I computed by eye from `extract.py`'s start/end times.
  This is the single biggest gap, and the prior analysis hit it too ("No cost data from transcripts").
- **`python` vs `python3`.** The README examples say `python`; the environment only has `python3`.
  Minor, but it stops a copy-paste cold.
- **Phase edge cases** the README already documents (post-review fix tasks classified as `review`)
  held true; not a defect, but worth the manual check it warns about.

### The fix, now built: `cost_window.py`

`extract.py` already computes `start_time_iso`/`end_time_iso`. The new
`tools/cursor/cost_window.py` takes that window + the usage CSV and turns the entire cost half of
this case study into one more pipe stage:

```bash
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music | \
  python3 tools/cursor/cost_window.py --csv usage-events-2026-06-26.csv
```

It auto-derives the window from the piped session, attributes tokens per model, and — by comparing
in-window models against the models the session actually used (from its Task calls) — flags
**foreign models** and prints an attribution-confidence figure. On this run it reports the
table in §2 plus *"~96.9% of window tokens belong to models this session used"* and labels
`composer-2.5-fast` / `gemini-3.5-flash` as foreign. It cannot invent a join key or a dollar figure
the data lacks, but it makes the timestamp-correlation method one command instead of a manual awk
session and tells the analyst how far to trust the window. It also has an explicit `--start/--end`
mode (no session list, so foreign-flagging is off — it says so). This was the highest-leverage
tooling change available, and it is the reason the cost section above was cheap to produce.

---

## 4. Advice for tweaking

### Skill (`iterate`)
- **The cycle-01 failures were a missing mechanism, not a misbehaving orchestrator — and the fix is
  already proven** (see §5). Cycle 01 ran on the briefs-less skill version; gate prompts degraded
  1199→213 chars because the orchestrator was *paraphrasing inline guidance under context pressure*,
  exactly the failure the skill's "pass briefs verbatim" rule exists to prevent. The briefs were
  added mid-run and cycles 02–04 held at 2800–3700-char gates. The forward lesson is small: the
  mechanism works, so **guard it** — a step-0 assertion that `briefs/` exist and are passed verbatim
  before any gate/synthesis dispatch would have prevented the entire cycle-01 degradation.
- **Model-selection drift recurred** (wrong review model in cycle 03; wrong synthesis model in
  cycle 04, both user-corrected). The orchestrator should treat model choice as a verbatim
  contract per phase (composer for build/review, GLM for synthesis), the same way `briefs/` are
  passed verbatim. This is cheap insurance against the most expensive single event in the run (the
  6.3M-token sonnet review burst at 22:22).
- **Close the artifact↔git loop.** The `JUDGEMENT.md`-says-stop / consolidation-commit-exists
  discrepancy means the artifacts are not a faithful record of what the orchestrator did. Have the
  consolidation step stamp the artifact with the commit it produced (or its absence), so the doc
  and the history cannot silently diverge.

### Tooling
1. ~~Add `cost_window.py`~~ — **done** (this study; see §3). Biggest leverage.
2. ~~Fix README `python` → `python3`~~ — **done** (all 27 invocations).
3. Still open: have `iterate_analysis.py` optionally emit the **gate prompt_len curve per cycle**
   as a first-class signal — it was the cleanest leading indicator of the cycle-01 degradation and
   is worth surfacing without the manual table.

---

## 5. The briefs natural experiment

The most useful thing this run accidentally produced is a **clean before/after of a skill change**,
because the skill was edited *while the run was in progress*. This is the strongest evidence in the
study, and it is causally clean — the boundary is a single commit at a known time.

**Timeline (all UTC):**

| Time | Event |
|------|-------|
| 12:37 | Session starts; cycle 01 runs on the **briefs-less** skill (`d8ccfcf`, 175-line SKILL.md, guidance inline, "judge" terminology) |
| 12:37–13:42 | Cycle 01 gates degrade **1199 → 213 chars** across 7 gate agents; first synthesis attempt is incomplete |
| **13:44** | Commit **`a857409`** — *"refine agent direction and judge → synthesis"*: adds the 3 `briefs/` files, moves drift-sensitive guidance out of SKILL.md into verbatim-passable briefs, renames judge→synthesis (14 → 2 "judge" mentions) |
| 13:48 → 23:36 | Cycles 02–04 run **with briefs**; gates hold at **2833 / 3716 / 3122 chars** |

**The split is mechanical:** 23 of the 67 subagents finished *before* `a857409`, 44 *after*, and the
boundary lands exactly at the cycle-01 synthesis step. Every degraded gate predates the briefs;
every consistent gate postdates them. The two "alignment issues" the prior trace flagged as
orchestrator failures — `prompt-degradation` and `synthesis-repeated` — are precisely the
**failure signature of the briefs-less version**, and the first synthesis-repeated event straddles
the commit (v1 briefs-less and incomplete → v2 under the new `briefs/synthesis.md`).

**What this is evidence *for*** — the skill's own central thesis: *pass drift-sensitive context to
subagents verbatim rather than paraphrasing it.* Inline guidance is something the orchestrator
re-derives and compresses each time it dispatches (hence the 1199→213 decay); a brief is a fixed
artifact it passes unchanged (hence the flat 2800–3700 across three later cycles). The mechanism
converted gate direction from *decaying* to *durable*.

**Honest confound:** the user also gave verbal corrections (msgs 32, 38) at the same boundary, so
"briefs" and "user told it to recheck" cannot be fully separated for the *next* message. But a
verbal correction decays as context grows, while a brief is re-passed every cycle — so the
*sustained* quality across cycles 02–04 (not just the next step) is better explained by the
structural change than by a one-off nudge. That is the load-bearing observation, and it is what
makes the briefs change look like a real, durable improvement rather than a lucky correction.

---

## Discrepancies

- **Consolidation vs. "stop after synthesis."** `iteration-01/JUDGEMENT.md` (lines 5–6) says the
  user instructed cycle 01 to halt at synthesis, but commit `0205798`
  ("consolidate iteration 01 stem harvest onto c08 atelier") and the cycle's `consolidation-plan`
  / `consolidation-execute` phases show consolidation ran. Either the instruction was overridden
  after the judgement was authored, or the artifact was written in a re-run. Unresolved; flagged as
  a traceability gap, not adjudicated.
- **glm event/token footprint** (57 events, 23.6M tokens) is far larger than its 5 task calls
  imply. Consistent with the orchestrator itself running on glm and synthesis agents being
  token-heavy, but the data cannot confirm which — another consequence of the missing join key.

## Reproduce

```bash
cd ~/workspace/workflow-plugin
python3 tools/cursor/extract.py 87e55915 ~/workspace/garcia-music > /tmp/session.json
cat /tmp/session.json | python3 tools/cursor/stats.py
cat /tmp/session.json | python3 tools/cursor/iterate_analysis.py
# Qualitative artifacts (in the target repo):
cd ~/workspace/garcia-music
sed -n '1,90p' 'docs/plans/[NEW]-player-stem-iteration/iteration-01/JUDGEMENT.md'
sed -n '1,60p' 'docs/plans/[NEW]-player-stem-iteration/OUTCOMES.md'
git branch --contains 0205798   # shows iterate work is NOT on master
```
