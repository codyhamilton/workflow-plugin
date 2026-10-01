# Tuning plan — offline replay only

**Status:** plan. **Confidence: not high.** No stage below has been executed. Live Claude `PostToolBatch` is not a stage.

The point of the plan is to produce hard numbers before any recommendation locks. The order is the control. Gold reliability comes before Jev interpretation. Jev interpretation comes before a change to `P0`. A change to the proposal’s defaults inside the same revision as the definitions would be tuning without data.

## 0. What “offline” includes

| In this plan | Not in this plan |
|--------------|------------------|
| Read stored Claude JSONL from disk | Install a hook, edit `settings.json`, or run a Claude session to mint a transcript |
| Build prefixes, stats, and snapshots locally | Inject `additionalContext` or draft the parent message |
| Call Jev (`jev-1.13.0`) on those snapshots when `TYPESAFE_API_KEY` is set | Call Jev from a worker loop or from `assert_phase` |
| Call the gold-panel models on judge bundles | Treat a gold-model call as a live gate |
| Dry-run the request JSON when a key is missing | Treat a dry-run as a checkout decision |

A missing key blocks stages 4 and 5. It does not block stages 1–3. It does not allow a narrative stand-in for the missing table.

## 1. Corpus

**Include** a worker JSONL when `api_turn` count `T >= 75` (TERMS §1).

**Priority, in this order,** once a path and a sha256 exist:

| Id | Published size | Why it is first |
|----|----------------|-----------------|
| `92a48e004519` | 296 API calls, 12.7MB, peak 130k, `OVER_TURNS`, `FAT_JSONL`; 6 paths re-read ≥ 3×; ~60 compact-ish events; sleep/poll bash ≈ 3 | Longest published runaway. H6 names it |
| `bb6165018de0` | 154 API calls, peak 125k, ~3.3MB, session `bd4f6c0d…` | Second fat worker. Gold may legitimately be null |
| Other maps workers with `T > 100` | 8 of 150 in the published aggregate | The late-runaway slice. Ids beyond the two above are not in the lab notes |
| Other workers with `75 <= T <= 100` | Part of the 24 over-ideal, mixed with context-only flags | Needed so the corpus is not two anecdotes |

**Exclude** from the metric corpus:

- `6c87c96bd9bb` at 70 turns (refine agent). It is a negative control, not a row: every cell with `first_at >= 75` must report an empty checkpoint list.
- Workers under 75 turns.
- Workers whose only maps flag is context, when `T < 75`. Context-only sizing stays on the closed gate’s peak thresholds. This study is about repeated turn checkpoints.
- Files that fail the turn definition (no assistant rows, or unreadable JSONL).

**Paths.** The maps summary and `proofs/fixtures/maps_named_workers.json` in the predecessor pack store aggregates, not file paths. This repo does not contain `92a48e004519`’s JSONL. Stage 1 stops at “blocked, n = 0” until someone points the harness at a directory. Do not download or reconstruct a transcript to fill the gap.

**Manifest columns:** `worker_id`, `path`, `sha256`, `bytes`, `T`, `tool_assistant_turns`, `peak_ctx_tokens`, `source` (`maps` or `other`). The first hard number this pack can emit is `n_workers_ge_75` plus the two priority rows found or not found.

**Minimum corpus before H1 is interpretable:** the two priority files, plus enough other `T >= 75` files that the length bins are not empty where the data exists. If the only files on disk are the two guns, run H2, H6, and the alpha **on those two**, and mark H1 `underpowered`. Do not generalise from n = 2.

## 2. Gold-label protocol

Rubric: [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md). Judges do not see Jev prompts or other judges.

**Panel, independent calls:**

| Seat | Model | If unavailable |
|------|--------|----------------|
| 1 | Grok 4.7 high | Worker is `underpowered` unless three other seats returned labels. In practice Grok is required for this pack’s sponsor. Record the outage and stop that worker |
| 2 | Claude Sonnet, exact id recorded | Same |
| 3 | Claude Opus, exact id recorded | Same |
| 4 | Composer, exact id recorded | Allowed to be missing. Alpha uses the three that returned |

Minimum for a primary gold row: **three** labels at each labeled turn that enters the aggregate.

**What each judge does, per worker:**

1. For each labeled turn `c` in `60, 75, 90, …` while `c <= T`, receive the 60_000-character prefix bundle and return `not_yet` or `checkout`, the pattern set, and a rationale of at most 120 words.
2. After that series is stored, one hindsight call on the full-file bundle. Stored separately. Never used to pick `P`.

Labeled-turn counts at 15-turn spacing from 60:

| Worker | `T` | Prefix calls per judge |
|--------|-----|------------------------|
| `92a48e004519` | 296 | 16 (60 through 285) |
| `bb6165018de0` | 154 | 7 (60 through 150) |

Four judges on both guns is `4 × 23 = 92` prefix calls, plus 8 hindsight calls. The rest of the corpus multiplies by its own prefix counts. That is the expensive step. It is still much smaller than calling every judge at every snapshot cell.

**Blindness.** Separate sessions per judge. The prompt is the rubric plus the bundle. No few-shot example that names `92a48e004519` or states a target turn. The calibration stories in the rubric are pattern shapes; the harness prompt includes those stories and does not include the hindsight turn counts as a suggested answer. A practical split: the judge prompt includes the pattern definitions and the “not this” contrasts, and omits the sentences that state 296, 154, and 130k. Those sentences stay in the rubric for human auditors. This avoids teaching the judge the ending of the priority files. The auditor doc and the judge prompt are different texts. The proof README keeps both hashes.

**Invalid labels** are dropped per the rubric. Dropping can push a turn under three judges. That turn is skipped in `A0`’s walk (it cannot be unanimous). It still counts in the alpha denominator as missing for those judges, via Krippendorff’s missing-data handling, and the skip is counted in `invalid_label_rate`.

### Aggregation

Pre-registered primary rule: **`A0` earliest unanimous checkout** (TERMS §7).

Also compute `A1` (earliest majority) and `A2` (median of finite per-judge exits, round up to the labeled grid). `A3` Dawid–Skene only if `n_workers_ge_75 >= 30`. Below that, write `A3 = inapplicable` and cite the reason: observer-error EM is not identified on a handful of items (Dawid and Skene, 1979).

**Agreement table, emitted before stage 5 is read:**

- Krippendorff’s alpha on `{not_yet, checkout}` pooled over powered prefixes
- Pairwise Cohen’s kappa
- Per-worker spread of first-checkout turns, plus `never_checkout` counts
- `invalid_label_rate`

**Stop rule (H5).** Alpha `< 0.40`: revise the judge prompt or the bundle, re-label the priority files, and do not select a Jev cell. Landis and Koch (1977) place 0.40 at the top of “fair” and the bottom of “moderate.” The floor is pre-registered so a disappointing alpha cannot be talked into a pass.

Report alpha next to two public numbers without claiming we should match them: Zheng et al. (NeurIPS 2023) found GPT-4 agreement with humans above 80% on MT-Bench non-ties, on chat preferences, with known position and verbosity biases. R-Judge (Yuan et al., Findings of EMNLP 2024) found GPT-4o at about 74% F1 on agent-trajectory safety labels and other models near chance. Our task is closer to a trajectory judgement than to MT-Bench, and our agreement is model–model, not model–human.

## 3. Parameter grid

Jev calls are cached. Policies that do not change the request are applied in stage 5 for free.

**Cache key:** `(worker_id, checkpoint_turn, snapshot_mode, snapshot_params, question_set, jev_model)`.

`checkpoint_turn` runs over the union of all schedules’ checkpoints, which for the grid is every turn `c >= 60` with `c <= T` that equals `60 + k*gcd` or, more simply, every turn in the set generated by all nine schedule pairs. Generating all three intervals from all three origins produces a turn set spaced by 5 from 60 (gcd of 10, 15, 20 is 5), plus the 76 sensitivity. Calling Jev every 5 turns multiplies cost by about three versus the gold grid.

**Cost control, pre-registered:**

| Wave | Jev checkpoints | Snapshot cells | Question sets | Purpose |
|------|-----------------|----------------|---------------|---------|
| Pilot | The 15-turn grid from 60, on the two guns only | `hybrid_v0` N=8 excerpt 400 only | `Y_full` only | Schema lengths, one real decision trace, H6’s raw material. 16 + 7 = 23 calls |
| Wave 2 | Same checkpoints, same two guns, then the rest of the corpus | All 13 snapshot cells | `Y_full`, `Y_choice_only`, `Y_legacy` | H2 and H3. Per gun: 16 × 13 × 3 = 624 calls if every prefix is used; skip a prefix the moment the state cannot be shrunk under 12_000 (no API call) |
| Wave 3 | Any schedule checkpoint not on the 15-turn grid, smoking guns only | The winning snapshot from wave 2, or hybrid if H5 failed and there is no winner | `Y_full` | Removes the “inherit the previous label” approximation for intervals 10 and 20 |

Confidence `{2, 3}` and `on_uncertain {open, closed}` do not add calls.

Nine schedule pairs times two confidence values times two uncertainty policies is 36 policy sheets over one cache. The 76 × 15 sensitivity is a 37th sheet on the same cache.

**Do not add** a rising `confidence_min` to this grid. H7 either motivates that axis later or retires it.

### Snapshot cells (13)

As TERMS §5: `stats_only`; `last_n_turns` N in {4, 8, 16}; `last_k_chars` K in {2000, 4000, 8000}; `hybrid_v0` N in {4, 8, 16} × excerpt in {200, 400}.

### Question sets (3)

`Y_full`, `Y_choice_only`, `Y_legacy` (TERMS §6).

## 4. Replay procedure

For each worker, in order of `api_turn`:

1. Parse the JSONL once. Assign `api_turn` as in TERMS §1.
2. At each cached checkpoint, build the snapshot from `prefix(c)` only. Apply the shrink order. Record `state_chars` and `request_chars`.
3. If the key is set, POST the `jev-1.13.0` request and store the raw response. If not, store `decision = missing`, `reason = dry_run`.
4. Map the response through `R(t)` for each policy sheet.
5. `gate_exit` is the earliest firing checkpoint on that sheet. `max_allowed_turns` follows TERMS §3.
6. Join to `gold_exit` under `A0`, and again under `A1` and `A2` for the robustness columns.

Baselines on the same workers:

- `B`: one `Y_legacy` call at the first prefix where the closed `jev_eligible` rule is true. No second call.
- `C`: `gate_exit = first_at` with no Jev call.

Peak context and prefix bytes for `B` come from the same cumulative stats as the snapshot, so the baseline and the progressive cells share a parser.

## 5. Metrics and the lock rule

Compute TERMS §8, including length bins `T < 100`, `100 <= T <= 150`, `T > 150`.

**Lock rule, applied only after H5 passes, and not applied in this revision:**

Among cells with `on_uncertain = open` and `gold_rule = A0`:

1. Discard cells with `false_early_rate > 0.15`.
2. Discard cells whose `false_early_rate` in the `T > 150` bin exceeds the corpus rate by more than 0.10 (repeated-testing inflation).
3. Among the rest, minimise `false_late_rate`, then minimise median positive overshoot, then minimise median `max_allowed_turns` on the smoking-gun slice.

If no cell survives (1) and (2), **do not recommend a cell.** Report `P0`’s numbers and leave the proposal `researching`. The 0.15 cap is a pre-registered constraint so the lock cannot quietly accept a trigger-happy rule. It is not a measured optimum. Change it only in a later revision that shows the constraint, not in the same breath as the results.

`P0` remains the reported proposal cell even when another cell wins the rule. The lock memo says either “`P0` won,” “`P*` won and `P0` lost for this stated reason,” or “no cell survived.”

## 6. Literature check, after the numbers exist

The lock memo includes a short table: each citation in [`LITERATURE.md`](LITERATURE.md), the quantity that paper measured, the quantity we measured, and one sentence on transfer. Required rows:

| Paper | Their quantity | Our quantity | Transfer test |
|-------|----------------|--------------|---------------|
| SWE-agent (Yang et al., 2024) | Median 12 steps on successes; failures run longer; raising the budget did not look promising | Our `max_allowed_turns` and the turn where gold fires | If our gold exits cluster near 12, the 75-start is late. If they cluster past 75, SWE-bench’s step counts do not set our band. Either result is informative |
| Liu et al., TACL 2024 | U-shaped use of long context | H2, hybrid vs tail vs stats | A hybrid win is consistent with primacy/recency. It does not reproduce their QA experiment |
| Lightman et al., 2023 | Process labels beat outcome labels on MATH | Gap `hindsight − primary` | A large gap means we were right to forbid tuning on hindsight. A near-zero gap means the ending was already visible in the prefix |
| Zheng et al., 2023; Wang et al., 2023 | LLM–human agreement and position bias | Our model–model alpha; field order of the bundle is fixed | We cannot claim their 80%. We can say whether our alpha is in a usable range |
| Yuan et al., R-Judge, 2024 | Best F1 ~74% on trajectory safety; others near chance | Our alpha and `invalid_label_rate` | Low agreement is the expected base rate for trajectory judgements |
| Wald, 1945 | Sequential tests stop when a boundary is crossed, else keep sampling | Fail-open, fixed bar, fixed interval | We did not implement a likelihood ratio. A fail-closed win on false late with a collapsed false-early rate would show the fixed-interval fail-open rule is too slow, which is a result, not a reason to pretend we ran SPRT |
| Tran and Kiela, 2026, arXiv:2604.02460 | Under a matched thinking budget, single agents match or beat multi-agent on multi-hop tasks; multi-agent helps when one agent’s context use is degraded | False early (handoff that was not yet warranted) vs gold checkouts that cite `context_thrash` | Their task is not coding. The transferable warning is that a handoff is a lossy channel, so false early has a cost, and thrash is the case where a second worker can be worth that cost |
| Greenblatt et al., 2024 | A weaker monitor on an untrusted coder, with a limited audit budget | Not measured here | Cited so nobody treats this pack as an AI-control evaluation. Different threat model |

## 7. Execution order

1. Manifest. If the priority paths are missing, publish the blocked manifest and stop. That publication is a valid result of this plan.
2. Judge-prompt hash and auditor-rubric hash, checked in beside the labels when labels exist.
3. Gold on the two guns. Alpha. Stop if H5 fails.
4. Gold on the rest of the corpus if the manifest has more files.
5. Jev pilot (23 calls) then wave 2. Schema overflows never hit the API.
6. Metrics, baselines, length bins.
7. Lock memo or an explicit “no cell survived.”
8. Only a later Cody decision can move hook behaviour. This plan does not schedule that decision.

No stage requires a running Claude Code process, a `PostToolBatch` event, or a change to `install.sh`.
