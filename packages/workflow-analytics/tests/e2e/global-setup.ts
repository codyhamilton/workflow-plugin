// Builds the workflow binary, starts a local-mode and a keyed `workflow serve`, posts the fixture to
// both, and writes their base URLs and the key to a JSON file the specs read (path in E2E_STATE).
import { type ChildProcess, execFileSync, spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { homedir, tmpdir } from 'node:os';
import path from 'node:path';
import { FACTS } from './fixture';

const PREVIEW_PORT = 4391; // keep in step with playwright.config.ts
const repoRoot = path.resolve(import.meta.dirname, '../../../..');

function freePort(): Promise<number> {
	return new Promise((resolve, reject) => {
		const s = createServer();
		s.once('error', reject);
		s.listen(0, '127.0.0.1', () => {
			const { port } = s.address() as { port: number };
			s.close(() => resolve(port));
		});
	});
}

async function waitHealth(base: string, proc: ChildProcess) {
	for (let i = 0; i < 100; i++) {
		if (proc.exitCode !== null) throw new Error(`workflow serve exited early (${proc.exitCode})`);
		try {
			if ((await fetch(`${base}/v1/health`)).ok) return;
		} catch {
			/* not listening yet */
		}
		await new Promise((r) => setTimeout(r, 100));
	}
	throw new Error(`serve at ${base} never became healthy`);
}

async function waitScreened(base: string) {
	for (let i = 0; i < 200; i++) {
		const h = (await (await fetch(`${base}/v1/health`)).json()) as { pending: number };
		if (h.pending === 0) return;
		await new Promise((r) => setTimeout(r, 100));
	}
	throw new Error(`serve at ${base} still has pending screens`);
}

export default async function globalSetup() {
	const key = process.env.E2E_KEY;
	if (!key) throw new Error('E2E_KEY is not set (playwright.config.ts sets it)');
	const tmp = mkdtempSync(path.join(tmpdir(), 'wa-e2e-'));
	// TYPESAFE_API_KEY is cleared: with it set, serve would send the fixture to the real screening
	// service and verdicts would be "pass"; without it every verdict is "unscreened", deterministically.
	const env = { ...process.env, PATH: `${homedir()}/.local/go/bin:${process.env.PATH}`, TYPESAFE_API_KEY: '' };
	const bin = path.join(tmp, 'workflow');
	execFileSync('go', ['build', '-o', bin, './cmd/workflow'], { cwd: path.join(repoRoot, 'tools/workflow'), env, stdio: 'inherit' });

	const procs: ChildProcess[] = [];
	const start = async (extra: Record<string, string>, name: string) => {
		const port = await freePort();
		const serveEnv = {
			...env,
			WORKFLOW_SERVE_ADDR: `127.0.0.1:${port}`,
			WORKFLOW_SERVE_DATA: path.join(tmp, name),
			WORKFLOW_CHECKS_DIR: path.join(repoRoot, 'tools/quality'),
			...extra
		};
		const p = spawn(bin, ['serve'], { env: serveEnv, stdio: 'ignore' });
		procs.push(p);
		const base = `http://127.0.0.1:${port}`;
		await waitHealth(base, p);
		return base;
	};
	const stop = () => {
		for (const p of procs) p.kill('SIGTERM');
		rmSync(tmp, { recursive: true, force: true });
	};

	try {
		const local = await start({}, 'local');
		const keyed = await start(
			{ WORKFLOW_SERVE_KEYS: `e2e=${key}`, WORKFLOW_SERVE_CORS_ORIGINS: `http://127.0.0.1:${PREVIEW_PORT}` },
			'keyed'
		);
		const body = JSON.stringify({ facts: FACTS });
		for (const [base, auth] of [[local, ''], [keyed, `Bearer ${key}`]] as const) {
			const res = await fetch(`${base}/v1/ingest`, {
				method: 'POST',
				headers: { 'content-type': 'application/json', ...(auth ? { authorization: auth } : {}) },
				body
			});
			if (!res.ok) throw new Error(`ingest ${base}: ${res.status} ${await res.text()}`);
			await waitScreened(base);
		}
		const state = path.join(tmp, 'state.json');
		writeFileSync(state, JSON.stringify({ local, keyed, key }));
		process.env.E2E_STATE = state;
	} catch (e) {
		stop();
		throw e;
	}
	return stop;
}
