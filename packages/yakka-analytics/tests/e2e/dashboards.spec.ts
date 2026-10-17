import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';
import { presetWindow } from '../../src/lib/presets';
import { useServe } from './helpers';

test.use({ timezoneId: 'UTC' });

function tileNames(page: import('@playwright/test').Page) {
	return page
		.getByTestId('dash-tile')
		.locator('.tile-name')
		.evaluateAll((els) => els.map((e) => e.textContent?.trim() ?? ''));
}

function queryUrlsFrom(page: import('@playwright/test').Page, urls: string[]) {
	page.on('request', (r) => {
		const u = r.url();
		if (u.includes('/v1/analytics/query')) urls.push(u);
	});
}

function expectQueryWindow(urls: string[], win: { from: Date; to: Date }) {
	const qs = urls.map((u) => new URL(u).searchParams);
	expect(qs.length, 'expected tile query requests').toBeGreaterThan(0);
	for (const params of qs) {
		expect(params.get('from')).toBe(win.from.toISOString());
		expect(params.get('to')).toBe(win.to.toISOString());
	}
}

test('a dashboard is built, persists, reorders, exports and imports', async ({ page, browser }) => {
	await useServe(page, 'local');

	await page.goto('/hooks?range=7d');
	await page.getByTestId('saveview-name').fill('hooks-7d');
	await page.getByTestId('saveview-save').click();
	await page.goto('/hooks?range=30d');
	await page.getByTestId('saveview-name').fill('hooks-30d');
	await page.getByTestId('saveview-save').click();

	await page.goto('/dashboards');
	await page.getByTestId('dash-name').fill('daily');
	await page.getByTestId('dash-create').click();
	await expect(page).toHaveURL(/\/dashboards\?d=/);
	await expect(page.getByTestId('dash-item').filter({ hasText: 'daily' })).toBeVisible();

	await page.getByTestId('dash-add-select').selectOption({ label: 'hooks-7d' });
	await page.getByTestId('dash-add').click();
	await page.getByTestId('dash-add-select').selectOption({ label: 'hooks-30d' });
	await page.getByTestId('dash-add').click();
	await expect(page.getByTestId('dash-tile')).toHaveCount(2);

	const firstTile = page.getByTestId('dash-tile').first();
	await expect(firstTile.getByTestId('hooks-harness')).toHaveAttribute('data-ready', 'true', {
		timeout: 15_000
	});

	await page.reload();
	await expect(page.getByTestId('dash-item')).toHaveCount(1);
	await expect(page.getByTestId('dash-tile')).toHaveCount(2);

	const before = await tileNames(page);
	await page.getByTestId('dash-tile-down').first().click();
	await expect.poll(tileNames.bind(null, page)).not.toEqual(before);
	expect(await tileNames(page)).toEqual([before[1], before[0]]);

	await page.getByTestId('dash-tile-remove').first().click();
	await expect(page.getByTestId('dash-tile')).toHaveCount(1);

	const [download] = await Promise.all([
		page.waitForEvent('download'),
		page.getByTestId('dash-export').click()
	]);
	expect(download.suggestedFilename()).toBe('daily.json');
	const json = JSON.parse(readFileSync((await download.path())!, 'utf8'));
	expect(json).toMatchObject({ version: 2, name: 'daily' });
	expect(json.tiles).toHaveLength(1);
	expect(json.tiles[0]).toMatchObject({ name: 'hooks-7d', report: 'hooks', params: {} });

	const ctx = await browser.newContext({ timezoneId: 'UTC' });
	const fresh = await ctx.newPage();
	await useServe(fresh, 'local');
	await fresh.goto('/dashboards');
	await fresh.getByTestId('dash-import-text').fill(JSON.stringify(json));
	await fresh.getByTestId('dash-import').click();
	await expect(fresh).toHaveURL(/\/dashboards\?d=/);
	await expect(fresh.getByTestId('dash-item').filter({ hasText: 'daily' })).toBeVisible();
	await expect(fresh.getByTestId('dash-tile')).toHaveCount(1);
	await expect(fresh.getByTestId('dash-tile').getByTestId('hooks-harness')).toHaveAttribute(
		'data-ready',
		'true',
		{ timeout: 15_000 }
	);
	await ctx.close();
});

test('dashboard tiles share the dashboard window, not saved page ranges', async ({ page }) => {
	await useServe(page, 'local');

	await page.goto('/hooks?range=7d');
	await page.getByTestId('saveview-name').fill('hooks-7d');
	await page.getByTestId('saveview-save').click();
	await page.goto('/hooks?range=30d');
	await page.getByTestId('saveview-name').fill('hooks-30d');
	await page.getByTestId('saveview-save').click();

	await page.goto('/dashboards');
	await page.getByTestId('dash-name').fill('shared-win');
	await page.getByTestId('dash-create').click();
	const dashUrl = page.url();
	await page.getByTestId('dash-add-select').selectOption({ label: 'hooks-7d' });
	await page.getByTestId('dash-add').click();
	await page.getByTestId('dash-add-select').selectOption({ label: 'hooks-30d' });
	await page.getByTestId('dash-add').click();

	const dashId = new URL(dashUrl).searchParams.get('d');
	const urls: string[] = [];
	queryUrlsFrom(page, urls);
	await page.goto(`/dashboards?range=7d&d=${dashId}`);

	const win7 = presetWindow('7d', new Date(), 'UTC')!;
	await expect(page.getByTestId('dash-tile')).toHaveCount(2);
	await expect(page.getByTestId('dash-tile').first().getByTestId('hooks-harness')).toHaveAttribute(
		'data-ready',
		'true',
		{ timeout: 15_000 }
	);
	await expect(page.getByTestId('dash-tile').nth(1).getByTestId('hooks-harness')).toHaveAttribute(
		'data-ready',
		'true',
		{ timeout: 15_000 }
	);
	expectQueryWindow(urls, win7);
});

test('changing the dashboard preset refetches hooks tiles with the new window', async ({ page }) => {
	await useServe(page, 'local');

	await page.goto('/hooks?range=7d');
	await page.getByTestId('saveview-name').fill('hooks-only');
	await page.getByTestId('saveview-save').click();

	await page.goto('/dashboards?range=7d');
	await page.getByTestId('dash-name').fill('win-change');
	await page.getByTestId('dash-create').click();
	await page.getByTestId('dash-add-select').selectOption({ label: 'hooks-only' });
	await page.getByTestId('dash-add').click();
	await expect(page.getByTestId('dash-tile').getByTestId('hooks-harness')).toHaveAttribute(
		'data-ready',
		'true',
		{ timeout: 15_000 }
	);

	const win30 = presetWindow('30d', new Date(), 'UTC')!;
	const urls: string[] = [];
	queryUrlsFrom(page, urls);
	const refetch = page.waitForResponse(
		(r) => r.url().includes('/v1/analytics/query') && r.url().includes('from=')
	);
	await page.getByTestId('preset-30d').click();
	await refetch;
	await expect(page.getByTestId('dash-tile').getByTestId('hooks-harness')).toHaveAttribute(
		'data-ready',
		'true',
		{ timeout: 15_000 }
	);
	expectQueryWindow(urls, win30);
});

test('importing 13 v2 tiles keeps 12 and reports one drop', async ({ page }) => {
	await useServe(page, 'local');
	await page.goto('/dashboards');

	const tiles = Array.from({ length: 13 }, (_, i) => ({
		name: `tile-${i}`,
		report: 'hooks',
		params: {},
		w: 1
	}));
	const json = { version: 2, name: 'cap-board', tiles };

	await page.getByTestId('dash-import-text').fill(JSON.stringify(json));
	await page.getByTestId('dash-import').click();
	await expect(page).toHaveURL(/\/dashboards\?d=/);
	await expect(page.getByTestId('dash-tile')).toHaveCount(12);
	await expect(page.getByTestId('dash-import-drops')).toContainText('1 tile dropped');
});

test('legacy v1 URL import keeps chart params and drops unknown paths', async ({ page }) => {
	await useServe(page, 'local');
	await page.goto('/dashboards');

	const json = {
		version: 1,
		name: 'legacy-import',
		views: [
			{ name: 'usage-cost', url: '/usage?range=7d&measure=cost_usd&repo_id=r1' },
			{ name: 'orphan', url: '/not-a-report?x=1' }
		]
	};

	await page.getByTestId('dash-import-text').fill(JSON.stringify(json));
	await page.getByTestId('dash-import').click();
	await expect(page).toHaveURL(/\/dashboards\?d=/);
	await expect(page.getByTestId('dash-tile')).toHaveCount(1);
	await expect(page.getByTestId('dash-import-drops')).toContainText('1 view dropped');

	const raw = await page.evaluate(() => localStorage.getItem('workflow-analytics-views:views'));
	const views = JSON.parse(raw!) as { name: string; report: string; params: Record<string, string> }[];
	const usage = views.find((v) => v.name === 'usage-cost');
	expect(usage?.report).toBe('usage');
	expect(usage?.params).toEqual({ measure: 'cost_usd' });
});

test('a malformed import shows the error and creates nothing', async ({ page }) => {
	await useServe(page, 'local');
	await page.goto('/dashboards');
	await page.getByTestId('dash-import-text').fill('{"version":1');
	await page.getByTestId('dash-import').click();
	await expect(page.getByTestId('dash-import-error')).toBeVisible();
	await expect(page.getByTestId('dash-item')).toHaveCount(0);
});
