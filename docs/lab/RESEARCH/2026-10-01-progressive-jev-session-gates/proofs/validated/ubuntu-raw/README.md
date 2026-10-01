# ubuntu-raw progressive Jev dry-run (2026-10-01)

Offline dry-run of `replay_progressive_gates.py` against **raw** Claude subagent JSONLs
on codyh-ubuntu (not redacted fixtures).

- Schedule: `75:15`
- Live `--call-jev`: **blocked** — `TYPESAFE_API_KEY` unset in environment / common profiles
- Commit policy: only `*.omit-state.jsonl`, `*-metrics-*.json` (without with-state),
  `*-thrash-table-*.json`, `SUMMARY-*.json`, and this README.
  Files named `*.with-state.jsonl` and `*-gold-bundles-*.jsonl` embed hybrid/gold prose
  from raw transcripts and must stay **untracked**.

Workers:
- `92a48e004519` smoking gun (T=296)
- `bb6165018de0` smoking gun (T≈154)
- `6c87c96bd9bb` negative control (T=70 < 75 → zero checkpoints)
