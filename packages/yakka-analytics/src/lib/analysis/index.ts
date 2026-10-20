/**
 * Analysis frame and tokens for dashboard routes in phase 2.
 *
 * Color and space tokens live in `tokens.css` as `--bg`, `--text`, `--space-*`, etc.
 * Light/dark/system preference uses `localStorage` key `yakka-analytics-theme` and sets
 * `data-theme="light"|"dark"` on `document.documentElement` (see `src/lib/charts/theme.ts`).
 */
export { default as IdentityPanel } from './IdentityPanel.svelte';
export { default as RouteSurface } from './RouteSurface.svelte';
export { isAnalysisFramePath, isLegacyReportPath } from './routes';
