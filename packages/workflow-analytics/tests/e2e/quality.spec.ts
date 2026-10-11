import { expect, test, type Page } from '@playwright/test';
import { serveState, trackRequests, useServe } from './helpers';

type ScoreRow = { name: string; n: number; min: number; p25: number; median: number; p75: number; max: number };
type BaseRow = { n: number; p25: number; median: number; p75: number };

// The e2e serve has no scorer, so every quality window is empty (n = 0). The distribution-chart
// checks hand the page scored rows so the chart has something to draw; a test then asserts the
// chart's table against these handed-in numbers, never against the chart code.
async function stubQuality(page: Page, checks: ScoreRow[], bases: Record<string, BaseRow>): Promise<void> {
	const cors = { 'access-control-allow-origin': '*' };
	await page.route('**/v1/analytics/scores*', (r) =>
		r.fulfill({ json: { kind: 'design', checks }, headers: cors })
	);
	await page.route('**/v1/baselines*', (r) =>
		r.fulfill({ json: { kind: 'design', checks: bases }, headers: cors })
	);
}

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

test('a kind tab sets the URL kind and every scores request carries exactly one kind', async ({ page }) => {
	const brief = await catalog('brief');
	const seen = trackRequests(page, '/v1/analytics/scores');
	await page.goto('/quality');
	await expect(page.getByTestId('q-row').first()).toBeVisible();
	for (const u of seen.urls()) expect(new URL(u).searchParams.getAll('kind')).toEqual(['design']);
	seen.reset();
	await page.getByTestId('quality-kind-brief').click();
	await expect(page).toHaveURL(/kind=brief/);
	await expect(page.getByTestId('quality-kind-brief')).toHaveAttribute('aria-pressed', 'true');
	await expect(page.getByTestId(`q-${brief[0]}-w-n`)).toBeVisible();
	expect(seen.count()).toBe(1);
	expect(new URL(seen.urls()[0]).searchParams.getAll('kind')).toEqual(['brief']);
});

test('switching kind renders within 1 s', async ({ page }) => {
	const brief = await catalog('brief');
	await page.goto('/quality');
	await expect(page.getByTestId('q-row').first()).toBeVisible();
	const t0 = Date.now();
	await page.getByTestId('quality-kind-brief').click();
	await expect(page.getByTestId(`q-${brief[0]}-w-n`)).toBeVisible();
	expect(Date.now() - t0).toBeLessThan(1000);
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

test('quality-dist: one box row per scored check, the baseline median as the marker', async ({ page }) => {
	const checks: ScoreRow[] = [
		{ name: 'd.alpha', n: 11, min: 0.1, p25: 0.2, median: 0.3, p75: 0.4, max: 0.5 },
		{ name: 'd.unscored', n: 0, min: 0, p25: 0, median: 0, p75: 0, max: 0 },
		{ name: 'd.gamma', n: 7, min: 0.6, p25: 0.7, median: 0.8, p75: 0.9, max: 1 }
	];
	// Only alpha has an all-time baseline; gamma's marker cell stays blank.
	await stubQuality(page, checks, { 'd.alpha': { n: 21, p25: 0.15, median: 0.35, p75: 0.55 } });
	await page.goto('/quality');
	const chart = page.getByTestId('quality-dist');
	await expect(chart).toBeVisible();
	await expect(chart).toHaveAttribute('data-ready', 'true');
	await page.getByTestId('quality-dist-table-toggle').click();
	const rows = page.getByTestId('quality-dist-table').locator('tbody tr');
	await expect(rows).toHaveCount(2); // d.unscored has n = 0, so it has no row
	const alpha = rows.nth(0).locator('td');
	await expect(alpha.nth(0)).toHaveText('d.alpha');
	for (const [i, v] of [0.1, 0.2, 0.3, 0.4, 0.5, 0.35].entries())
		await expect(alpha.nth(i + 1), `alpha cell ${i}`).toHaveAttribute('data-value', String(v));
	const gamma = rows.nth(1).locator('td');
	await expect(gamma.nth(0)).toHaveText('d.gamma');
	await expect(gamma.nth(6)).toHaveText('');
});

test('quality-dist re-renders when the kind switches', async ({ page }) => {
	const cors = { 'access-control-allow-origin': '*' };
	const byKind: Record<string, ScoreRow> = {
		design: { name: 'd.only', n: 3, min: 0.1, p25: 0.2, median: 0.3, p75: 0.4, max: 0.5 },
		brief: { name: 'b.only', n: 5, min: 0.2, p25: 0.3, median: 0.4, p75: 0.5, max: 0.6 }
	};
	await page.route('**/v1/analytics/scores*', (r) => {
		const kind = new URL(r.request().url()).searchParams.get('kind') ?? 'design';
		return r.fulfill({ json: { kind, checks: [byKind[kind]] }, headers: cors });
	});
	await page.route('**/v1/baselines*', (r) =>
		r.fulfill({ json: { kind: 'design', checks: {} }, headers: cors })
	);
	await page.goto('/quality');
	await page.getByTestId('quality-dist-table-toggle').click();
	const rows = page.getByTestId('quality-dist-table').locator('tbody tr');
	await expect(rows).toHaveCount(1);
	await expect(rows.nth(0).locator('td').nth(0)).toHaveText('d.only');
	await page.getByTestId('quality-kind-brief').click();
	await expect(page).toHaveURL(/kind=brief/);
	await expect(rows.nth(0).locator('td').nth(0)).toHaveText('b.only');
});

test('quality-dist renders in the dark theme', async ({ page }) => {
	await stubQuality(
		page,
		[{ name: 'd.alpha', n: 4, min: 0.1, p25: 0.2, median: 0.3, p75: 0.4, max: 0.5 }],
		{}
	);
	await page.emulateMedia({ colorScheme: 'dark' });
	await page.goto('/quality');
	const chart = page.getByTestId('quality-dist');
	await expect(chart).toHaveAttribute('data-ready', 'true');
	await expect(chart).toHaveAttribute('data-theme', 'dark');
});
