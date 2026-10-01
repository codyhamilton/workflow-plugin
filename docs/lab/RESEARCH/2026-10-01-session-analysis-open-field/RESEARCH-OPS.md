# Research operations — multi-agent cadence

**Status:** operating rules for this open field. **Confidence: not high** that the cadence will be followed until a cycle log exists. The rules are concrete so a later cycle can be audited against them.

Workflow System Manager (WSM) is the Grok context that registers and closes cycles. It does not sit a gold seat in the same context that wrote the registration. Cloud seats stay the pattern already used for shape-qual (Composer, Sonnet, Grok on pack rows). Flash and the local server stay volume authors under the [Flash review gate](../../GUIDANCE-flash-review-gate.md) and cheap-analysis R2.

## Cycle

One cycle is one registered cell: one approach id from [`CANDIDATE-APPROACHES.md`](CANDIDATE-APPROACHES.md), one metric, one kill, one worker list, one budget. A cycle that tries to answer two approaches has not been registered.

Steps, in order:

1. **Register.** WSM writes a short registration: approach id, metric, kill criterion copied from that approach (not paraphrased into something easier), worker ids, whether live TypeSafe is in scope, card hash or "cards not built yet." Registration is committed before any seat runs. Composer does not invent the metric.
2. **Collect.** A Composer collector builds artifacts the registration names (feature JSONL, dry-run batch, fidelity diff). No gold labels. Fast-tier models are not used for this research, same rule as the lab-proposal skill.
3. **Volume, only if the approach asks.** Local llama.cpp and/or Flash. Outputs carry `seat_class: volume` or `author_tier: flash` and `review_status: unreviewed`.
4. **Review, only if Flash wrote.** Sonnet 5.5. This pass is not a shape-gold seat and does not see other seats' labels.
5. **Sign the review, only if a Flash artifact will be cited.** Claude or Grok, study convention, not a phase close and not a `Workflow-Phase` trailer.
6. **Gold seat, only if the registration asked for new prose labels.** Sonnet (signed), Grok, Composer, in fresh contexts, under cheap-analysis `shape-rubric-v0` if that is the rubric named. Default for this field: **do not seat**. `shape-qual-full-maps-v1` themes are the standing target. A new panel is a different cycle with its own α gate.
7. **Score.** A script. Disagreement is a row with both values. Means across seats, majority shortcuts on expiry, and "the model seemed right" are not scores.
8. **Close or fork.** WSM writes one of: `gate_cleared`, `killed`, `refused` (`prose_required`, `insufficient_n`, `gold_missing`, `agreement_withheld`, `missing`), or `fork`. A fork is a new registration. It is not a reply in the same thread that changes the metric.

Parallel cycles are allowed when they do not share a live TypeSafe budget and do not write the same gold file. The marker-screen distribution cycle can run beside a dry-run framing registration. Two live 32-call waves cannot run as one unregistered spend.

There is no standing multi-agent chat. The cycle log is the thread.

## Who is spawned

| Need | Spawn | Leave idle |
|------|--------|------------|
| Feature table, pack walk, dry-run, fidelity diff | Composer collector, or a script the collector commits | Flash, Jev, gold seats |
| Schema-locked summary of a prose prefix | Flash, then Sonnet review, then Claude or Grok sign-off | Flash as the reviewer or the sign-off |
| High-volume window labels ending at or before `early_window_end` | Local server at `WORKFLOW_LOCAL_LLM_URL` | TypeSafe as a fallback if the server errors; OpenCode's default provider map |
| Structured framing on a frozen card | `jev-1.13.0` through the existing client, dry-run first, cap 32 | A second HTTP stack, a substitute model, Cursor/Claude MCP in the first cycles |
| Prose-field α | Three fresh seats: Sonnet signed, Grok, Composer. Opus optional, not required | Flash, local, the WSM context that wrote the rubric, any seat that has seen the outcome suffix during an early-signal pass |
| Mechanical `reread_cluster` | Nobody. The path count is the label | Any seat asked whether "at least three" is true |
| Checkout α, `A0`, CHM seat-swap hints | Nobody in this field | The whole cycle. Those numbers stay in the progressive pack as a failed target and a non-adopted hint (nominal α ≈ 0.5674 does not override the over-fire discard) |

Grok has two jobs that must not share a context: WSM registration/close, and a gold seat. If a cycle needs both, the seat is a separate run that receives pack rows and the rubric, not the registration debate.

Composer has two jobs with the same split: collector, and gold seat. A collector context that built the card does not also label that card for α.

## When a disagreement becomes an experiment

Disagreement is already the valuable outcome on several workers. `92a48e004519` is 2-of-3 `early_thrash` with Composer `late_pivot`, while the early thrash **signals** are shared. `bb6165018de0` is the only three-way shape diverge, with a shared monitor-wait theme. The experiment is the shared theme and the recorded split. It is not a fourth seat asked to pick a label.

Rules:

- Two approaches that flag different worker lists produce a **fork** whose metric is the symmetric difference of those lists, scored against the standing strata. The fork does not average the flags.
- Two gold seats that split a §11 label and share a theme are scored on the theme. A cycle whose metric is "unanimous `shape_label`" on this corpus will rediscover 17 `unclear` agreements and is the wrong cycle.
- A local theme and a Flash theme that differ are a conflict row for `segment-swarm-arbiter`. They are not resolved in prose between agents.
- A Jev answer that echoes a count is `echo`. It is not debated as a judgement.
- If the disagreement is about TERMS, hooks, `confidence_min`, or whether to turn on `--call-jev`, that is an escalation, not a fork. Agents do not edit those by experiment.

## When a thread closes

Close, with one of the status words above, when any of these is true:

- The proof gate's artifacts exist and the metric is filled in, including an honest null (`agreement_withheld`).
- A kill criterion fired. Sibling approaches keep running.
- The approach's first slice is blocked on a mount or a server, and the refusal is written down.
- The cycle has spent its registered budget. More calls need a new registration.
- Someone proposes a second labeling under `shape-rubric-v0` or a second boolean cut under the same marker-rule id. That proposal closes as a protocol break, not as a new insight.

A thread without a registration does not stay open as exploration. Unregistered work is a note in the cycle log pointing at a missing registration, then it stops.

## When to escalate to Cody

Escalate, and do not keep cycling, when:

- A result would change TERMS, a hook, `confidence_min`, P0, or the decision to run `--call-jev`.
- Two approaches have both cleared gates and a write-up is about to call one of them the plan of record.
- The raw corpus mount is required (`summary-then-judge`, Flash arbiter on empty excerpts) and it is not available. Collectors do not vendor `/home/codyh`.
- A failed α or a failed marker rule is about to be re-run under the same id.
- Spend would exceed 32 live TypeSafe calls without `budget_tokens`, or any call would use a model other than `jev-1.13.0`.
- A cycle wants a new cloud seat panel over all 34 workers. That is a Cody decision because it spends three full seats to re-ask a question the agreement note already answered in theme form.

Escalation text is the registration, the score file, and the sentence that would become policy. It is not a transcript of the agents.

## Cadence

- WSM registers at most one live TypeSafe cycle at a time. Dry cycles (marker screen, dry-run search protocol, mount probe) can stack.
- Each cycle ends with a log entry: id, approach, status word, artifact paths, call count, kill fired or not. Suggested path when the first cycle starts, not created by this pack: `docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/cycles/CYCLE-LOG.md`.
- WSM closes or forks before opening another live cycle. A queue of unclosed live cycles is a failed cadence.
- Weekly lab skim, if one happens, reads the log's status words and the kill list. It does not re-litigate seat prose.
- No approach is promoted to a `PROPOSALS/` white paper from inside a cycle. A proposal that recommends one pipeline is a later Grok pass, after at least two cycles have closed with comparable metrics, and it stays soft until Cody accepts behaviour.

## What the first cycles are allowed to be

The cheapest audits, in an order that does not force the later ones:

1. `marker-screen-margin` distribution, 0 calls. It can kill or spare whole families before anyone writes a prompt.
2. Dry-run half of `stats-jev-tournament` or `frozen-card-search` (registration, hashes, cap). Still 0 live calls.
3. Mount probe for `summary-then-judge`. A refusal is a finished cycle.
4. Local server probe for `segment-swarm-arbiter`. `missing` is a finished cycle.

A live 32-call wave waits until cycle 1 or 2 has a frozen card and a registration Cody has not been asked to pre-approve beyond the standing dry-run rule. Turning `live` on is inside the cheap-analysis contract only when the key, `confirm_live`, and the cap are all present. This operating note does not turn it on.
