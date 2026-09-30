# Strategy pass — 2026-09-30

**Author:** Workflow Optimiser (Grok strategy pass)
**Inputs:** `docs/lab/` research and proposals, `tools/transcript/classify.py` + `lib/snapshot.py` + `lib/jev_client.py`, eight live rows in the attached `classify-log.jsonl` (2026-09-30T04:08:57Z, model `jev-1.13.0`).
**Decision:** do **not** promote any of the five proposals to implementation. No skill or classify behaviour change in this pass. The next work is measurement hygiene.

---

## 1. What the eight rows actually say

All eight calls landed in ~1.4s with `output_tokens` fixed at 110. Treat that as schema size, not a quality signal. `human_label` is null on every row.

### Choice (`session_kind`)

| prefix | source | choice | conf | top prob | runner-up (prob) | margin |
|--------|--------|--------|------|----------|------------------|--------|
| d006f5a0 | claude | workflow | 0.82 | 0.84 | build 0.13 | 0.71 |
| af9b5cb1 | claude | build | 0.73 | 0.76 | workflow 0.23 | 0.53 |
| 30844998 | claude | workflow | 0.85 | 0.87 | build 0.13 | 0.74 |
| bd4f6c0d | claude | plan | **0.30** | 0.37 | build 0.31 (workflow 0.29) | 0.06 |
| 1dc10dd4 | cursor | ops | 0.93 | 0.95 | workflow 0.04 | 0.91 |
| 77572779 | cursor | ops | **0.45** | 0.50 | question 0.23 | 0.27 |
| a2be9531 | cursor | workflow | **0.62** | 0.66 | review 0.25 | 0.41 |
| eac38429 | cursor | question | **0.41** | 0.48 | research 0.24 (ops 0.20) | 0.24 |

Published `confidence` tracks the top probability (a few points lower). It does **not** equal the margin. Three of eight rows clear 0.8 (37%). That is a review-budget knob, not a calibrated accuracy threshold. An 80% agreement claim on the three high-confidence rows is not a measurement.

`mixed` has probability **0.0 on all eight rows**, including `bd4f6c0d`, where plan/build/workflow sit at 0.37/0.31/0.29. The instruction “use mixed when two kinds are roughly equal” is not what the model does. Ambiguity shows up as a split across specific labels. Do not use `mixed` as the safety valve, and do not add another numeric gate (a margin cutoff fit on n=8 would repeat the uncalibrated 0.8).

**Taxonomy collisions, in the order the log shows them:**

1. **workflow ↔ build ↔ plan.** Workflow mass ≥ 0.10 on six of eight rows. On Claude, workflow is top or second on three rows and third at 0.29 on the tie. The criterion (“running or tuning the iterate/lab workflow itself”) collides with ordinary plan/build when the *subject* is this plugin. That is a label problem, not a reason to merge kinds with `iterate_analysis.py` phases.
2. **question ↔ research ↔ ops.** `eac38429` and `77572779` split across “looking” and “environment” with no dominant residue.
3. **workflow ↔ review.** `a2be9531` puts 0.25 on review under a workflow top label.

Keep the eleven labels until blind labels exist. The revision trigger is in §5, not a preemptive taxonomy edit.

### Score (`workflow_alignment`)

Score confidence maxes at **0.70** (mean ~0.57). A 0.8 gate on Score would auto-accept nothing. The low confidence is often an adjacent-bin split, not a claim that the session is ad-hoc:

- `30844998`: kind confidence 0.85, score 2.46, score confidence 0.46, with P(2)=0.47 and P(3)=0.50. The expected score is the useful summary; the confidence flags a boundary between “mostly on-rails” and “tight”.
- `1dc10dd4`: score 1.47, P(1)=0.50, P(2)=0.47.

Mean score is 2.28 on the Claude half and 1.16 on the Cursor half. That gap matches **kind mix** (workflow/build/plan versus ops/question), not a demonstrated parser bug. Do not explain it as newline distortion, and do not use alignment as a cross-source KPI.

There is no `human_alignment` field. `human_label` can calibrate kind only. Until a human 0–3 exists, Score stays a descriptive column.

### Snapshot tokens

Cursor `input_tokens − snapshot_token_estimate` is **728, 725, 729, 728**. The questions JSON is ~333 chars/4; the rest is API wrapper. Call the constant **~728 tokens of non-state overhead**.

Claude state-implied tokens `(input − 728) / snapshot_token_estimate` are **1.82, 1.99, 1.85, 1.94** (mean **1.90**). Cursor state-implied tokens match the chars/4 estimate within a handful of tokens. Same questions, same model: the Claude *state* tokenizes at about twice the estimator’s density. That is high-confidence evidence of a payload difference. It is only medium-confidence that the mechanism is newline-per-character joining: `_extract_user_queries` does `"\n".join` on content blocks, which is correct for normal blocks and pathological only if blocks are single characters. Reproduce with a text dump before any parser change (§5, move 1).

---

## 2. Research takeaways — strong, weak, missing

Source: `RESEARCH/2026-09-30-workflow-systems.md` and `RESEARCH/INDEX.md`. The INDEX confidence column mixes “the paper says this” with “therefore change a skill.” Split those. Analogies can stay; they are not eval results.

### Strong (keep, and let them constrain the backlog)

- **ACI is the product** (SWE-agent). Skills, brief shape, and `Workflow-Phase:` trailers are the interface. Transcript tools are how interface changes become visible. This justifies classify and harvest. It does not justify new orchestration.
- **Inference separated from grading** (SWE-bench). A scenario without a verifier is a demo. Grading is the harness or a human rubric, not another agent in the same context.
- **Jev is for closed labels over compact state**, not for compiling or for judging code correctness. Batching Choice + Score in one request is the right shape. The review gate (low confidence → human) is the right *policy shape*.
- **Evaluator–optimizer is already the plugin** (`comprehensive-review`, remediation, `evals/`). Jev classify is a different layer: session behaviour, not outcome correctness. The deep-dive table says this; the assertion-spike proposal forgets it.
- **No HITL inside `execute` for cloud.** Matches the core plugin rule. Leave it as a non-goal.
- **Session kind stays orthogonal to iterate phase regex** until labels settle. Open question 2 is answered for now: stay orthogonal. `agree_with_iterate_phase_mode` is the wrong column to optimise; phase mode and session kind are different questions.

### Weak (do not let these drive builds)

- ReAct → “design contexts should minimise tool thrash” is taste. No trajectory sample in this repo has tested it. Do not turn it into a skill edit.
- AutoGen’s event/actor note is a watch-item. It is the weakest justification on the page for building `tools/driver/`. GOALS already lists a mandatory driver as a non-goal this quarter; the backlog must match.
- Open question 3 (repair inside `execute` versus bounce to `refine`) is a behaviour change. Park it. Research should not keep it on the proposal runway while the remit is measure-first.
- “High confidence” on orchestrator–worker mappings restates the architecture. Useful as orientation, not as a finding.

### Missing

- **How to evaluate the evaluator.** No sample-size floor, no separation of kind labels from alignment labels, no mention that `mixed` can be a dead criterion. The 0.8 / 80% pair is stated as policy before a single human label.
- **Confounding.** “Workflow” as subject-matter versus “workflow” as phase discipline, and source versus kind mix on the alignment score. Both are visible in the eight rows and absent from the research note.
- **Deterministic checks versus typed judges.** Heading presence, trailer presence, and “does IMPLEMENTATION.md list a verification line per phase?” are schema checks. Spending a Jev calibration cycle on them is the wrong layer.
- **Variance already admitted by `evals/README.md`.** One frozen baseline cannot carry a hypothesis verdict. The research cites SWE-bench `run_id` hygiene and skips that sentence.
- **The observational route the README already specifies** for hypotheses 1, 4, 6, and 8. The bibliography over-weights a harness and under-weights harvest. `docs/analysis/2026-09-08-workflow-vs-field.md` already gives hypothesis 8 a partial observational verdict (quadratic cost supported; “nearly always cheaper” unsupported; 40–75 turns is a crossover, not an optimum). That is sitting unused by GOALS.

---

## 3. The five proposals

| Proposal | Verdict | Why |
|----------|---------|-----|
| Classify human-label workflow | **Right process, wrong success bar.** Keep proposed. | Blind labels are the bottleneck. “≥10 labeled rows” cannot be met from eight rows, and 80% at confidence ≥ 0.8 is not computable yet. Run the eight as a pilot. Do not build a labeling tool; a jq merge is enough when labels exist. |
| Claude snapshot text join | **Right suspicion, unconfirmed mechanism.** Keep proposed. Do not start the patch. | The 1.9× density gap is real. The join-on-blocks code path does not by itself prove newline-per-character. A dump is the whole first step. Kill the join hypothesis if the dumped user text is readable prose with a normal newline ratio; the density gap would then still need another explanation before cross-source token comparisons. |
| First eval scenario | **Mis-aimed.** Keep proposed. Do not run it. | Empty `evals/scenarios/` is true. Choosing “a documented plan under `docs/plans/`” contradicts the research’s own SWE-bench line: pin an external repo and commit, and name a verifier. An in-repo self-solve has no independent outcome. One run also cannot support a verdict under the harness README’s variance rule. A frozen baseline is a milestone, not a result. |
| Jev hook assertion spike | **Defer.** Keep proposed. | It invents “Score ≥ 2.5” the same way classify invented 0.8, one layer too early, on a question a deterministic read of `IMPLEMENTATION.md` / `DESIGN.md` can answer. Revisit only when someone names a semantic check that a schema cannot do, and only after kind calibration exists. |
| Archive spike design | **Hygiene, not a measurement step.** Keep proposed. | Code constants are the taxonomy source of truth. This strategy note covers the decision-relevant subset (labels, gate, log schema gaps). Do not block the three moves below on a design-doc merge. |

Nothing here is promoted to implementation.

---

## 4. Focus windows

Windows are attention order, not effort estimates.

### First window — make the ruler honest

1. Snapshot parity dump (move 1).
2. Blind kind labels on these eight rows, reported split by the provisional 0.8 line (move 2).
3. No new classify batch for pooled metrics until (1) returns. New rows, if someone runs them for another reason, stay tied to `snapshot_hash` and are not pooled with post-fix rows.

### Second window — one honest hypothesis status, and a scenario decision

4. Hypothesis ledger for the eight README hypotheses (move 3). Record hypothesis 8 as **observational-partial** from `docs/analysis/2026-09-08-workflow-vs-field.md`, and state the still-open piece: per-phase orchestrator turn and context counts from cloud `IMPLEMENTATION.md` records, which the README named and nobody has tabulated.
5. First-scenario decision: write `source.md` only if an **external** repo, pinned commit, and verifier can be named. Otherwise kill “in-repo plan as the first scenario” in FINDINGS and leave the corpus empty on purpose.
6. If move 1 confirms a parser bug, that fix is the first code change allowed. Re-classify the same four Claude session ids; compare `snapshot_hash` and token estimate. Do not retune labels that were collected against the old hash.

### Third window — one baseline, or stop pretending the harness is the metric

7. If an external spec survived, run **one** baseline and freeze it. The comparison files for that run say “first run, no baseline” in substance even if the folder copy exists. A verdict waits on a later candidate plus the variance caveat.
8. If no verifier could be named, measurement stays observational. Do not invent a self-scenario to satisfy the “non-empty baseline/” cell.
9. Still no artifact-level Jev hook, no driver MVP, no live per-turn gating.

---

## 5. Next three moves

### Move 1 — Snapshot parity diagnostic

**Why.** Cross-source token comparisons are invalid while Claude state tokenizes at ~1.9× the chars/4 estimate and Cursor matches it. Alignment scores are a separate issue (kind mix); this move does not “explain” them.

**How.** On one Claude session and one Cursor session from the eight, dump `first_user_message` length, newline count, and whether a human can read it. Record `(input_tokens − 728) / snapshot_token_estimate`.

**How we’ll know.** A FINDINGS paragraph with a binary mechanism verdict.

**Kill.** If newline ratio and readability look like normal prose, kill the join-bug proposal’s mechanism. Leave the density gap open as a new question rather than patching `claude.py` on a hunch.

### Move 2 — Blind kind labels on the eight rows

**Why.** Every accuracy number downstream is blocked on `human_label: null`. The tie on `bd4f6c0d` and the dead `mixed` criterion are the taxonomy facts labels will confirm or overturn.

**How.** Label from the taxonomy in `lib/jev_client.py` without opening `answers` first. Store by `session_id` + `snapshot_hash`. Kind only in `human_label`. Optional human alignment 0–3 goes in `human_notes` as `align=<n>` so we do not pretend Score is calibrated; do not add a code field in this window.

**How we’ll know.** A FINDINGS table: agreement on the three rows with confidence ≥ 0.8, and separately on the five below. The pilot succeeds by being published. It does not succeed by hitting 80%.

**Kill / revise.** If the labeler cannot assign a single dominant kind on **three or more** of the eight rows, the taxonomy is too overlapped to support auto-metrics. Revise criteria (likely workflow-as-subject versus workflow-as-discipline, and question versus research) before any larger batch. If high-confidence agreement is worse than 2/3, drop the idea that ≥ 0.8 is an auto-metric and keep every row human-gated.

**Claim rule (later, not now).** The GOALS 80% line becomes claimable only with **≥ 10 labeled rows at confidence ≥ 0.8**, on one snapshot generation. At today’s 3/8 pass rate that is on the order of thirty classified sessions. Do not collect them before move 1.

### Move 3 — Hypothesis ledger, and kill or replace the in-repo first scenario

**Why.** The cheapest true GOALS hit is an observational status, not a full workflow run. Hypothesis 8 is already argued. The first-eval proposal, as written, would spend a high-variance run on a task with no independent verifier.

**How.** Eight-row ledger: hypothesis, route (eval / observational), status (`untested`, `observational-partial`, `observational-supported`, `eval-pending`, `not-measurable`), evidence pointer, what would change the status. In the same entry, either sketch an external `source.md` (repo URL, SHA, task, verifier command or artifact rubric) or kill the in-repo shortcut.

**How we’ll know.** FINDINGS contains the ledger line for hypothesis 8 (**observational-partial**, citation to the 2026-09-08 analysis) and an explicit scenario decision. Hypothesis 2 stays **eval-pending**: lesson 20 is support, not a plugin-wide verdict.

**Kill.** If the chosen “next measurement” for hypothesis 8 (cloud per-phase turn/context counts) is not in the artifacts, record `not-measurable` and stop. Do not launch a full eval to force a number. If no external verifier can be named in the same pass, kill the in-repo scenario idea rather than weakening the verifier requirement.

---

## 6. Kill list (dead ends this quarter)

| Dead end | Why it stops |
|----------|----------------|
| Mandatory or MVP `tools/driver/` | GOALS non-goal. Research event-log analogy is not a requirement. Blocked on nesting economics that are not measured. |
| Jev artifact assertion hook | Mechanizable checks should be deterministic. Uncalibrated Score threshold. |
| Merging `session_kind` with iterate phases | Orthogonal questions. Disagreement is expected, not a bug. |
| Alignment score as a gate or cross-source KPI | No human alignment labels. Confidence never clears 0.8. Source gap tracks kind mix. |
| Retuning 0.8 on this batch | n=8, zero human labels. Keep 0.8 only as a provisional review exemption. |
| In-repo plan folder as the first eval scenario | No independent verifier. Conflicts with the SWE-bench takeaway the research already accepted. |
| LangGraph-style brief-quality optimizer | Duplicate of the assertion spike, vaguer, and a behaviour loop. |
| HITL changes inside `design` / `execute` | Behaviour. Research confidence is medium. Cloud rule already forbids execute HITL. |
| Online per-turn Jev gating | GOALS non-goal. Batch classify is the layer that is not calibrated yet. |
| Pooling classify rows across a snapshot fix | Hashes exist so this is avoidable. Labels do not transfer. |
| “Document Composer vs Grok” as open backlog | Already stated in `docs/lab/README.md`. Close it. |

---

## 7. Operating model (unchanged, one constraint added)

Composer collects; Jev does cheap typed eval; this pass is the high-thinking strategy layer; additive docs land toward `master`; behaviour waits. Added constraint: **Composer does not grow the classify corpus for metrics until snapshot parity is settled.** Collecting more rows of an uninspected Claude payload makes the next calibration pass harder, not cheaper.
