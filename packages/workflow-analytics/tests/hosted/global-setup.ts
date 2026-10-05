// Starts the release binary named by WORKFLOW_BIN in local mode, posts the e2e fixture, waits for
// screening to finish, and exports the serve origin as HOSTED_BASE.
import { type ChildProcess, spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { createServer } from 'node:net';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { FACTS } from '../e2e/fixture';

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

export default async function globalSetup() {
	const bin = process.env.WORKFLOW_BIN;
	if (!bin) throw new Error('WORKFLOW_BIN is not set: give the absolute path of a binary built by tools/release/build.sh');
	if (!path.isAbsolute(bin)) throw new Error(`WORKFLOW_BIN must be an absolute path, got ${bin}`);
	const tmp = mkdtempSync(path.join(tmpdir(), 'wa-hosted-'));
	const port = await freePort();
	const base = `http://127.0.0.1:${port}`;
	const proc: ChildProcess = spawn(bin, ['serve'], {
		env: {
			...process.env,
			WORKFLOW_SERVE_ADDR: `127.0.0.1:${port}`,
			WORKFLOW_SERVE_DATA: path.join(tmp, 'data'),
			WORKFLOW_CHECKS_DIR: path.join(repoRoot, 'tools/quality'),
			TYPESAFE_API_KEY: ''
		},
		stdio: 'ignore'
	});
	const stop = () => {
		proc.kill('SIGTERM');
		rmSync(tmp, { recursive: true, force: true });
	};
	try {
		let up = false;
		for (let i = 0; i < 100 && !up; i++) {
			if (proc.exitCode !== null) throw new Error(`workflow serve exited early (${proc.exitCode})`);
			try {
				up = (await fetch(`${base}/v1/health`)).ok;
			} catch {
				/* not listening yet */
			}
			if (!up) await new Promise((r) => setTimeout(r, 100));
		}
		if (!up) throw new Error(`serve at ${base} never became healthy`);
		const res = await fetch(`${base}/v1/ingest`, {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify({ facts: FACTS })
		});
		if (!res.ok) throw new Error(`ingest: ${res.status} ${await res.text()}`);
		for (let i = 0; ; i++) {
			const h = (await (await fetch(`${base}/v1/health`)).json()) as { pending: number };
			if (h.pending === 0) break;
			if (i >= 200) throw new Error('serve still has pending screens');
			await new Promise((r) => setTimeout(r, 100));
		}
		process.env.HOSTED_BASE = base;
	} catch (e) {
		stop();
		throw e;
	}
	return stop;
}
