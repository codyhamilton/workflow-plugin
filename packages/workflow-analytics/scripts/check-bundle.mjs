// Fails if any file under build/ carries a secret: a value listed in E2E_FORBIDDEN (comma-separated),
// or "Bearer " followed by a token literal. "Bearer " followed by a template placeholder, a quote,
// a backtick, `$`, `{` or an identifier-like expression boundary is the client's header code, not a token.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const dir = process.argv[2] ?? 'build';
const forbidden = (process.env.E2E_FORBIDDEN ?? '').split(',').map((s) => s.trim()).filter(Boolean);
// A token literal: 16+ characters of the usual token alphabet directly after "Bearer ".
const literal = /Bearer [A-Za-z0-9._~+/=-]{16,}/g;

function* walk(d) {
	for (const name of readdirSync(d)) {
		const p = join(d, name);
		if (statSync(p).isDirectory()) yield* walk(p);
		else yield p;
	}
}

let files = 0;
const bad = [];
try {
	statSync(dir);
} catch {
	console.error(`check-bundle: ${dir} does not exist`);
	process.exit(1);
}
for (const p of walk(dir)) {
	files++;
	const text = readFileSync(p, 'latin1');
	for (const f of forbidden) if (text.includes(f)) bad.push(`${p}: contains a forbidden value (length ${f.length})`);
	for (const m of text.matchAll(literal)) bad.push(`${p}: Bearer token literal (${m[0].length - 7} chars)`);
}
if (bad.length) {
	console.error('check-bundle: FAILED\n' + bad.join('\n'));
	process.exit(1);
}
console.log(`check-bundle: ok (${files} files, ${forbidden.length} forbidden values)`);
