# Findings log

Append-only, dated notes. Prefer facts and pointers over speculation. Confidence: **high** / **medium** / **low**.

---

## 2026-09-30 — Lab workspace seeded; plugin + classify baseline

### Plugin map (high)

- **Core `workflow`:** version **2.5.0** (`/.claude-plugin/plugin.json`) — skills `design`, `refine`, `execute`, `comprehensive-review`, `close-out`, `post-build`.
- **Lab `workflow-lab`:** version **1.1.0** — `setup`, `iterate`, `transcript-parser`, `workflow-tuning`.
- **Evals:** harness documented in `evals/README.md`; **fixture corpus empty** (no `scenarios/` populated in repo yet).
- **Phase driver:** described in `docs/OVERVIEW.md` as `tools/driver/` — **not present in tree**; design lives in `docs/plans/06-phase-driver/DESIGN.md` (medium).
- **Transcript toolkit:** `tools/transcript/` — extract, stats, cost, search, `iterate_analysis.py` (regex phase skim); **classify spike landed on master** (`classify.py`, `lib/snapshot.py`, `lib/jev_client.py`, pin `jev-1.13.0`).

### Jev transcript classify — live batch (high for numbers, medium for label quality)

Eight sessions classified 2026-09-30 (UTC) into `tools/transcript/.classify-log.jsonl` (see attached export used for this seed). Model **jev-1.13.0**; each row includes `session_kind` (Choice) and `workflow_alignment` (Score 0–3).

| source | session_id (prefix) | kind | conf | align score | snapshot tok est | input_tokens |
|--------|---------------------|------|------|-------------|------------------|--------------|
| claude-code | d006f5a0 | workflow | 0.82 | 2.1 | 284 | 1244 |
| claude-code | af9b5cb1 | build | 0.73 | 2.25 | 694 | 2111 |
| claude-code | 30844998 | workflow | 0.85 | 2.46 | 878 | 2351 |
| claude-code | bd4f6c0d | plan | **0.30** | 2.29 | 496 | 1692 |
| cursor | 1dc10dd4 | ops | 0.93 | 1.47 | 110 | 838 |
| cursor | 77572779 | ops | **0.45** | 0.81 | 109 | 834 |
| cursor | a2be9531 | workflow | **0.62** | 1.2 | 143 | 872 |
| cursor | eac38429 | question | **0.41** | 1.16 | 103 | 831 |

**Spot-check verdict (medium):** labels are **mostly plausible** (workflow/build/ops/question mix matches heterogeneous sessions). Four rows fall **below 0.8 confidence** on `session_kind` — treat as **review-gate** candidates, not auto-metrics.

**Claude vs Cursor snapshot shape (medium):** Claude-code rows show **higher `snapshot_token_estimate`** (284–878) than Cursor (103–143) at similar `input_tokens` ~800–870 for Cursor vs ~1.2k–2.3k for Claude. Hypothesis: **Claude extract text is distorted** (reported “newline-per-char” bug in snapshot user-message fields) — needs fix in snapshot builder or parser, not taxonomy change. See proposal `PROPOSALS/2026-09-30-snapshot-claude-text-join.md`.

**Workflow alignment score (low–medium):** Scores cluster ~1–2.5; several runs show **moderate Score confidence** (e.g. 0.46–0.68) even when Choice confidence is high — do not use Score alone for gates until calibrated.

### Design spike (high)

Pre-implementation spike doc: Jev Choice over ≤~4k token snapshot, optional Score in same request, JSONL logging with `human_label` — aligned with merged code. API: TypeSafe System One, pin `jev-1.13.0`. Primary refs: [docs.typesafe.ai](https://docs.typesafe.ai/), [jevtypesafeai.com how-to-use](https://www.jevtypesafeai.com/how-to-use).

### Operating hypotheses (medium)

Root `README.md` lists eight falsifiable hypotheses; most still **untested** in cloud-pipeline context. Eval empty → hypotheses remain observational only.

---

## 2026-09-30 — Strategy pass on the eight-row classify batch

Full argument: [`ANALYSIS/2026-09-30-strategy-pass.md`](ANALYSIS/2026-09-30-strategy-pass.md). No proposal promoted. No behaviour change.

### Numbers re-derived from the log (high)

Same eight rows as the entry above. Extra measurements:

- **Non-state overhead** on Cursor is stable: `input_tokens − snapshot_token_estimate` = 728, 725, 729, 728.
- **Claude state density:** `(input_tokens − 728) / snapshot_token_estimate` = 1.82, 1.99, 1.85, 1.94 (mean 1.90). Cursor state-implied tokens match the chars/4 estimate. Same questions and model, so the gap is in the Claude snapshot payload. Mechanism (newline-per-character join versus something else) is **not** confirmed; `parsers/claude.py` joins content blocks with newlines, which is only pathological if blocks are single characters.
- **`mixed` probability is 0.0 on all 8 rows**, including `bd4f6c0d` (plan 0.37 / build 0.31 / workflow 0.29).
- **Score confidence** ranges 0.46–0.70. None would pass a 0.8 gate. `30844998` is the illustration: kind confidence 0.85, score 2.46, score confidence 0.46, P(2)=0.47, P(3)=0.50.
- **Alignment means** (Claude 2.28, Cursor 1.16) track kind mix (workflow/build/plan versus ops/question). Not attributed to the token-density gap.
- **`output_tokens` is 110 on every row.** Schema size, not a signal.
- Workflow probability ≥ 0.10 on 6/8 rows. Collision of “subject is the workflow plugin” with plan/build is the leading taxonomy issue. Unresolved until blind labels.

### Decisions (high for the policy, medium for the taxonomy revision trigger)

- Provisional review exemption stays at kind confidence ≥ 0.8. It is not a calibrated accuracy bar. 80% agreement is not claimable until ≥ 10 labeled rows sit above that line on one snapshot generation (3 rows qualify today).
- Do not gate or rank sessions on `workflow_alignment`.
- Do not pool later classify rows with these hashes if the snapshot builder changes.
- Hypothesis 8 already has an observational-partial writeup in `docs/analysis/2026-09-08-workflow-vs-field.md` (quadratic cost supported; “nearly always cheaper” unsupported; 40–75 turns is a crossover). Ledger entry still to be written into FINDINGS by the next measurement move. Eval corpus remains empty on purpose until an external verifier exists.

---

## Template for future entries

```markdown
## YYYY-MM-DD — Title

### Observation (confidence)

- Fact with pointer to PR, log, or eval run.
```
