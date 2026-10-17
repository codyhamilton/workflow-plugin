# Unit report: 2-05 — JavaScript and Node test consumers

**Status:** `done` (analytics e2e: `needs context`)

## What changed

- `packages/workflow-analytics/tests/e2e/global-setup.ts`: `go build` cwd `tools/workflow` → `packages/workflow`; `WORKFLOW_CHECKS_DIR` → `packages/workflow/catalogue`.
- `packages/workflow-analytics/tests/hosted/global-setup.ts`: `WORKFLOW_CHECKS_DIR` → `packages/workflow/catalogue`.
- `packages/opencode-workflow-hooks/README.md` and `src/index.ts`: path prose/comments `tools/hooklog` → `packages/hooklog` (behaviour unchanged).
- `packages/opencode-workflow-hooks/tests/test_hooks.mjs`: `spoolSh` resolves `packages/hooklog/spool.sh` (path string only; policy test unchanged).

JEV signal log default (`tools/driver/.jev-signal-log.jsonl`) not touched (Phase 4).

## Commands run

| Check | Before | After |
|-------|--------|-------|
| `node --test packages/opencode-workflow-hooks/tests/test_hooks.mjs` (system Node v22.14.0) | fail — `ERR_UNKNOWN_FILE_EXTENSION` on `src/index.ts` | fail — same on v22.14.0 |
| Same command with Node **v22.23.3** (`~/.nvm/versions/node/v22.23.3/bin/node`) | fail (import); with `--experimental-strip-types`: 7 pass / 1 fail (`tools/hooklog/spool.sh` missing) | **8 pass / 0 fail** |
| `node --experimental-strip-types --test …` (v22.14.0) | 7 pass / 1 fail (spool path) | **8 pass / 0 fail** |
| `rg 'tools/workflow\|tools/hooklog\|tools/quality' packages/workflow-analytics/tests packages/opencode-workflow-hooks` | 5 hits | **no hits** |
| `go build -o /tmp/wf-test-bin ./cmd/workflow` in `packages/workflow` | (not run before) | **ok** |
| Analytics e2e (`npm run test:e2e` in `packages/workflow-analytics`) | — | **not run** — no `node_modules` / lockfile in checkout |

**Orchestrator e2e command (when deps installed):**

```bash
cd packages/workflow-analytics && npm ci && npm run test:e2e
```

Hosted variant: `npm run test:hosted` (requires `WORKFLOW_BIN` per hosted `global-setup.ts`).

## Deviations

- Done evidence cites bare `node --test …`; package README and `package.json` use `--experimental-strip-types` on Node &lt;22.18. Evidence recorded with Node **v22.23.3** bare command (8/8). System default **v22.14.0** still requires `--experimental-strip-types` or a newer Node.
- Analytics e2e not executed in VM; repoint-only verified via `rg` and successful `go build` from new cwd.

## Contradictions

- Brief done evidence vs OpenCode README: bare `node --test` vs `--experimental-strip-types` on older Node — resolved by using Node ≥22.18 per README (v22.23.3 passes bare command).
- DESIGN.md Phase 2 outcome lists bare `node --test`; same Node version caveat applies.

## Problems outside done evidence

None beyond analytics e2e `needs context` above.
