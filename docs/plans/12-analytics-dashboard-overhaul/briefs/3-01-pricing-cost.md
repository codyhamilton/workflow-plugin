# Brief: 3-01 — Embedded pricing table and the cost function

Consumer: a Go worker (flash-tier); 3-05 (usage measures) and 3-09 (conversation route) call `store.Cost`.
Owned paths: `tools/workflow/internal/store/pricing.go` (new), `pricing_test.go` (new), `pricing_table.json` (new, a byte copy of `tools/transcript/pricing.json`). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-01-pricing-cost.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-02, 3-03.
Budget: 4 files to read, about 200 lines to write, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads, the **Cost** bullet (binding).
2. `tools/transcript/pricing.json` — the table (a `_meta` key plus per-model `input`, `cache_write`, `cache_read`, `output`, USD per million tokens).
3. `tools/transcript/cost_window.py` lines 140-200 (`_cost` and how rates apply) — the reference formula.
4. `tools/workflow/internal/ingest/extract.go` lines 36-95 — what each harness stores in `tok_in`, `tok_cache_read` and `cost_reported`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Given a call's harness, model, token columns and reported cost, one function returns its dollar cost, or says it cannot price it. It never charges cached input twice, and never treats a reported cost of 0 as a price.

## Contract

Design, cited: "`cost_usd` is computed at read time. It is the call's `cost_reported` when present. Otherwise it is tokens × the model's price in a pricing table that serve embeds, generated from `tools/transcript/pricing.json` (a test asserts the two are equal). A call with neither counts in `unpriced_calls` and adds 0."

Settled by this brief:
- Embed with `//go:embed pricing_table.json` (embed cannot reach `../`, so the file is a copy inside the package). A test reads `../../../transcript/pricing.json` and asserts the two files are byte-equal.
- API (exact):
  ```go
  type Tokens struct{ In, Out, CacheRead, CacheWrite, Reasoning int64 }
  func Cost(harness, model string, tok Tokens, reported *float64) (usd float64, priced bool)
  ```
- Order: (1) `reported != nil && *reported > 0` returns `(*reported, true)`. A reported 0 or negative is "not reported" (carried item: OpenCode cost 0 means unreported; `extract.go` already stores nil for 0, this is the defensive second guard). (2) Look up `model` exactly in the table. If absent and `model` contains `/`, look up the text after the first `/`. If still absent (or the model is empty), return `(0, false)`. No other fuzzy matching. (3) Price: `fresh = tok.In`, except harness `codex`, where `fresh = max(tok.In - tok.CacheRead, 0)` because Codex `input_tokens` already includes cached input (carried item: cached input must not be charged twice; `extract.go` lines 57-59 say so). `usd = (fresh*input + tok.CacheRead*cache_read + tok.CacheWrite*cache_write + tok.Out*output) / 1e6`. `Reasoning` is not charged separately (it is inside output).
- Known and to be reported, not fixed: the table holds only 7 models (Cursor names). Most local models (for example `claude-sonnet-5`, `gpt-5.4`) are absent, so they are unpriced unless the harness reported a cost. Do not add rates.
- Add `func PricedModel(model string) bool` using the same lookup (3-05 uses it).

## Done evidence

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store -run 'Cost|Pricing' -v` passes with tests for: reported 12.5 wins over tokens; reported 0 falls to token pricing; a Codex call `In=1000, CacheRead=400` is charged `600` fresh plus `400` cache-read (hand-computed expected value written as a literal in the test, for the model `kimi-k2.5`); a Claude call is not reduced; `opencode` model `x/kimi-k2.5` prices via the prefix rule; unknown model returns `(0,false)`; the byte-equality test.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go vet ./internal/store && gofmt -l internal/store` prints nothing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
