# Competing interception variants - Soft HOLD

**Status:** evidence and proposal only. No hook, automatic reviewer spawn, phase advancement change, or other behavior ship.

## Evidence boundary

This report recomputes the landed TypeSafe review-axis rows and treats the phase axis as unavailable at row level.

- [`typesafe-review-check/results.jsonl`](typesafe-review-check/results.jsonl) has 1,744 unique rows, all `axis=review_check`: 244 initial rows and a 1,500-row top-up.
- [`typesafe-review-check/meters.json`](typesafe-review-check/meters.json) reports a separate 2,000-call run with 1,756 `phase_gate` and 244 `review_check` cells. No landed JSONL contains a `phase_gate` row, so phase outcomes, variants, and cross-axis agreement cannot be measured.
- [`typesafe-review-check/meters-topup.json`](typesafe-review-check/meters-topup.json) reports 2,744 total rows after another 1,000-call top-up, but the extra rows are not landed. They are excluded here.
- All landed review rows have HTTP 200 responses and answer objects. No raw request or response artifacts are landed.
- The Flash vol2 fallback is not used. [`FLASH-VOL2-PARSE-MISS.md`](FLASH-VOL2-PARSE-MISS.md) confirms that the meter, result rows, and raw output needed for a root-cause finding are not landed.

The 1,500-row review top-up contains three example rows and 1,497 synthetic corpus rows. The synthetic rows use five Claude Code sessions from one project at checkpoint 30. Four session blocks are complete; the fifth is truncated. Measurements below use only the four complete blocks: 1,248 cells split into 576 `unit_needs_review`, 384 `refine_brief`, and 288 `session_progress` cells.

These are repeated synthetic manipulations, not independent units. The tables report response sensitivity without cell-level confidence intervals. There are no blind defect, phase-correctness, or later-failure labels, so none of the results measure interception accuracy.

All 576 balanced `unit_needs_review` cells also lack a `Carried` heading. The unit-review path has no existing `evaluate_assert()` gate. The sequential arms below therefore propose a unit-state shape filter based on the documented compact schema; all 576 balanced cells fail that proposed filter. Their responses are useful only for selecting future contrast dimensions, not for estimating advisory review workload.

## Review-axis measurements

### Unit closure

`review_confidence` is on a 0-3 risk scale. `P(review)` is the response probability assigned to the `review` choice.

| Contrast | Cells | Mean risk | Mean P(review) |
|---|---:|---:|---:|
| Verifier exit 0 | 288 | 2.332 | 0.713 |
| Verifier exit 1 | 288 | 2.853 | 0.949 |
| Strong verification text + exit 0 | 36 | 1.657 | 0.429 |
| Contradictory text + exit 1 | 36 | 2.969 | 1.000 |
| Error-cascade text + exit 1 | 36 | 2.990 | 0.990 |

The exit-code effect is stable across the four complete blocks: `exit 1 - exit 0` is +0.492 to +0.535 risk and +0.222 to +0.250 P(review). Phase number is effectively null in this synthetic cut: mean risk is 2.591-2.594 across phases 1-3. Trailer variants span only 0.032 risk and 0.031 P(review).

This supports verifier status and semantic closure evidence as contrast dimensions. It does not establish deterministic rules for contradiction, placeholder, or error text. The separate existing phase assertion checks report status, trailer and phase agreement, `Verification` and `Carried` headings, and quoted-outcome or substantive-verification evidence; `unit_needs_review` currently has no equivalent assertion.

### Refine brief

`P(large)` is the summed probability of score classes 2 and 3.

| Brief lines | Cells | Mean complexity | Mean P(large) |
|---:|---:|---:|---:|
| 40 | 96 | 1.202 | 0.439 |
| 120 | 96 | 1.638 | 0.684 |
| 240 | 96 | 1.803 | 0.777 |
| 600 | 96 | 1.995 | 0.854 |

The 600-line minus 40-line difference is +0.787 to +0.798 complexity and +0.413 to +0.416 P(large) in each complete block. Line count is a viable control axis, but the generated excerpts reuse verification and error prose. A follow-up must hold a genre-correct excerpt constant before attributing the response to brief size.

### Session progress

| Synthetic tool-batch size | Cells | Mean progress | Mean P(handoff soon) |
|---:|---:|---:|---:|
| 1 | 96 | 2.665 | 0.321 |
| 2 | 96 | 2.790 | 0.329 |
| 8 | 96 | 2.848 | 0.392 |

This contrast is not stable. In the independent initial 84-row grid, batch sizes 1, 2, and 8 produce mean progress scores of 2.336, 2.894, and 1.114, while P(handoff soon) remains nearly flat at 0.382, 0.363, and 0.374. The top-up also repeats generic `tool-N` states. Do not promote tool-batch count as an interception variant.

## Competing shadow variants

All variants stay offline. The deterministic phase gate retains authority in every arm.

For this proposed comparison, unit-state shape eligibility requires `Verification` and `Carried` headings, a non-empty closing excerpt, a trailer matching the unit slug and phase, and verifier exit 0. This is an experimental filter, not current product behavior.

| Variant | Phase-gate axis | Review-check axis | Current evidence |
|---|---|---|---|
| M0 mechanical control | Existing deterministic outcome-evidence assertion only | No advisory call; audit a fixed sample after deterministic phase pass | Comparator is defined but has no result row in this corpus |
| S1 sequential advisory | After deterministic pass, record `alignment_sanity`; never override the pass/fail result | For units linked to a deterministic phase pass, validate the documented unit-state shape and then ask `needs_review` | Zero balanced unit rows pass the proposed shape filter; phase rows are missing |
| T2 threshold sweep | Sweep advisory alignment-score thresholds after deterministic pass | Sweep `review_confidence` thresholds after the same linkage and shape filter | 612/828 unfiltered landed unit rows have score >=2.5, but those synthetic rows cannot select or estimate an eligible-unit threshold |
| P3 paired budgeted triage | Rank deterministic-pass phases for inspection under a fixed budget | Rank eligible units under the same budget and adjudicate disagreements | Preferred next measurement; zero paired records exist because phase rows and shared record IDs are missing |

P3 is the most informative next experiment. It evaluates both axes on the same real closing record and exposes disagreement instead of treating either advisory score as authority. M0 remains the required control. S1 and T2 remain proposed shadow arms; the current review rows inform contrast design but do not measure either arm.

## Measurement gate

Do not rank a winner until a follow-up:

1. Lands or explicitly marks unavailable the 1,756 reported phase rows and the later 1,000 reported review rows.
2. Uses one stable record ID for the phase and review calls on the same real closure record.
3. Records deterministic pre-gate eligibility, assertion result, and state-field missingness.
4. Balances projects, harnesses, phases, and checkpoints and reports session/phase-clustered denominators.
5. Adds blind human disposition plus later defect, failed-assert, or reopen outcomes.
6. Measures trigger rate, audited-skip miss rate, precision, phase/review disagreement, review cost, and repeated-call stability.

Until those gates close, the result is **Soft HOLD**: review-axis sensitivity is measured, phase-axis outcomes are missing, and no behavior change is authorized.
