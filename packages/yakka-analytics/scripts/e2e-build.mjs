// Build the site with secrets present in the environment, then prove they did not reach build/.
import { spawnSync } from 'node:child_process';

const key = process.env.E2E_KEY;
const dummy = process.env.E2E_DUMMY_TOKEN;
if (!key || !dummy) {
	console.error('e2e-build: E2E_KEY and E2E_DUMMY_TOKEN must be set');
	process.exit(1);
}
const env = {
	...process.env,
	WORKFLOW_SERVE_KEYS: `e2e=${key}`,
	PUBLIC_E2E_TOKEN: dummy,
	VITE_E2E_TOKEN: dummy,
	E2E_FORBIDDEN: [key, dummy].join(',')
};
for (const script of ['build', 'check:bundle']) {
	const r = spawnSync('npm', ['run', script], { env, stdio: 'inherit' });
	if (r.status !== 0) process.exit(r.status ?? 1);
}
