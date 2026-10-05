# Report: 3-02 — Release build embeds the site; Pages output

Status: done.

## What was done

- `tools/release/build.sh`: after the Go probe it finds `npm` (else `build.sh: no Node toolchain`, exit 1), runs `npm ci` only if `node_modules/` is absent, then `npm run build` in `packages/workflow-analytics`. It fails naming the path when `build/index.html` is missing or still holds `workflow-analytics-placeholder`. It then replaces the contents of `tools/workflow/internal/serve/site/` with `build/`, and the four `go build`s and sums run as before. A `trap … EXIT` restores `site/` to the saved placeholder `index.html` on success or failure. ldflags, `OUT_DIR`/`SUMS_FILE`, Go probing and the matrix are unchanged.
- `tools/release/test_release.py`: `test_7_build_sh` adds the outer `npm` directory to `PATH` and passes `npm_config_cache` (outer value, else `~/.npm`); it also asserts `git status --porcelain tools/workflow/internal/serve/site` is empty after the run. `Base.env()` itself is unchanged; the extras are set in the test.
- `packages/workflow-analytics/wrangler.toml` (`name`, `pages_build_output_dir = "./build"`); `package.json`/lockfile: `@perspective-dev/server@^5.5.1` (same as the installed client 5.5.1; lockfile change is the one root dependency line) and a `test:hosted` script.
- `playwright.hosted.config.ts`, `tests/hosted/global-setup.ts`, `tests/hosted/hosted.spec.ts` (6 tests). Setup fails fast naming `WORKFLOW_BIN`, starts `serve` locally on a free port with fresh data, posts `FACTS`, waits for `pending` 0 and exports the origin as `HOSTED_BASE`, which the spec uses as `baseURL`.

## Evidence

- Before (binary from the placeholder build): `npm run test:hosted` gave 5 failed, 1 passed (`/v1 stays JSON` passes); `GET /` returned 404 rather than 200.
- After (`OUT_DIR=$T/dist SUMS_FILE=$T/SUMS bash tools/release/build.sh`): exit 0, four binaries; `git status --porcelain tools/workflow/internal/serve/site bin` empty. `WORKFLOW_BIN=$T/dist/workflow-linux-amd64 npm run test:hosted`: 6 passed.
- Failure path: with a stub `npm` that exits 1 on `PATH`, `build.sh` exits 1 with `build.sh: site build failed in <package path>` and `site/` holds only the placeholder `index.html` (git status clean).
- `npm run test:e2e`: 26 passed. `python3 -m unittest tools.release.test_release.BuildTests -v`: OK. `npm run build` writes `build/index.html`.

## Departures from the brief

- The failure check as worded ("PATH without npm") is not reachable on this host: `/usr/bin/npm` and `/usr/bin/node` exist, so `PATH=/usr/bin:/bin` still finds Node. I used a stub `npm` that fails instead. The `no Node toolchain` branch is unexercised here.
- The hosted spec uses `test.use({ baseURL: process.env.HOSTED_BASE })` rather than a config-level `baseURL`, because the free port is only known in global setup.
- While probing the failure case I ran `build.sh` once without `SUMS_FILE`, which rewrote `bin/SHA256SUMS`. I restored it with `git checkout bin/SHA256SUMS`; it is not in the commit.

## Unfinished

Nothing. The orchestrator's uncommitted edit to `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` was left alone and is not in this commit.

## Known problems

- `build.sh` prints the whole `vite build` output; harmless but noisy.
- The DESIGN says "fails if `index.html` is missing". The brief also rejects a build that still holds the placeholder marker, which I implemented. I found no contradiction beyond that.
