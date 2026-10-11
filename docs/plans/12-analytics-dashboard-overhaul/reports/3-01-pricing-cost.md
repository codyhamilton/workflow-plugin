# Report: 3-01 pricing table and cost function

Status: done

## What changed
- `tools/workflow/internal/store/pricing_table.json`: byte copy of `tools/transcript/pricing.json`, embedded with `//go:embed`.
- `tools/workflow/internal/store/pricing.go`: `Tokens`, `Cost(harness, model, tok, reported)`, `PricedModel(model)`, with the API and order exactly as the brief settled (positive reported cost wins; exact lookup, then text after the first `/`; Codex fresh input = max(In - CacheRead, 0); Reasoning not charged).
- `tools/workflow/internal/store/pricing_test.go`: tests for reported 12.5 winning, reported 0 and negative falling to tokens, Codex In=1000/CacheRead=400 on `kimi-k2.5` (literal 0.0004), Codex clamp, Claude not reduced, `x/kimi-k2.5` prefix rule, unknown/empty/double-prefix models returning (0,false), and byte-equality with `tools/transcript/pricing.json`.

## Evidence
- Before: no `Cost` or pricing files in the package.
- After: `go test ./internal/store -run 'Cost|Pricing' -v` passes all 7 tests; `go vet ./internal/store` and `gofmt -l internal/store` print nothing.

## Departures and contradictions
None.

## Known problems (reported, not fixed)
- The table holds only 7 Cursor model names. Most local models (for example `claude-sonnet-5`, `gpt-5.4`) are absent, so they are unpriced unless the harness reported a cost. No rates were added.
- A model like `a/b/kimi-k2.5` does not match (only the text after the first `/` is tried), per the brief.

## Unfinished
None. 3-05 and 3-09 can call `store.Cost`; 3-05 can call `store.PricedModel`.
