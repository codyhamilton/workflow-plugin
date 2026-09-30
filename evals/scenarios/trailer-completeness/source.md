# Scenario: trailer-completeness

## Repo

- URL: https://github.com/codyhamilton/workflow-plugin
- Commit: in-tree fixture. `verify.py` rebuilds git history from `reference/DESIGN.md` and `reference/expected.json`. There is no external pinned SHA and no second clone.

## Task

Close a two-phase plan so `Workflow-Phase:` trailers on `master..HEAD` are `<slug>:1`, `<slug>:2`, and `<slug>:done`. A wrong-slug trailer on the same branch must not count as closure. The phase-2 closing record must pass the driver's deterministic outcome-evidence check.

## Reference Notes

The quality signal is the verifier exit code: trailer completeness via `tools/driver/status.py`, plus `assert_phase.py --deterministic` on `reference/assert_state.json`. `reference/expected.json` is the status row and trailer list. `reference/SUMMARY.md` states the same bar in prose. A person reading a diff is not the score. Session classify is not the score.

## Reproduction

Stand-in for the bot path (status → once → assert). The script shells out to those three commands:

```bash
python3 evals/scenarios/trailer-completeness/verify.py
```

Exit 0 is pass. Stdout is one JSON object with `verifier`, `trailers`, and `cost`. With no `ANTHROPIC_API_KEY` or `CURSOR_API_KEY`, `cost.available` is false. Dry-run `cost_usd: 0` is not a provider cost.

`baseline/outcome.json` is the frozen first stdout. Do not overwrite it.
