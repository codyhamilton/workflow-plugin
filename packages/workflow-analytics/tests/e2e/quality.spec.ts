import { expect, test } from '@playwright/test';
import { serveState, useServe } from './helpers';

const F = ['n', 'min', 'p25', 'median', 'p75', 'max'] as const;
const BF = ['n', 'p25', 'median', 'p75'] as const;

async function catalog(kind: string): Promise<string[]> {
	const r = await (await fetch(`${serveState().local}/v1/analytics/scores?kind=${kind}`)).json();
	return r.checks.map((c: { name: string }) => c.name);
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('zero-scorer serve: every design check listed with zero window and blank baseline', async ({ page }) => {
	const names = await catalog('design');
	expect(names.length).toBeGreaterThan(0);
	await page.goto('/quality');
	await expect(page.getByTestId('q-row')).toHaveCount(names.length);
	for (const n of names) {
		for (const f of F) await expect(page.getByTestId(`q-${n}-w-${f}`), `${n} w ${f}`).toHaveText('0');
		for (const f of BF) await expect(page.getByTestId(`q-${n}-b-${f}`), `${n} b ${f}`).toHaveText('');
	}
});

test('?kind=brief switches to the brief checks', async ({ page }) => {
	const design = await catalog('design');
	const brief = await catalog('brief');
	await page.goto('/quality?kind=brief');
	await expect(page.getByTestId('q-row')).toHaveCount(brief.length);
	await expect(page.getByTestId(`q-${brief[0]}-w-n`)).toBeVisible();
	if (!design.includes(brief[0])) await expect(page.getByTestId(`q-${design[0]}-w-n`)).toHaveCount(0);
});

test('stubbed responses: every cell shows its own field; only GETs are made', async ({ page }) => {
	const methods: string[] = [];
	page.on('request', (r) => {
		if (r.url().includes('/v1/')) methods.push(r.method());
	});
	const scores = {
		kind: 'design',
		checks: [
			{ name: 'd.alpha', n: 11, min: 0.1, p25: 0.2, median: 0.3, p75: 0.4, max: 0.5 },
			{ name: 'd.beta', n: 12, min: 0.6, p25: 0.7, median: 0.8, p75: 0.9, max: 1 }
		]
	};
	const base = { kind: 'design', checks: { 'd.alpha': { n: 21, p25: 0.15, median: 0.35, p75: 0.55 } } };
	await page.route('**/v1/analytics/scores*', (r) => r.fulfill({ json: scores, headers: { 'access-control-allow-origin': '*' } }));
	await page.route('**/v1/baselines*', (r) => r.fulfill({ json: base, headers: { 'access-control-allow-origin': '*' } }));
	await page.goto('/quality?kind=design');
	for (const c of scores.checks)
		for (const f of F) await expect(page.getByTestId(`q-${c.name}-w-${f}`)).toHaveText(String(c[f]));
	for (const f of BF)
		await expect(page.getByTestId(`q-d.alpha-b-${f}`)).toHaveText(String(base.checks['d.alpha'][f]));
	for (const f of BF) await expect(page.getByTestId(`q-d.beta-b-${f}`)).toHaveText('');
	expect(methods.length).toBeGreaterThan(0);
	expect(methods.every((m) => m === 'GET')).toBe(true);
});
