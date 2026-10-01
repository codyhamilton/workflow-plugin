# Literature and prior art

**Status:** reading notes for the lock memo. **Confidence: not high.** Citations are not replay results. A design that only has this file has not met Cody’s bar.

Each note has four lines: what was measured, the number we are willing to repeat, what this pack borrows, and what we must not infer. Full bibliographic lines are at the bottom.

In-repo predecessors are included because they are the actual baseline. They are not public studies.

## Sequential decisions

### Wald, 1945 — sequential tests

Wald’s sequential probability ratio test takes observations one at a time and stops when the likelihood ratio crosses a boundary. Until it crosses, the experiment continues. The sample size is random.

**Borrow.** Fail-open is the same shape: at each checkpoint, checkout only when the evidence clears a bar; otherwise take another look. The bar in v0 is fixed across checkpoints, which is closer to Wald’s fixed boundaries than to a bar that tightens with time.

**Do not infer.** We do not compute a likelihood ratio, we do not have a specified error probability α, and our “observation” is a judge’s choice on a snapshot. The interval is fixed at 10, 15, or 20 turns, not “one more observation as soon as it exists.” Calling `P0` an SPRT would be false. The tuning plan uses Wald as the language for the stop rule, then asks whether fail-closed would have been less late. That comparison is ours to measure.

### Page, 1954 — CUSUM

Page’s cumulative-sum charts accumulate deviations from a target and alarm when the sum crosses a limit. The chart is the classical industrial answer to “detect a change quickly, without alarming on every wiggle.”

**Borrow.** The cumulative block in `hybrid_v0` (re-read counts, compaction count, turns since a checkable step) is a crude chart. H7 asks whether that chart actually worsens after the gold exit.

**Do not infer.** We have not set a CUSUM threshold or a run length. `runaway_pattern` is a judge’s score, not a cumulative sum. If H2 says stats-only loses to the tail, the chart metaphor is the wrong one and the note should say so.

### Landis and Koch, 1977 — kappa bands

On observer agreement for categorical data, they assign labels: below 0 poor, 0.00–0.20 slight, 0.21–0.40 fair, 0.41–0.60 moderate, 0.61–0.80 substantial, 0.81–1.00 almost perfect. The paper presents the labels as a nomenclature aid. They are not a theorem.

**Borrow.** H5’s floor of alpha ≥ 0.40 is the bottom of their moderate band, chosen in advance so a weak panel cannot be declared good enough after the fact.

**Do not infer.** 0.40 is not “validated agreement.” Krippendorff has argued that fixed kappa cut-offs ignore prevalence and the cost of disagreement. We still publish alpha itself, the pairwise kappas, and the turn-spread, and we treat 0.40 as a stop rule rather than a quality claim.

### Dawid and Skene, 1979 — rater error rates

When several observers label items and the true class is hidden, the EM algorithm can estimate each observer’s error rates and a posterior on the true class.

**Borrow.** Alternative gold rule `A3`.

**Do not infer.** With a handful of transcripts the latent class is not identified. `A3` is inapplicable below 30 workers. Unanimity (`A0`) does not need that model.

### Krippendorff’s alpha

Alpha is a multi-rater reliability coefficient that allows missing assignments. That matches a panel where Composer may be absent and where invalid labels are dropped.

**Borrow.** The primary agreement number in the gold table.

**Do not infer.** A high alpha among three language models is not a human gold standard. The lock memo has to say “model–model” every time it quotes alpha.

## LLM judges (eval of evals)

### Zheng et al., NeurIPS 2023 — MT-Bench and Chatbot Arena

Strong LLM judges, GPT-4 in their study, agreed with human preferences at over 80%, and on MT-Bench non-tie cases the agreement with humans was about 85%, against about 81% human–human. They also documented position bias, verbosity bias, self-enhancement, and limited reasoning.

**Borrow.** The justification for using more than one judge and for fixing the field order of the bundle (brief anchor first, tail last), which is the mitigation we can actually implement. Also the warning that a single strong judge can look decisive and still be wrong in a systematic way.

**Do not infer.** Our panel is not GPT-4-on-MT-Bench, our items are agent prefixes, and we have no human votes in the primary gold. Quoting 80% as our expected alpha would launder their result.

### Wang et al., ACL 2024 — positional bias

Swapping the order of two candidate answers can reverse an LLM judge’s preference. In their Vicuna-benchmark setting, order manipulation let Vicuna-13B beat ChatGPT on 66 of 80 queries under a ChatGPT judge. They report GPT-4 conflict rates of 46.3% and 5.0% across two comparisons when order flipped, and higher conflict rates for ChatGPT.

**Borrow.** The judge bundle and the Jev state use one field order for every call. We do not randomise the tail into the middle. The gold protocol forbids showing another judge’s rationale, which would add a second “answer” for the model to anchor on.

**Do not infer.** We have not measured our own conflict rate under order swap. That measurement is a possible sensitivity after H5, not part of the first grid. Until it exists, “we fixed the order” is a precaution, not a debiasing result.

### Liu et al., EMNLP 2023 — G-Eval

G-Eval prompts an LLM with explicit criteria and chain-of-thought for NLG evaluation. With GPT-4 they report Spearman 0.514 against humans on summarization, higher than earlier automatic metrics. They also warn that LLM evaluators prefer LLM-authored text.

**Borrow.** The v0 criteria are written as explicit rubrics rather than a single “is this bad?” line, for the same reason G-Eval writes criteria: vague judgements move around. Pattern scores are separated from the choice so we can see an ungrounded checkout.

**Do not infer.** 0.514 is not a target for our alpha or for Jev–gold correlation. Their task is summary quality. Their bias finding is a reason to keep gold judges off the Jev prompt: if the judge and the worker share a family, a fluent but empty tail can look like progress. The panel mixes families (Grok, Claude, Composer) partly for that reason. Mixing families is not a proven fix.

### Lightman et al., ICLR 2024 — process vs outcome supervision

On MATH, their best process-supervised reward model solved 78.2% of a representative test subset at best-of-1860, versus 72.4% for the outcome-supervised model in the same table. The paper’s alignment point is the one we use: an outcome label can endorse a bad trajectory that happened to finish, and a process label can be checked without waiting for the end.

**Borrow.** Primary gold is prefix-causal. Hindsight gold is stored and is not the tuning target. The gap between them is a required column.

**Do not infer.** We are not training a reward model, and we are not on MATH. The 78% versus 72% figure does not predict our overshoot.

## Long inputs and summaries

### Liu et al., TACL 2024 — lost in the middle

On multi-document QA and a synthetic key-value task, accuracy was highest when the relevant span sat at the start or the end of the context, and fell when it sat in the middle, including for models built for long context. In the multi-document setting, adding documents could fail to help and sometimes hurt relative to a closed-book baseline.

**Borrow.** `hybrid_v0` puts `brief_anchor` first and the latest turns last, and does not hide the task in a prose middle. H2 is the test of whether that arrangement beats a tail with no stats and a stats block with no tail.

**Do not infer.** Their tasks are retrieval of a planted span. Ours is a judgement of a trajectory. A hybrid win on two JSONLs is not a replication of the U-curve.

### Wu et al., 2021 — recursive book summarization

A model summarized sections, then summarized the summaries, so a person could judge a book-length text without reading it. Human raters sometimes matched human summary quality (on the order of 5% of books in their report) while average quality stayed below human summaries. The method exists because the source does not fit in the judge.

**Borrow.** The reason a 12.7MB JSONL cannot be the Jev state, and the name of a future mode `recursive_summary`.

**Do not infer.** v0 does not put a summary model in the state. Doing so would make the gold and the instrument depend on a third model we have not measured. Recursive summary stays out of the grid until hybrid has numbers.

## Agent trajectories

### Yang et al., NeurIPS 2024 — SWE-agent

SWE-agent’s custom interface raised resolve rates on SWE-bench (12.5% pass@1 with their reported setup). The trajectory analysis that matters here: successful GPT-4 runs finished earlier and cheaper than unsuccessful ones (median about $1.21 and 12 steps versus a mean about $2.52 and 21 steps). About 93% of resolved instances were submitted before the cost budget, versus about 69% of instances overall. The authors suspect that raising the budget or the token limit would not substantially raise performance. Resolved trajectories on the full test set averaged 14.71 turns, median 12, with 75% inside 18 turns.

**Borrow.** The motive for an exit hatch: long runs are where failures live, and “give it more turns” is not automatically more solve rate. Baseline `C` (cut at `first_at` with no judge) is the crude version of their budget cap. Jev has to beat `C` to be worth calling.

**Do not infer.** Their median success is 12 steps, on SWE-bench, with a $4 cap that itself cuts runs in the 30–40 turn region. Our proposed first look is turn 75. Those numbers are not on the same scale. The field note already says 50–75 is an in-house crossover. H1’s literature row asks whether our gold exits sit near their 12 or near our 75. Until that column exists, 75 is not supported by SWE-agent.

### Yuan et al., Findings of EMNLP 2024 — R-Judge

R-Judge is 569 multi-turn agent records with human safety labels. The best model they report, GPT-4o, reached about 74.45% F1. Other models did not clearly beat chance. Fine-tuning on the judgement helped; simple prompting did not. The task is two-step: analyse the record, then mark safe or unsafe.

**Borrow.** The expectation that trajectory judgements are hard, so a low alpha is a plausible outcome rather than a harness bug. Also the separation between a written rationale and a binary label, which our rubric copies in miniature.

**Do not infer.** Checkout is not a safety label. Their taxonomy (program, IoT, software, web, finance risks) is not runaway / low progress / thrash / drift. We are not fine-tuning Jev on this corpus. “Prompted judges struggle” is a caution, not a prediction of our exact F1.

### Kwa, West, and Becker et al., METR, 2025 — task time horizons

METR define the 50% time horizon: the human-time length of tasks an agent completes with 50% success. On their suite the horizon for frontier agents has been doubling on a timescale of months (about seven months in the 2025 paper’s headline fit). Claude 3.7 Sonnet was reported near a 50-minute horizon in one version of the write-up; later fits on a changed suite put stronger models higher (the NeurIPS version discusses o3 near 110 minutes). The 80% horizon is several times shorter.

**Borrow.** Context only: long autonomous runs are a measured trend in the field, so a 296-turn worker is not a one-off curiosity. The maps 5-hour windows are the local version of the same theme.

**Do not infer.** A time horizon is human task duration at a success rate. It is not an API-turn cap. Nothing in that paper says to stop at turn 75 or turn 15. Using it to justify `interval = 15` would be a category error.

### Tran and Kiela, 2026 — single agent vs multi-agent under a matched budget

arXiv:2604.02460. On multi-hop QA (FRAMES, MuSiQue), across Qwen3, a DeepSeek-R1 distill, and Gemini 2.5, single-agent setups matched or beat several multi-agent setups when thinking tokens were held equal. The authors’ information argument (data-processing inequality) says a handoff through text is lossy when the single agent can still use its context. They also predict the opposite case: multi-agent becomes competitive when the single agent’s context use is degraded.

**Borrow.** False early has a cost, because a checkout is a handoff into a fresh context. False late has a cost when the pattern is `context_thrash`. The rubric’s refusal to checkout on turn count alone is the same caution: splitting a worker that is still using its context throws away a working state. The field note already cites this paper for the lossy-channel point.

**Do not infer.** The experiments are multi-hop questions, not repository workers. They do not estimate a turn threshold. “Context degraded ⇒ handoff” is their prediction and our H2/H7 region to measure, not a result we can import.

### Greenblatt et al., ICML 2024 — AI control

Protocols that keep a stronger untrusted model useful while a trusted monitor, or another copy, looks for backdoors in code. Trusted monitoring, untrusted monitoring, and trusted editing beat naive baselines in their programming game. The monitor is not the actor. Audit budget is limited, so only suspicious outputs get the expensive look.

**Borrow.** The shape “a separate judge sees a slice; the actor is not asked to grade itself,” and the economic point the cheap-Jev paper already uses: the expensive follow-up is the scarce resource. Also a reason the feedback channel is deferred: control protocols spend their design effort on what the monitor sees and when a human is called, which is a different paper from “does checkout match gold.”

**Do not infer.** This pack is not a control evaluation. There is no red team, no backdoor, no audit budget, and no claim that `session-checkout` would catch intentional subversion. Jev is not established here as a trusted monitor.

## In-repo prior art (the baseline, not a citation substitute)

| Source | What it already established | What this pack is not allowed to reopen |
|--------|-----------------------------|-----------------------------------------|
| `docs/analysis/2026-09-08-workflow-vs-field.md` | 50–75 turns / 100–125k is a crossover that moves with cold-start size and thinking volume. The note’s own table marks the sweet-spot claim **partial**. “No published source names these numbers.” | Treating 75 as externally validated |
| `evidence-maps-claude-5h.md` | 150 subagents, 24 over the band, 8 over 100 turns, `92a48e004519` at 296, `bb6165018de0` at 154 | Treating the finished-file flags as prefix-causal gold |
| Resolved cheap-Jev paper, use case 1 | `band_exit` at 76, one optional `session-progress` call when `jev_eligible`, state guard 12_000, pin `jev-1.13.0`, exit 0 | Editing those constants or that schema file |
| `tools/transcript/lib/snapshot.py` | A classify snapshot already truncates, redacts, and caps (~8_000 tokens in that file’s hard cap) | Using classify snapshots or classify labels as this study’s score |
| `GOALS.md` | Per-turn Jev inside the worker loop is out of remit | Sliding the interval down to 1 |

## Bibliography

- Dawid, A. P. and Skene, A. M. (1979). Maximum likelihood estimation of observer error-rates using the EM algorithm. *Journal of the Royal Statistical Society: Series C*, 28(1), 20–28. https://doi.org/10.2307/2346806
- Greenblatt, R., Shlegeris, B., Sachan, K., and Roger, F. (2024). AI control: Improving safety despite intentional subversion. *ICML 2024*. https://arxiv.org/abs/2312.06942
- Krippendorff, K. (2004). Reliability in content analysis: Some common misconceptions and recommendations. *Human Communication Research*, 30(3), 411–433.
- Kwa, T., West, B., Becker, J., et al. (2025). Measuring AI ability to complete long tasks. https://arxiv.org/abs/2503.14499
- Landis, J. R. and Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159–174. https://doi.org/10.2307/2529310
- Lightman, H., Kosaraju, V., Burda, Y., et al. (2024). Let’s verify step by step. *ICLR 2024*. https://arxiv.org/abs/2305.20050
- Liu, N. F., Lin, K., Hewitt, J., et al. (2024). Lost in the middle: How language models use long contexts. *TACL*, 12, 157–173. https://aclanthology.org/2024.tacl-1.9/
- Liu, Y., Iter, D., Xu, Y., et al. (2023). G-Eval: NLG evaluation using GPT-4 with better human alignment. *EMNLP 2023*. https://aclanthology.org/2023.emnlp-main.153/
- Page, E. S. (1954). Continuous inspection schemes. *Biometrika*, 41(1/2), 100–115.
- Tran, D. and Kiela, D. (2026). Single-agent LLMs outperform multi-agent systems on multi-hop reasoning under equal thinking token budgets. https://arxiv.org/abs/2604.02460
- Wald, A. (1945). Sequential tests of statistical hypotheses. *Annals of Mathematical Statistics*, 16(2), 117–186. https://doi.org/10.1214/aoms/1177731118
- Wang, P., Li, L., Chen, L., et al. (2024). Large language models are not fair evaluators. *ACL 2024*. https://arxiv.org/abs/2305.17926
- Wu, J., Ouyang, L., Ziegler, D. M., et al. (2021). Recursively summarizing books with human feedback. https://arxiv.org/abs/2109.10862
- Yang, J., Jimenez, C. E., Wettig, A., et al. (2024). SWE-agent: Agent-computer interfaces enable automated software engineering. *NeurIPS 2024*. https://arxiv.org/abs/2405.15793
- Yuan, T., He, Z., Dong, L., et al. (2024). R-Judge: Benchmarking safety risk awareness for LLM agents. *Findings of EMNLP 2024*. https://arxiv.org/abs/2401.10019
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. *NeurIPS 2023*. https://arxiv.org/abs/2306.05685

METR’s author list is longer than the three names above; the arXiv record is the citation to use when the lock memo quotes a horizon number. Page’s 1954 pages are the standard *Biometrika* citation for CUSUM. Krippendorff 2004 is the misconceptions paper; implementations of alpha should follow his own definition rather than a blog summary.
