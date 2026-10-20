import { expect, test } from '@playwright/test';
import { serveState, trackRequests, useServe } from './helpers';

const DAY_MS = 30 * 24 * 60 * 60 * 1000;

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
	const { local } = serveState();
	await page.addInitScript((base) => {
		localStorage.setItem('yakka-analytics-base', base);
		localStorage.setItem('yakka-analytics-key', 'e2e-local-stay');
	}, local);
});

test('landing shows two day trends over the default thirty-day window', async ({ page }) => {
	const query = trackRequests(page, /analytics\/query/);
	await page.goto('/');
	expect(new URL(page.url()).search).toBe('');

	await expect(page.getByTestId('landing-trend-hook_events')).toBeVisible();
	await expect(page.getByTestId('landing-trend-cost_usd')).toBeVisible();
	await expect(page.getByTestId('landing-trend-hook_events')).toHaveAttribute('data-ready', 'true');
	await expect(page.getByTestId('landing-trend-cost_usd')).toHaveAttribute('data-ready', 'true');

	await expect(page.getByTestId('overview-summary')).toHaveCount(0);
	await expect(page.getByTestId('overview-heatmap')).toHaveCount(0);
	await expect(page.getByTestId('summary-conversations')).toHaveCount(0);

	const urls = query.urls().filter((u) => new URL(u).searchParams.get('measure'));
	expect(urls).toHaveLength(2);
	const params = urls.map((u) => new URL(u).searchParams);
	const measures = params.map((p) => p.get('measure')).sort();
	expect(measures).toEqual(['cost_usd', 'hook_events']);
	for (const p of params) {
		expect(p.get('bucket')).toBe('day');
		expect(p.get('repo_id')).toBeNull();
	}
	const from = params[0].get('from');
	const to = params[0].get('to');
	expect(from).toBeTruthy();
	expect(to).toBeTruthy();
	expect(params[1].get('from')).toBe(from);
	expect(params[1].get('to')).toBe(to);
	expect(Date.parse(to!) - Date.parse(from!)).toBe(DAY_MS);
});

test('repo_id in the URL does not change landing query params', async ({ page }) => {
	const query = trackRequests(page, /analytics\/query/);
	await page.goto('/?repo_id=r1');
	await expect(page.getByTestId('landing-trend-hook_events')).toBeVisible();
	await expect(page.getByTestId('landing-trend-cost_usd')).toBeVisible();
	for (const u of query.urls()) {
		expect(new URL(u).searchParams.get('repo_id')).toBeNull();
	}
});
