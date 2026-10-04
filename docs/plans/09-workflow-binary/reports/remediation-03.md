# Remediation 03: screen content past the first window

Execution 34. Brief: `briefs/remediation-03.md`. Orchestrator chose option 1 (screen in chunks).

## Done
- Added `TestJevScreensPastFirstWindow` (`internal/scorer/jev_test.go`). Before the fix:
  `marker at rune 65000 flags: verdict = {Flag:false ...}, <nil>; want flag`, and the window-edge, per-request
  question count and later-window-failure subtests failed too. After: all pass.
- `jev.go`: `Screen` sends window 1 (runes 0..60000) with the screen question and the kinds' checks, as before.
  If the content is longer, it sends screen-only windows of 60000 runes starting 200 runes before the previous
  window's end, stopping at the first level that rounds to 2 or more. The verdict uses the highest raw score
  (`math.Round`, flag at 2, unchanged). A failed later window returns its error (`ErrUnreachable` for transport
  or 5xx), so the item stays pending and is retried whole. `Score` still scores the first window only.
- Content up to 60000 runes makes exactly one request (tested).

## Departures
- The existing subtest "request shape and one request" fed 70000 runes and expected one request. That is now two
  by design, so it uses 60000 runes (the exact limit), which keeps its truncation assertion.
- No change to `serve.go`: no new verdict.

## Known problems
- Cost grows linearly with size (about one request per 59800 runes). A retry after a later-window failure
  re-sends window 1 as well.
- A credential longer than the 200-rune overlap could still be split; none is expected.
- Quality checks still see only the first window (as the brief specified).
