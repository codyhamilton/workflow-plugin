# Unit report: 5-03 — Plugin `bin/yakka` and hook edge

**Status:** done

## What was built

- Renamed `plugins/yakka/bin/workflow` → `bin/yakka`; step-4 source build uses `$ROOT/../../packages/yakka` and `./cmd/yakka`; cache/assets use `yakka-*` naming; `YAKKA_ROOT`, `YAKKA_BIN`, `YAKKA_RELEASE_URL`; `bin/VERSION` → `0.2.0`; `SHA256SUMS` asset names repointed (checksums unchanged until `5-05` rebuild).
- Claude/Codex hooks, `prefetch-version.sh`, `.mcp.json`, `.codex-mcp.json`: `bin/yakka`, MCP server key `yakka`. `cursor.json` unchanged (`./script/...` only).
- `packages/hooklog/spool.sh` and `plugins/yakka/script/spool.sh`: `YAKKA_*` queue/hooklog env defaults (`~/.local/share/yakka/queue`), drain kick via `bin/yakka`. Plugin copy keeps plugin-root fallback (`$root/bin/yakka`); package copy uses repo layout (`$root/plugins/yakka/bin/yakka`).
- `hooklog.py` store paths → `YAKKA_HOOKLOG_*` / `~/.local/share/yakka/hooklog`. Hooklog tests updated for `YAKKA_*`.

## Done evidence

**Cold build** (`plugins/yakka`, empty `HOME` cache, `YAKKA_RELEASE_URL=http://127.0.0.1:9`, `PATH` with Go 1.27.1):

```
yakka 0.2.0 74c96af90acb
```

**Step-4 probe:** `test -f ../../packages/yakka/go.mod` from `plugins/yakka` → exit 0.

**Cursor hook shape:** all `hooks/cursor.json` commands start with `./script/` (`cursor_ok`).

**Tests:**

```
python3 -m unittest discover -s packages/hooklog/tests -p 'test_spool_queue.py' -v
→ Ran 20 tests in ~9s — OK
```

## Deviations

1. **Plugin vs package `spool.sh`** — Not byte-identical after sync: only `start_drain` fallback differs so marketplace-only installs resolve `bin/yakka` under the plugin root (brief sync intent; behaviour requirement).
2. **`test_write_surfaces` / `test_surfaces` / `test_hooklog`** — Updated for `YAKKA_*` and `packages/yakka` build path alongside `test_spool_queue.py` (not listed in done evidence but same owned package).
3. **`SHA256SUMS` hashes** — Filenames only; digests still match pre-rename `workflow-*` blobs until `5-05` publishes `yakka-*` assets (expected; download step falls through to source build).

## Unfinished work

- Release pipeline and fresh checksums: `5-05`.
- Residual `workflow` product naming in hooklog README prose (e.g. `client.toml` path) — later phases / migration docs.

## Known problems

None for this unit’s contract. Source build requires Go ≥ 1.27.1 on `PATH` when system `go` is older (`GOTOOLCHAIN=local`).
