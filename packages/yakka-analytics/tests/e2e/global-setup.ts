// Builds the yakka binary, starts a local-mode and a remote `yakka serve` (registry bearer),
// posts the fixture to both, and writes base URLs and the issued token to state.json.
import { type ChildProcess, execFileSync, spawn } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { homedir, tmpdir } from 'node:os';
import path from 'node:path';
import { FACTS } from './fixture';

const PREVIEW_PORT = Number(process.env.E2E_PORT) || 4391; // keep in step with playwright.config.ts
const E2E_TENANT = 'e2e';
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
		if (proc.exitCode !== null) throw new Error(`yakka serve exited early (${proc.exitCode})`);
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

function issueRegistryToken(dataDir: string): string {
	const plain = `wk_${randomBytes(32).toString('base64url')}`;
	const hash = createHash('sha256').update(plain).digest('hex');
	const id = randomBytes(16).toString('hex');
	const now = new Date();
	const expires = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000);
	mkdirSync(dataDir, { recursive: true });
	const doc = {
		version: 1,
		policy: { mode: 'everyone' },
		sessions: {},
		owners: { [E2E_TENANT]: '1' },
		token_hashes: [
			{
				id,
				tenant: E2E_TENANT,
				scope: 'read_write',
				hash,
				github_id: 1,
				expires_at: expires.toISOString(),
				revoked: false,
				created_at: now.toISOString()
			}
		]
	};
	writeFileSync(path.join(dataDir, 'registry.json'), JSON.stringify(doc));
	return plain;
}

export default async function globalSetup() {
	const tmp = mkdtempSync(path.join(tmpdir(), 'wa-e2e-'));
	// TYPESAFE_API_KEY is cleared: with it set, serve would send the fixture to the real screening
	// service and verdicts would be "pass"; without it every verdict is "unscreened", deterministically.
	const env = {
		...process.env,
		PATH: `${homedir()}/.local/go/bin:${process.env.PATH}`,
		TYPESAFE_API_KEY: '',
		GOTOOLCHAIN: 'auto'
	};
	const bin = path.join(tmp, 'yakka');
	execFileSync('go', ['build', '-o', bin, './cmd/yakka'], {
		cwd: path.join(repoRoot, 'packages/yakka'),
		env,
		stdio: 'inherit'
	});

	const keyedData = path.join(tmp, 'keyed');
	const key = issueRegistryToken(keyedData);

	const procs: ChildProcess[] = [];
	const start = async (name: string, extra: Record<string, string> = {}, remote = false) => {
		const port = await freePort();
		const serveEnv = {
			...env,
			YAKKA_SERVE_ADDR: remote ? `0.0.0.0:${port}` : `127.0.0.1:${port}`,
			YAKKA_SERVE_DATA: path.join(tmp, name),
			YAKKA_CHECKS_DIR: path.join(repoRoot, 'packages/yakka/catalogue'),
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
		const local = await start('local');
		const keyed = await start(
			'keyed',
			{
				YAKKA_SERVE_DATA: keyedData,
				YAKKA_SERVE_CORS_ORIGINS: `http://127.0.0.1:${PREVIEW_PORT}`,
				GITHUB_OAUTH_CLIENT_ID: 'e2e-cid',
				GITHUB_OAUTH_CLIENT_SECRET: 'e2e-csec',
				YAKKA_PUBLIC_URL: 'https://collector.e2e.test'
			},
			true
		);
		const body = JSON.stringify({ facts: FACTS });
		for (const [base, auth] of [
			[local, ''],
			[keyed, `Bearer ${key}`]
		] as const) {
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
