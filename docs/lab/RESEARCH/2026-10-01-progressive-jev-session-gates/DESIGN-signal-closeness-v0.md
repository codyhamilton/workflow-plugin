# Design — signal closeness (v0)

> **Draft instrument, not current method:** Start at the [lab results](../../JEV-RESULTS.md) and [active methodology](../../JEV-METHODOLOGY.md). A qualitative float earns a variant sweep only after its underlying signal has shown useful association with an independent outcome. The D0 stop-bar direction below is historical contrast to Cody's proposed continuation-confidence bar.

**2026-10-02 parent-hypothesis clarification:** [`../../JEV-HYPOTHESES.md`](../../JEV-HYPOTHESES.md) H2 puts an empirical signal-outcome test before matcher optimisation. A Jev float measures confidence that a signal is present; it does not itself establish that the signal predicts near useful completion or prolonged continuation. Supported signal floats can later feed a *continuation-confidence* policy with a modest per-round discount. The offline union and D0 stop-bar material below remain unsigned design contrasts; their scale and direction are not silently assumed to implement that policy.

**Date:** 2026-10-02  
**Status:** design intent · measurement / white-paper evidence only · **unsigned** · **not** behaviour ship.  
**Confidence: not high.** Definitions only. No seats, no inventory signature, no GO.  
**Owner:** Workflow System Manager (approach and the offline union). Corpus Ops inventories a family only after a later signature. Trial Runner seats only after that inventory is free.  
**Terms:** [`TERMS.md`](TERMS.md) §15 (this grammar), §12 (decay / leap / accumulate), §11–§14 (shape vocabulary this loop does not replace).  
**Decay schedule to align:** [`DESIGN-progressive-decay-bar-v0.md`](DESIGN-progressive-decay-bar-v0.md) **D0**. **D1** stays the adversarial challenger in [`ADVERSARIAL-progressive-decay-bar-v0.md`](ADVERSARIAL-progressive-decay-bar-v0.md). Neither schedule is adopted as a harness here.  
**Contrast (not the primary instrument of this loop):** interception H1 `(state, question, response-class) → rating → fire` in [`../2026-10-02-interception-steer-to-stop/SIGNAL-CLOSENESS-CONTRAST.md`](../2026-10-02-interception-steer-to-stop/SIGNAL-CLOSENESS-CONTRAST.md).

This note is the durable copy of Cody’s 2026-10-02 measurement guidance. A later reader should be able to run the theory → signal → subset loop from this file. It does not authorise an API call, a harness edit, or a hook.

---

## 1. Thesis

Hard yes/no questions and multi-class labels are a poor primary instrument on muddy workers. They force one bucket when the prefix is a mixture. Wave-2 (section 4) is the evidence for that claim: a blind phase label collapsed, an integer event time came back empty, and a zero-call profile already separated extremes that a live tournament was about to ask a model to separate.

Prefer **float closeness to a set of qualitative signals**.

- Each signal is one qualitative shape (thrash, poll, productive-edit, validation inflection, or a later theorised shape).
- Each signal is scored as **its own float**, judged alone.
- Many signals may ride in **one API call**, as independent asks. Independence means the floats are not a partition: they need not sum to 1, they are not mutually exclusive, and the call must not ask which label wins.
- **Prove or kill each signal on its own** before any variant grid and before any union.
- **Variants come second:** wording and anchors of a signal that survived, crossed with specialised state subsets. There is no single ladder of state that every signal must climb.
- **The aggregator is ours, offline.** Workflow System Manager owns a weighted union of the surviving floats and a fire bar that **discounts once per revalidation round** until leap or kill. The model is not asked for the union, the bar, the leap, or the kill.

`signal_closeness` is a float in **[0, 1]**: 0 is no resemblance to that signal’s written anchor; 1 is a clear instance of it. A later signed inventory may rename the scale. It may not turn the float back into a class label and still call it this experiment.

Hard yes/no, multi-class, integer event time, and a single rating mapped onto fire are **demoted as primary**. They may sit beside a float as a contrast column. They do not enter the union.

---

## 2. Loop the next reader runs

Do these steps in order. Stop at the step whose gate is not met. Stopping is the result. Do not skip to a union, a seat, or a call.

1. **Theorise** a short list of signals from shapes already observed or predicted. The starter list in section 3 is enough to begin. Add a signal only with a one-sentence qualitative anchor and a pre-declared contrast (which kind of prefix should score high, which kind should score low). Write the kill in the same sentence: flat or reversed order on that contrast kills the signal.
2. **Batch independent asks.** One request, one float per signal, each judged alone. The request does not ask for a phase, a class, an event time, a winner, or a union. A missing float on one signal leaves that signal missing. It is not filled from a sibling ask.
3. **Prove or kill each signal alone**, on the cheapest subset that can carry it (section 5). Read each float against its own contrast. Do not average across signals before the kill. A killed wording is not reseated. A repair is a new signal, with a new anchor, and it starts again at step 1.
4. **Then variants, only for survivors.** Cross wording / anchor variants with the state subsets in section 5. Specialise the subset per signal. Escalate to a richer subset only when float quality on the cheaper subset has stalled (the contrast goes flat, or the float cannot see a fact the anchor requires). Record the stall. Do not start on the richest subset.
5. **Union and discount last.** Only after at least one signal has survived steps 3 and 4 may a later inventory open the weighted union and the decaying bar (section 6). That inventory is not this note.

No step above is a seat protocol. It does not name a model, a call budget, a worker panel, or a GO.

---

## 3. Starter signals (theory, not an inventory)

These four are the shapes the 2026-10-02 guidance names. They are unsigned drafts. Any one of them may die at step 3.

| Starter signal | Closeness anchor | Pre-declared contrast (from wave-2 stories, not a seat list) | First subset |
|----------------|------------------|--------------------------------------------------------------|--------------|
| `thrash` | Repeated low-progress tool cycling, already the dominant pattern | Stable early-thrash (ca977 micro: the thrash arm did not flip) versus prefixes that are forward edits | `turn_type_profile` |
| `poll` | Wait, sleep, or poll without forward edits | A poll-shaped worker versus a productive-edit prefix. The validation gate’s `write_count = 1` building labels on `bb6165018de0` are the caution: one write must not force this float down by itself, and must not be laundered into a “building” class | `turn_type_profile` |
| `productive-edit` | Forward writes that change the deliverable, distinct from a reactive fix/test loop | Tool-grounded validation recovered productive-edit building mass (**12/18**) and left thrash at **0/18**. The blind phase label had **0** building, including on productive-edit. This float is a new ask, not a reseat of that label | `turn_type_profile`; escalate only if the profile cannot show the anchor and the float has stalled |
| `validation-inflection` | The trajectory shifts from forward delivery into a reactive read / fix / test loop | Same story as the row above, as a **change** rather than a class. The killed yes/no (“already in validation?”) is not this ask | May skip the profile when the anchor needs prose the profile does not contain. Record the skip, then start at `prompt_plus_last_n` |

A fifth shape may be added the same way. Do not add “time until stop”, “which phase”, or “fire now” as a signal in this panel. Those are the demoted instruments.

---

## 4. Wave-2 lessons this loop must keep

**Source.** Workflow System Manager rollup `registry/ANALYSIS-OUTCOMES-2026-10-02.md` in the corpus-ops tree, with per-join stamps `joins/<name>/WSM-ACCEPT.md` (on disk under `/workspace/corpus-ops/` when that tree is mounted). This repository does not re-stamp those joins. The figures below are that rollup, copied so this loop can be read without the chat.

Wave-2 burn is **closed**. Nothing in the rollup unlocks behaviour ship. The next inventory is **not signed**.

| Case / join | PR | Stamp in the rollup | Lesson for this loop |
|-------------|-----|---------------------|----------------------|
| validation-phase (v1) | #128 | **KILLED** (negative evidence) | **63/63** `in_validation`, **0** `building`, including productive-edit. Blind phase labels collapse. Same question is not reseated |
| tournament-binary-foreshadow | #130 | ACCEPT hygiene; **not policy** | **1/8** fire at confidence **0.18**. Descriptive only. Not a scoreboard and not a float |
| stats-jev-tournament live kill | #131 | **CLOSED** | `zero_call_already_separates` **PASS** (**0** POSTs). Extremes already separate with no model call. Do not open with a prose ask on a contrast a profile already splits |
| adversarial-brittle | #133 | ACCEPT brittleness corpus | Flip rates are real on unclear workers. The registered kill waited for the micro |
| survival-event (v1) | #134 | **KILLED** (vacuous) | **36/36** event times `null`. Agreement and Cox were not estimable. Same question is not reseated |
| ca977-kill micro | #135 | **ACCEPT · kill PASS** | `ca977` `early_thrash` did not flip under the registered arms. Near-empty excerpts still flip unclear workers |
| survival-event v2 | #136 | **ACCEPT · KILL clause 2** | Stage-1 thrash labeling recovered (**5/6** `event_observed`); stage 2 was always null, so **0** valid times. Do not pad this question |
| validation-toolgrounded | #137 | **ACCEPT · kill PASS** | Productive-edit building **12/18** (v1 had **0**); thrash **0/18**; evidence violations **0**. Grounding recovered a mass the blind label had erased |

Reading those rows as design constraints:

1. **Validation collapse.** A hard phase bucket is overconfident when the worker is muddy. The replacement, if one is theorised, is a float with an explicit evidence anchor, proved alone. It is a new signal. It is not v1 asked again.
2. **Survival null times.** Asking for an integer event time failed twice. This loop does not elicit a time. A closeness float is not a survival clock.
3. **Zero-call separation.** If a programmatic turn-type profile already orders the pre-declared contrast, record a zero-call separation and do not spend the request on that signal. The tournament kill is why `turn_type_profile` is first, not a curiosity.
4. **Tool-ground recovery.** Productive-edit mass came back when the judgement was tied to Write/Edit evidence, and thrash did not flood. That supports a grounded float. It does not reinstate a building/validation class as the primary output. The poll caution stays: `bb6165018de0` was **9/9** `building` on `write_count = 1` only, legal under the freeze and still a flood. A tighter rule is a **new** signal, not a patch on the killed question.
5. **Unclear workers stay brittle.** ca977’s thrash arm was stable; near-empty slices still flip unclear workers. A float that only looks decisive on a stripped prefix is not a survival. Say so in the kill note.

Same-question reseat of the killed validation framing and of either survival framing is forbidden. Candidate redesigns that were left unsigned in the rollup (a stage-2 band choice, a tighter poll gate) are not adopted here. A band choice would be another hard elicitation unless someone rewrites it as a float and starts at section 2.

---

## 5. State subsets

Specialise per signal. Cheap subsets first. Escalate only when float quality stalls.

| Id | What the ask is allowed to see | When it is the right first look |
|----|--------------------------------|---------------------------------|
| `turn_type_profile` | A programmatic array of turn types only (`think`, `bash`, `read_file`, `write_file`, and the other observed types). Minimal or no prose. Built offline, before any model call | Default first look. Also the place a zero-call separation is recorded, in which case the model is not called for that signal |
| `last_n_assistant` | The last **N** assistant turns and nothing earlier. **N** is a variant axis for a signed ablation, not a number frozen here. Start from a small N | After the profile stalls, or when the anchor is about recent assistant behaviour the profile cannot express |
| `prompt_plus_last_n` | The opening system/user prompt (the brief) plus the last N assistant turns | When the signal is closeness to the brief, not only to recent tools |
| `all_user_prompts_plus_last_n` | Every user message in the prefix, plus the last N assistant turns. No earlier assistant prose | When later user redirects are part of the anchor and the single opening prompt is not enough |

Rules:

- One signal does not inherit another signal’s subset just because both were in the same request.
- Richer state is a cost. It is earned by a stall on the cheaper subset, written down, not by habit.
- Maps transcripts only, until a separate non-maps capture is unblocked. Leave the local `:8080` server unloaded.
- Building a `turn_type_profile` is not a Jev call and is not `--call-jev`. Scoring a float still waits for a signed inventory.

---

## 6. Offline union and discount-to-kill

This section is the contract for a **later** draft, family name `PR-DECAY-ACCUM`. It is not runnable from this note.

**Who computes it.** Workflow System Manager, offline, after the floats exist. The model does not return a union, a weight, a bar, or a fire bit.

**Union.** A weighted combination of the floats that survived section 2. Weights are declared before the kill outcomes for that round are read. A missing float is not imputed by the model. The numeric weights, and whether a missing float is dropped or treated as zero, are part of the signature this note does not give.

**Discount.** Once per revalidation round the fire bar drops, until the union **leaps** (clears the current bar with the qualitative shape the surviving signals were built for) or the run is **killed** (the policy stops the counterfactual worker). Round index and checkpoint grid stay the progressive schedule: first look at turn 75, then every 15 turns ([`TERMS.md`](TERMS.md) §2, §12).

**Align D0.** The registered discount to compare against is schedule **D0** in [`DESIGN-progressive-decay-bar-v0.md`](DESIGN-progressive-decay-bar-v0.md):

| Round `k` | Checkpoint turn | D0 `t_k` |
|-----------|-----------------|----------|
| 0 | 75 | 3 |
| 1 | 90 | 3 |
| 2 | 105 | 2 |
| 3 | 120 | 2 |
| 4+ | 135, 150, … | 1 |

**D1** (evidence-gated lowering, no earlier than 105, floor 2, with floor-1 challenger `D1-F1`) remains a proposed comparison from the adversarial pack. `PR-DECAY-ACCUM` may compare D0 and D1. It does not replace D0 inside the decay design, and it does not ask the model to choose a schedule.

**Scale join, deliberately open.** A union in **[0, 1]** is not `checkout_confidence` on {0, 1, 2, 3}, and D0’s `t_k` is that confidence bar. Plugging the union into `t_k` without a declared map would pretend the scales are the same object. The map (a threshold on the union, or an explicit function onto `t_k`) has to be written in the signature that opens `PR-DECAY-ACCUM`. This note does not choose it.

**Leap and accumulate** keep the [`TERMS.md`](TERMS.md) §12 meanings, with the union in place of a single checkout score: leap clears the current bar because the shape agrees; accumulate holds, and the next round uses the next lower bar. Calendar decay without persistent signal mass is exactly the D0 property the adversarial pack already flagged. Comparing D1 does not silently rewrite D0.

---

## 7. Draft case families (unsigned)

Names for a later Corpus Ops inventory. **No seat protocol. No GO. No claim that a family is frozen or ready to run.**

| Draft family | What it would contain, once signed | Gate before anyone signs it |
|--------------|------------------------------------|-----------------------------|
| `PR-SIGNAL-CLOSENESS` | The atomic multi-ask float panel: one request, independent floats, per-signal prove/kill on the first subset | This note’s section 2 steps 1–3 written as an inventory. Not written here |
| `PR-SIGNAL-STATE-ABLATION` | The grid of surviving signals × wording/anchor variants × section 5 subsets | At least one signal survived `PR-SIGNAL-CLOSENESS` on its own contrast. A flat signal does not enter the grid to be rescued |
| `PR-DECAY-ACCUM` | WSM weighted union plus a D0-versus-D1 discount-to-kill comparison | Signals have earned a signature, and the [0, 1] ↔ `t_k` map is in that signature. The rollup’s deferred “DECAY-ACCUM (WSM harness)” item is this family **still unsigned**, not a harness to build now |

Order is the table order. Ablation does not start in parallel with the first prove/kill. Decay does not start in parallel with ablation.

---

## 8. What stays contrast

| Instrument | Where it lives | Role after this note |
|------------|----------------|----------------------|
| Fixed bar `P0`, `confidence_min = 3` | [`TERMS.md`](TERMS.md) §§3, 9 | Unchanged sweep cell. Not the live discount |
| D0 / leap / accumulate | [`DESIGN-progressive-decay-bar-v0.md`](DESIGN-progressive-decay-bar-v0.md), [`TERMS.md`](TERMS.md) §12 | The discount this union is meant to feed. Harness still closed |
| D1 / D1-F1 | [`ADVERSARIAL-progressive-decay-bar-v0.md`](ADVERSARIAL-progressive-decay-bar-v0.md) | Challenger schedules. Not adopted |
| Validation yes/no at ~50/60/75 | [`TERMS.md`](TERMS.md) §13, decay design §3 | 2026-10-01 handoff sketch. Demoted as a **primary measurement** after the v1 collapse. Not deleted, not reseated |
| H1 rating → fire | [`../2026-10-02-interception-steer-to-stop/H1-DETAIL.md`](../2026-10-02-interception-steer-to-stop/H1-DETAIL.md) | Contrast for this loop. The interception white paper’s recorded bake-off order is not rewritten by this file |
| Shape-signal and full-maps qual panels | [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md), [`TERMS.md`](TERMS.md) §§11, 14 | Existing qualitative vocabulary. This loop does not relaunch those seats and does not treat their labels as floats |

---

## 9. Non-goals

- No behaviour ship, no hooks, no `additionalContext`, no plugin or driver edit.
- No `--call-jev`, no stats-gate sweep, no live fan-out, no local `:8080` load.
- No same-question reseat of killed validation-phase or survival-event framings.
- No seat protocol, no call budget, no worker panel, no GO, no Corpus Ops signature.
- No model-emitted union, kill, or fire bit.
- No use of a retired hold phrase as a behaviour gate. Behaviour ship stays closed because this note is measurement design, not because a hold label was applied.
- Maps only, unless a separate non-maps capture is unblocked.
- No edit to `gate_thresholds.py`, replay decision code, or the P0 grid.

---

## 10. Traceability

| Need | Path |
|------|------|
| Vocabulary | [`TERMS.md`](TERMS.md) §15 |
| Where the loop sits among experiments | [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) — `signal-closeness-v0` |
| D0 table and handoff sketch | [`DESIGN-progressive-decay-bar-v0.md`](DESIGN-progressive-decay-bar-v0.md) §2.2, §3, §8 |
| D1 challenger | [`ADVERSARIAL-progressive-decay-bar-v0.md`](ADVERSARIAL-progressive-decay-bar-v0.md) |
| H1 rating → fire as contrast | [`../2026-10-02-interception-steer-to-stop/SIGNAL-CLOSENESS-CONTRAST.md`](../2026-10-02-interception-steer-to-stop/SIGNAL-CLOSENESS-CONTRAST.md) |
| Wave-2 rollup (outside this repo) | corpus-ops `registry/ANALYSIS-OUTCOMES-2026-10-02.md` |
| Per-join stamps (outside this repo) | corpus-ops `joins/*/WSM-ACCEPT.md` |

**Version:** v0 — design note only. Bump the version id if the float range, the subset list, or the D0 alignment changes.
