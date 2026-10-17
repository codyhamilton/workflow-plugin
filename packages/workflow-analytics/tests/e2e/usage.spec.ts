import { expect, test } from '@playwright/test';
import { costLabel } from '../../src/lib/format';
import { USAGE_ALL, USAGE_BY_MODEL } from './fixture';
import { brush, clickBar, expectSettled, trackRequests, useServe } from './helpers';

test.use({ timezoneId: 'UTC' });

const SONNET = 'anthropic/claude-sonnet-5-5';
const QWEN = 'ollama-maxctx/qwen3-coder:30b-a3b-q4_K_M';
const OPUS = 'claude-opus-5-5';

// `clickBar` reads bar N''s geometry from the chart box after showing the table. Open the table
// first and wait so its own toggle (which counts rows before Svelte flushes) does not race.
async function openTable(page: import('@playwright/test').Page, testid: string) {
	await page.getByTestId(`${testid}-table-toggle`).click();
	await expect(page.getByTestId(`${testid}-table`).locator('tbody tr').first()).toBeVisible();
}

// The priced Sonnet bar is first in `usage-cost-by-model` (clickBar's index is the bar band, 0-based).
const SONNET_BAR = 0;

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('usage table shows per-model calls, tokens and cost, and the unpriced banner', async ({ page }) => {
	await page.goto('/usage');
	const sonnet = USAGE_BY_MODEL[SONNET];
	await expect(page.getByTestId(`usage-${SONNET}-calls`)).toHaveText(String(sonnet.calls));
	await expect(page.getByTestId(`usage-${SONNET}-unpriced`)).toHaveText('0');
	await expect(page.getByTestId(`usage-${SONNET}-cost`)).toHaveText('$0.02');
	await expect(page.getByTestId(`usage-${QWEN}-cost`)).toHaveText('unpriced');
	const opus = USAGE_BY_MODEL[OPUS];
	await expect(page.getByTestId(`usage-${OPUS}-cost`)).toHaveText(
		costLabel({ cost: opus.cost_usd, unpriced: opus.unpriced, calls: opus.calls })
	);
	await expect(page.getByTestId('usage-unpriced-banner')).toHaveText(
		`${USAGE_ALL.unpriced_calls} of ${USAGE_ALL.model_calls} calls are unpriced`
	);
});

test('a window with only unpriced calls never shows $0', async ({ page }) => {
	await page.goto(`/usage?model=${encodeURIComponent(QWEN)}`);
	await expect(page.getByTestId(`usage-${QWEN}-cost`)).toHaveText('unpriced');
	await expect(page.getByTestId('usage-unpriced-banner')).toHaveText('1 of 1 calls are unpriced');
	await expect(page.getByTestId('usage-table')).not.toContainText('$0.00');
});

test('?model= narrows the table to that model', async ({ page }) => {
	await page.goto(`/usage?model=${encodeURIComponent(SONNET)}`);
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await expect(page.getByTestId(`usage-row-${QWEN}`)).toHaveCount(0);
	await expect(page.getByTestId('usage-unpriced-banner')).toHaveCount(0);
});

test('clicking a cost bar filters by model; shift-click excludes', async ({ page }) => {
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await openTable(page, 'usage-cost-by-model');
	await clickBar(page, 'usage-cost-by-model', SONNET_BAR);
	await expect(page.getByTestId(`chip-model-${SONNET}`)).toBeVisible();
	await clickBar(page, 'usage-cost-by-model', SONNET_BAR, { shift: true });
	await expect(page.getByTestId(`chip-model-${SONNET}`)).toHaveAttribute('data-mode', 'exclude');
});

test('__other__ is inert', async ({ page }) => {
	await page.route('**/v1/analytics/query*', (route) => {
		const url = new URL(route.request().url());
		const dims = url.searchParams.getAll('dim');
		const rows = dims.includes('model')
			? [
					{ k: [SONNET], v: 0.02 },
					{ k: ['__other__'], v: 0.5 }
				]
			: [];
		return route.fulfill({
			json: { measure: url.searchParams.get('measure') ?? 'cost_usd', bucket: 'none', dims, rows },
			headers: { 'access-control-allow-origin': '*' }
		});
	});
	await page.goto('/usage');
	await expect(page.getByTestId('usage-row-__other__')).toBeVisible();
	await openTable(page, 'usage-cost-by-model');
	await clickBar(page, 'usage-cost-by-model', 2);
	await expect(page.locator('[data-testid^="chip-"]')).toHaveCount(0);
});

test('one load issues seven /analytics/query requests and one distribution', async ({ page }) => {
	const queries = trackRequests(page, /analytics\/query/);
	const dist = trackRequests(page, /analytics\/distribution/);
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await expectSettled(page);
	expect(queries.count()).toBe(7);
	expect(dist.count()).toBe(1);
});

test('switching 30d to 90d issues each distinct query once', async ({ page }) => {
	// Slow responses as on the real ledger: a facet response landing after the window change must not
	// re-run the effect and supersede queries already in flight.
	await page.route('**/v1/analytics/query*', async (route) => {
		await new Promise((r) => setTimeout(r, 700));
		try {
			await route.continue();
		} catch {
			/* the client aborts superseded requests */
		}
	});
	const queries = trackRequests(page, /analytics\/query/);
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible({ timeout: 15000 });
	await page.waitForTimeout(2500);
	queries.reset();
	await page.getByTestId('preset-90d').click();
	await page.waitForTimeout(3500);
	const urls = queries.urls().map((u) => new URL(u).pathname + new URL(u).search);
	expect(urls.length).toBe(new Set(urls).size);
	expect(urls.length).toBe(7);
});

test('a preset change settles within 1 s', async ({ page }) => {
	await page.goto('/usage');
	await expectSettled(page);
	const t0 = Date.now();
	await page.getByTestId('preset-7d').click();
	await expectSettled(page);
	expect(Date.now() - t0).toBeLessThan(1000);
});

test('All time: every query carries from/to, none carries all=1, none is a 400', async ({ page }) => {
	const queries: string[] = [];
	const statuses: { url: string; status: number }[] = [];
	page.on('request', (r) => {
		if (/analytics\/query/.test(r.url())) queries.push(r.url());
	});
	page.on('response', (r) => {
		if (/analytics\/query/.test(r.url())) statuses.push({ url: r.url(), status: r.status() });
	});
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	queries.length = 0;
	statuses.length = 0;
	await page.getByTestId('preset-all').click();
	await expectSettled(page);
	await page.waitForTimeout(1000);
	expect(queries.length).toBeGreaterThan(0);
	for (const url of queries) {
		const u = new URL(url);
		expect(u.searchParams.get('all'), url).toBeNull();
		expect(u.searchParams.get('from'), url).not.toBeNull();
		expect(u.searchParams.get('to'), url).not.toBeNull();
	}
	for (const { url, status } of statuses) expect(status, `${url} -> ${status}`).not.toBe(400);
});

test('cost-by-model table formats cost by unit and keeps exact values', async ({ page }) => {
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await openTable(page, 'usage-cost-by-model');
	const table = page.getByTestId('usage-cost-by-model-table');
	const priced = table.locator('tbody tr', { hasText: SONNET }).locator('td').nth(1);
	await expect(priced).toHaveText('$0.02');
	expect(Number(await priced.getAttribute('data-value'))).toBeCloseTo(0.0223, 6);
	const unpriced = table.locator('tbody tr', { hasText: QWEN }).locator('td').nth(1);
	await expect(unpriced).toHaveText('unpriced');
	await expect(unpriced).toHaveAttribute('data-value', '0');
});

test('every table row reports USAGE_BY_MODEL calls, and no zero-call row shows tokens', async ({ page }) => {
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	for (const [model, v] of Object.entries(USAGE_BY_MODEL)) {
		await expect(page.getByTestId(`usage-${model}-calls`)).toHaveText(String(v.calls));
	}
	const rows = page.getByTestId('usage-table').locator('tbody tr');
	const parse = (t: string) => (t === '—' ? 0 : Number(t.replace(/[^0-9.-]/g, '')) || 0);
	for (let i = 0; i < (await rows.count()); i++) {
		const cells = rows.nth(i).locator('td');
		const calls = parse(await cells.nth(0).innerText());
		const tin = parse(await cells.nth(2).innerText());
		const tout = parse(await cells.nth(3).innerText());
		expect(calls === 0 && (tin > 0 || tout > 0), `row ${i} calls 0 beside tokens`).toBe(false);
	}
});

test('a model with no cost data shows unpriced, never $0.00', async ({ page }) => {
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-${QWEN}-cost`)).toHaveText('unpriced');
	const opus = USAGE_BY_MODEL[OPUS];
	await expect(page.getByTestId(`usage-${OPUS}-cost`)).toHaveText(
		costLabel({ cost: opus.cost_usd, unpriced: opus.unpriced, calls: opus.calls })
	);
	await expect(page.getByTestId('usage-table')).not.toContainText('$0.00');
});

test('the five by-model table requests ask for top=100', async ({ page }) => {
	const seen: { measure: string; top: string | null }[] = [];
	await page.route('**/v1/analytics/query*', async (route) => {
		const u = new URL(route.request().url());
		if (u.searchParams.getAll('dim').includes('model') && u.searchParams.get('bucket') === 'none') {
			seen.push({ measure: u.searchParams.get('measure') ?? '', top: u.searchParams.get('top') });
		}
		await route.continue();
	});
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await expectSettled(page);
	expect(seen.map((s) => s.measure).sort()).toEqual(
		['cost_usd', 'model_calls', 'tokens_in', 'tokens_out', 'unpriced_calls'].sort()
	);
	for (const s of seen) expect(s.top, s.measure).toBe('100');
});

test('tokens-over-time query includes dim=model', async ({ page }) => {
	const seen: string[][] = [];
	page.on('request', (r) => {
		if (!/analytics\/query/.test(r.url())) return;
		const u = new URL(r.url());
		if (u.searchParams.get('measure') === 'tokens_out' && u.searchParams.get('bucket') !== 'none') {
			seen.push(u.searchParams.getAll('dim'));
		}
	});
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await expectSettled(page);
	expect(seen.length).toBeGreaterThan(0);
	for (const dims of seen) expect(dims).toContain('model');
});

test('distribution measure control switches measure and requests cost_usd', async ({ page }) => {
	const seen: string[] = [];
	page.on('response', (r) => {
		if (/analytics\/distribution/.test(r.url())) seen.push(r.url());
	});
	await page.goto('/usage');
	await expect(page.getByTestId('usage-distribution')).toBeVisible();
	await expectSettled(page);
	expect(seen.some((u) => new URL(u).searchParams.get('measure') === 'cost_usd')).toBe(true);
	const switched = page.waitForResponse(
		(r) => /analytics\/distribution/.test(r.url()) && new URL(r.url()).searchParams.get('measure') === 'tokens_in'
	);
	await page.getByTestId('usage-distribution-measure').selectOption('tokens_in');
	await switched;
	await expectSettled(page);
});

test('brushing usage-over-time sets from/to and reloads distribution', async ({ page }) => {
	await page.goto('/usage');
	await expectSettled(page);
	await page.getByTestId('usage-over-time-table-toggle').click();
	await expect(page.getByTestId('usage-over-time-table')).toBeVisible();
	await page.getByTestId('usage-over-time-table-toggle').click();
	await expect(page.getByTestId('usage-over-time').locator('.echart svg')).toBeVisible();
	const distAfter = page.waitForResponse((r) => /analytics\/distribution/.test(r.url()));
	await brush(page, 'usage-over-time', 0.25, 0.75);
	await expect(page).toHaveURL(/[?&]from=/);
	const u = new URL(page.url());
	expect(u.searchParams.get('from')).toBeTruthy();
	expect(u.searchParams.get('to')).toBeTruthy();
	await expectSettled(page);
	await distAfter;
});

test('model bar click filters time series and distribution via chip', async ({ page }) => {
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await expect(page.getByTestId(`usage-row-${QWEN}`)).toBeVisible();
	await openTable(page, 'usage-cost-by-model');
	await clickBar(page, 'usage-cost-by-model', SONNET_BAR);
	await expect(page.getByTestId(`chip-model-${SONNET}`)).toBeVisible();
	await expect(page.getByTestId(`usage-row-${QWEN}`)).toHaveCount(0);
	await expectSettled(page);
});

test('empty model key shows (none) and is inert; __other__ shows other models with a truncation note', async ({ page }) => {
	await page.route('**/v1/analytics/query*', (route) => {
		const u = new URL(route.request().url());
		const dims = u.searchParams.getAll('dim');
		const rows = dims.includes('model')
			? [
					{ k: [''], v: 1 },
					{ k: ['__other__'], v: 0.5 }
				]
			: [];
		return route.fulfill({
			json: { measure: u.searchParams.get('measure') ?? 'cost_usd', bucket: 'none', dims, rows },
			headers: { 'access-control-allow-origin': '*' }
		});
	});
	await page.goto('/usage');
	await expect(page.getByTestId('usage-row-')).toContainText('(none)');
	await expect(page.getByTestId('usage-row-__other__')).toContainText('other models');
	await expect(page.getByTestId('usage-truncated-note')).toBeVisible();
	await page.getByTestId('usage-row-').click();
	await page.getByTestId('usage-row-__other__').click();
	await expect(page.locator('[data-testid^="chip-"]')).toHaveCount(0);
});
