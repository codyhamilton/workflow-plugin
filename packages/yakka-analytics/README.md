# yakka-analytics

**Consumers** — the `yakka` binary that embeds the built static site.

**Build** — `npm run build`.

**Test** — `npm test` and `npm run test:e2e`.

**Release** — embedded in `packages/yakka`.

SvelteKit static site copied into `packages/yakka/internal/serve/site/` during `tools/release/build.sh`.
