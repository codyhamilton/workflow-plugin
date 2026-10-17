import { expect, test } from '@playwright/test';
import { costLabel } from '../../src/lib/format';
import { FILTER_REPO, SUMMARY_ALL, SUMMARY_R1, USAGE_ALL } from './fixture';
import { expectSettled, trackRequests, useServe } from './helpers';

type P = import('@playwright/test').Page;
async function expectNumbers(page: P, want: Record<string, number>) {
	for (const [k, v] of Object.entries(want)) await expect(page.getByTestId(`summary-${k}`), k).toHaveText(String(v));
}
// The usage fields the page renders as plain number tiles; tokens/cost are asserted via their
// dedicated tiles, so they are left out of this map.
const USAGE_TILES = { model_calls: USAGE_ALL.model_calls, unpriced_calls: USAGE_ALL.unpriced_calls };
// The fixture stores grouped summary counts flat ("by_kind-design"); the serve nests them. Rebuild
// the nested shape for the mocked summary response.
const nested = (field: string) =>
	Object.fromEntries(
		Object.entries(SUMMARY_ALL)
			.filter(([k]) => k.startsWith(`${field}-`))
			.map(([k, v]) => [k.slice(field.length + 1), v])
	);

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test.describe('KPI links', () => {
	test('conversations tile keeps repo_id on /conversations', async ({ page }) => {
		await page.goto(`/?repo_id=${FILTER_REPO}`);
		await expect(page.getByTestId('summary-conversations')).toBeVisible();
		await page.locator('a').filter({ has: page.getByTestId('summary-conversations') }).click();
		await expect(page).toHaveURL(new RegExp(`/conversations\\?.*repo_id=${FILTER_REPO}`));
	});

	test('artifact versions tile sets metric on /trends', async ({ page }) => {
		await page.goto(`/?repo_id=${FILTER_REPO}`);
		await expect(page.getByTestId('summary-artifact_versions')).toBeVisible();
		await page.locator('a').filter({ has: page.getByTestId('summary-artifact_versions') }).click();
		await expect(page).toHaveURL(new RegExp(`/trends\\?.*repo_id=${FILTER_REPO}.*metric=artifact_versions`));
	});

	test('hook events tile lands on /hooks', async ({ page }) => {
		await page.goto(`/?repo_id=${FILTER_REPO}`);
		await expect(page.getByTestId('summary-hook_events')).toBeVisible();
		await page.locator('a').filter({ has: page.getByTestId('summary-hook_events') }).click();
		await expect(page).toHaveURL(new RegExp(`/hooks\\?.*repo_id=${FILTER_REPO}`));
	});

	test('cost tile lands on /usage', async ({ page }) => {
		await page.goto(`/?repo_id=${FILTER_REPO}`);
		await expect(page.getByTestId('summary-cost_usd')).toBeVisible();
		await page.locator('a').filter({ has: page.getByTestId('summary-cost_usd') }).click();
		await expect(page).toHaveURL(new RegExp(`/usage\\?.*repo_id=${FILTER_REPO}`));
	});
});

test('overview shows the fixture numbers for the whole window', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, SUMMARY_ALL);
	await expectNumbers(page, USAGE_TILES);
	await expect(page.getByTestId('summary-tokens')).toHaveText(String(USAGE_ALL.tokens_in + USAGE_ALL.tokens_out));
	await expect(page.getByTestId('summary-tokens_cache_read')).toHaveText(String(USAGE_ALL.tokens_cache_read));
	await expect(page.getByTestId('summary-cost_usd')).toHaveText(
		costLabel({
			cost: USAGE_ALL.cost_usd,
			unpriced: USAGE_ALL.unpriced_calls,
			calls: USAGE_ALL.model_calls
		})
	);
});

test('repo_id in the URL filters, and survives a reload', async ({ page }) => {
	await page.goto(`/?repo_id=${FILTER_REPO}`);
	await expectNumbers(page, SUMMARY_R1);
	await page.reload();
	expect(new URL(page.url()).searchParams.getAll('repo_id')).toEqual([FILTER_REPO]);
	await expectNumbers(page, SUMMARY_R1);
});

test('choosing a repo in the filter bar changes the URL and the numbers', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, SUMMARY_ALL);
	await page.getByTestId('filter-repo_id').selectOption(FILTER_REPO);
	await expect(page).toHaveURL(new RegExp(`repo_id=${FILTER_REPO}`));
	await expectNumbers(page, SUMMARY_R1);
	await page.goBack();
	await expectNumbers(page, SUMMARY_ALL);
});

test('no filter control offers an empty option', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, SUMMARY_ALL);
	for (const name of ['repo_id', 'harness', 'kind', 'plan']) {
		const opts = await page.getByTestId(`filter-${name}`).locator('option').evaluateAll((os) =>
			os.map((o) => ({ value: (o as HTMLOptionElement).value, text: (o.textContent ?? '').trim() }))
		);
		expect(opts.length, name).toBeGreaterThan(0);
		for (const o of opts) {
			expect(o.value, name).not.toBe('');
			expect(o.text, name).not.toBe('');
		}
	}
});

test('cost tile never shows $0.00 while calls are unpriced', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByTestId('summary-cost_usd')).toHaveText(
		costLabel({
			cost: USAGE_ALL.cost_usd,
			unpriced: USAGE_ALL.unpriced_calls,
			calls: USAGE_ALL.model_calls
		})
	);
	await expect(page.getByTestId('summary-unpriced_calls')).toHaveText(String(USAGE_ALL.unpriced_calls));
	await page.route('**/analytics/summary*', (route) =>
		route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				...SUMMARY_ALL,
				...USAGE_ALL,
				by_kind: nested('by_kind'),
				by_source: nested('by_source'),
				rejections: nested('rejections'),
				screens: nested('screens'),
				cost_usd: 0,
				model_calls: 3,
				unpriced_calls: 3
			})
		})
	);
	await page.reload();
	await expect(page.getByTestId('summary-cost_usd')).toHaveText('unpriced');
	await expect(page.getByTestId('summary-unpriced_calls')).toHaveText('3');
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
	// An exclude makes the effect wait for the current window's facets; the switch must not then
	// re-run it when the late facet response lands.
	await page.goto(`/?x.repo_id=${FILTER_REPO}`);
	await expect(page.getByTestId('summary-conversations')).toBeVisible({ timeout: 15000 });
	await page.waitForTimeout(2500);
	queries.reset();
	await page.getByTestId('preset-90d').click();
	await page.waitForTimeout(3500);
	const urls = queries.urls().map((u) => new URL(u).pathname + new URL(u).search);
	expect(urls.length).toBe(new Set(urls).size);
	expect(urls.length).toBe(10);
});

test('heatmap reports ready', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByTestId('overview-heatmap')).toHaveAttribute('data-ready', 'true');
});

test('preset click settles within 1s', async ({ page }) => {
	await page.goto('/');
	await expectSettled(page);
	const start = Date.now();
	await page.getByTestId('preset-7d').click();
	await expectSettled(page);
	expect(Date.now() - start).toBeLessThan(1000);
});

test('one summary and at most ten query requests per load', async ({ page }) => {
	const summary = trackRequests(page, /analytics\/summary/);
	const query = trackRequests(page, /analytics\/query/);
	await page.goto('/');
	await expectNumbers(page, SUMMARY_ALL);
	await expectSettled(page);
	await page.waitForTimeout(500);
	expect(summary.count()).toBeLessThanOrEqual(1);
	expect(query.count()).toBeLessThanOrEqual(10);
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
	await page.goto('/');
	await expectSettled(page);
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
