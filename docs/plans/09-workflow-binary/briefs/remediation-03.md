---
brief_id: 239
design_id: 209
---

# Remediation 03: Jev screens the first 60,000 runes and records `pass` for the whole file

Severity: medium. Source: service-side review (`review-service.md`).
Owned paths: `tools/workflow/internal/scorer/jev.go`, `tools/workflow/internal/scorer/*_test.go`,
and, if a new verdict is chosen, the verdict handling in `tools/workflow/internal/serve/serve.go`.

## Defect

`scorer/jev.go` `ask` (line 178) cuts the snapshot to `maxText = 60000` runes before the request.
The answer to `screen_credential` covers only that prefix. The verdict is still recorded as `pass`
for the whole content hash, and the full blob is promoted.

The truncation is noted in the 3-01 report. Its security consequence is not: anything past rune
60,000 is never screened.

## Why it matters

DESIGN.md says the screen is the last check before persistence. A credential the regex precheck
misses (an unusual format, or one that only an LLM would recognise) is persisted under a `pass`
verdict if it sits past the cut. Large IMPLEMENTATION.md files and generated artifacts can reach
that size. The reads then report the content as screened clean, which is worse than reporting it
as unscreened.

## Fix approach

Pick one of these:

1. **Screen in chunks.** When the content exceeds `maxText`, split it into overlapping windows
   (overlap of about 200 runes, so a credential is not split) and send a screen-only request for
   each window after the first. Quality checks still score the first window. Any window flagged
   means `flag`; any window unreachable means the item stays pending, as today. The cost grows
   linearly with size, which is acceptable for a rare case.
2. **Use an honest verdict.** Record `partial` (or `pass` plus a `truncated` flag) when the content
   was cut, and have the reads show it. This is cheaper, but it leaves the tail unscreened.

Option 1 matches the design's intent. Choose option 2 only with the orchestrator's approval.

## Done evidence

Run from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH` and `TYPESAFE_API_KEY=`.

- Fail first: a jev test uses an `httptest` stub that flags the screen whenever the snapshot holds
  a marker string. Feed it 70,000 runes with the marker at rune 65,000, and assert the verdict is
  `flag` (option 1) or not `pass` (option 2). Quote its failure before the fix.
- After the fix it passes. Content under the cut still makes exactly one request.
- `go vet ./... && go test -race -count=1 ./...` passes.
