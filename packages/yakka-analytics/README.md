# yakka-analytics

**Consumers** — the `workflow` binary that embeds the built static site.

**Build** — `npm run build`.

**Test** — `npm test` and `npm run test:e2e`.

**Release** — embedded in `packages/workflow`.

SvelteKit static site copied into `packages/workflow/internal/serve/site/` during `tools/release/build.sh`.
