# Execution report: 5-03 Spool default flip and drain retirement

Brief 227, execution 28.

## Done

- `tools/hooklog/spool.sh`: the queue is the only path (`${WORKFLOW_QUEUE:-$HOME/.local/share/workflow/queue}`); no-id payloads are dropped; missing or `auto` harness spools nothing (Cursor response unchanged); kick is `$WORKFLOW_BIN drain` or `bash <root>/bin/workflow drain`, detached; with no `flock` (or `WORKFLOW_SPOOL_NOFLOCK=1`) a `mkdir` lock on `<queue>/.kick.d` with a pid check (dead pid or no-pid directory older than a minute is retaken once); `read -N` became `head -c 65536`, `EPOCHREALTIME` became `date +%s.%N` with a `date +%s` fallback. Written via temp file and `mv`, mode 0755 kept.
- Deleted (`git rm`): `drain.py`, `install-drain.sh`, `workflow-hooklog-drain.service`, `workflow-hooklog-drain.timer`.
- `test_spool_queue.py`: new tests for default queue, default queue under HOME, auto/missing harness, default kick target (temp repo copy with stub `bin/workflow`), mkdir fallback (ten concurrent hooks start one drain; dead pid retaken; young no-pid blocks; old no-pid retaken), bash 3.2 lint. Fail-first: before the `spool.sh` change 10 failures and 1 error (default queue, auto harness, kick target, three fallback tests, lint, and the retargeted legacy tests); after, 20 tests OK.
- `test_hooklog.py`: 11 tests OK.
- Go: `go test -count=1 ./...` in `tools/workflow` passes (temp HOME and XDG_CACHE_HOME).

## Deleted tests and why

- `test_spool_queue.py`: `test_no_id_is_unknown` (subject was `unknown-` naming); `DRAIN` helper and the `drain.py --once` half of `test_fixture_payloads_named_by_id_and_drain` (now `test_fixture_payloads_named_by_id`, queue names only); `test_files_land_in_queue` / `test_no_id_not_spooled` stay (GoPath).
- `test_hooklog.py`: `test_claude_prompt_and_tool`, `test_cursor_events_and_verdict`, `test_hook_returns_without_drain_and_keeps_fire_time`, `test_legacy_record_shim_spools`, `test_drain_retains_while_service_down_then_delivers_once`, `test_unparseable_spool_file_is_quarantined`, `TestAutoHarness.test_auto_routes_to_harness_dir`: each asserted `drain.py` delivery or the `auto` harness path. `drain()` and `DRAIN` helpers removed; `test_garbage_never_fails` retargeted to the queue; `test_hook_spools_to_queue_only` added.

## Departures and known problems

- The brief's last grep expects only `test_surfaces.py` and `test_artifact_submit_surfaces.py`; it actually lists `tools/hooklog/hooklog.py` (a comment or help text mentioning `drain.py`) and `test_surfaces.py`. `hooklog.py` is untouchable here; the stale reference is left for whoever owns it.
- bash 3.2 compliance is static only (no bash 3.2 available).
- Live effect: Cursor events now go to `~/.local/share/workflow/queue` and each kick starts `bin/workflow drain`, which exits while no `client.toml` exists. Not exercised against the real home.
- `test_surfaces.py` and `test_artifact_submit_surfaces.py` are expected to fail until 5-05.
