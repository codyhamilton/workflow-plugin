import { defineConfig } from '@playwright/test';

// Runs against a binary built by tools/release/build.sh (WORKFLOW_BIN). The global setup starts its
// `serve` and exports the origin as HOSTED_BASE; the spec uses it as baseURL.
export default defineConfig({
	testDir: 'tests/hosted',
	testMatch: '**/*.spec.ts',
	fullyParallel: false,
	workers: 1,
	reporter: 'list',
	globalSetup: './tests/hosted/global-setup.ts'
});
