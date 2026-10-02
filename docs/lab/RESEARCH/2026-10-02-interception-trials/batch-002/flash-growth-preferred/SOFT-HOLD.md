# SOFT-HOLD — Flash preferred GROWTH cut (#109/#111)

**Generated:** 2026-10-02T12:46:52+10:00 (AEST)

**Soft Standard HOLD** — white-paper evidence only. No hooks, Soft Standard unlock, Pilot, or live Jev. `:8080` unused.

## Cut
- Preferred scenarios: **12** (frozen from `GROWTH-RANKING.json`)
- Exact-labeled sessions: **9**
- Planned cells: **108** (12×9=108 when exact=9)
- Include diagnostic 7: **False**
- growth-fill: `growth-fill-v1`; empty state = unsupported (gated)
- Tail-less gated sessions: **25**

## Counts
- attempted: **108**
- fire: **19**
- defer: **89**
- parse_miss: **0**
- errors: **0**
- fire_rate: **0.1759**
- wall_s: **120.6**

## Exact sessions
- `2e083814b952`
- `499377c18811`
- `5415ae00a788`
- `567e678f0a57`
- `730a03ecdc0d`
- `a2e9f853749d`
- `a56bad1c7f13`
- `a8d0a590128a`
- `b13d1a65a961`

## Outcomes by scenario
- `state.markers_focus|q.context_thrash_compact` — n=9 fire=4 defer=5 rate=0.4444
- `state.markers_focus|q.dependency_wait` — n=9 fire=4 defer=5 rate=0.4444
- `state.markers_focus|q.idle_tool_spin` — n=9 fire=6 defer=3 rate=0.6667
- `state.markers_focus|q.test_flake_loop` — n=9 fire=3 defer=6 rate=0.3333
- `state.recent_delta_brief|q.bash_retry_storm` — n=9 fire=0 defer=9 rate=0.0
- `state.recent_delta_brief|q.brief_abandon` — n=9 fire=0 defer=9 rate=0.0
- `state.recent_delta_brief|q.deliverable_orphan` — n=9 fire=0 defer=9 rate=0.0
- `state.recent_delta_brief|q.docs_only_drift` — n=9 fire=1 defer=8 rate=0.1111
- `state.recent_delta_brief|q.edit_churn` — n=9 fire=0 defer=9 rate=0.0
- `state.recent_delta_brief|q.parallel_agent_thrash` — n=9 fire=1 defer=8 rate=0.1111
- `state.recent_delta_brief|q.scope_creep_silent` — n=9 fire=0 defer=9 rate=0.0
- `state.recent_delta_brief|q.speculative_rewrite` — n=9 fire=0 defer=9 rate=0.0

## Non-authorization
- Soft HOLD unchanged; no behaviour/hooks ship.
- `window_status=unidentified` at emit; no FP/miss board.
- Replication of preferred analytic cut, not a preregistered product eval.

