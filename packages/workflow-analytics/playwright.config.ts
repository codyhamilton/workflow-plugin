import { randomBytes } from 'node:crypto';
import { defineConfig } from '@playwright/test';

// The preview origin is fixed so the keyed serve can list it in WORKFLOW_SERVE_CORS_ORIGINS.
export const PREVIEW_PORT = 4391;

// Generated once in the main process; workers inherit them through the environment.
process.env.E2E_KEY ??= randomBytes(16).toString('hex'); // 32 hex chars: the keyed serve's tenant key
process.env.E2E_DUMMY_TOKEN ??= 'e2e-dummy-' + randomBytes(8).toString('hex');

export default defineConfig({
	testDir: 'tests/e2e',
	testMatch: '**/*.spec.ts',
	fullyParallel: false,
	workers: 1,
	reporter: 'list',
	globalSetup: './tests/e2e/global-setup.ts',
	use: { baseURL: `http://127.0.0.1:${PREVIEW_PORT}` },
	// Playwright starts webServer before globalSetup, so the build and the bundle check run in this
	// command: the build sees the key and a dummy token in its environment and must not embed them.
	webServer: {
		command: `node scripts/e2e-build.mjs && npx vite preview --host 127.0.0.1 --port ${PREVIEW_PORT} --strictPort`,
		url: `http://127.0.0.1:${PREVIEW_PORT}/`,
		reuseExistingServer: false,
		timeout: 180_000
	}
});
