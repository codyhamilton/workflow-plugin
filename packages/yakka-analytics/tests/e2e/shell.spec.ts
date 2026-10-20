import { expect, test } from '@playwright/test';
import { trackRequests, useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('the layout fits 1024x768 without a horizontal scrollbar', async ({ page }) => {
	await page.setViewportSize({ width: 1024, height: 768 });
	await page.goto('/');
	await expect(page.getByTestId('landing-trend-hook_events')).toBeVisible();
	const { scroll, inner } = await page.evaluate(() => ({
		scroll: document.documentElement.scrollWidth,
		inner: window.innerWidth
	}));
	expect(scroll).toBeLessThanOrEqual(inner);
});

const ANALYSIS_LIGHT = { bg: '#f4f6fa', text: '#1a2332' };
const ANALYSIS_DARK = { bg: '#12151c', text: '#d8dee9' };
const SOLARIZED_BG = new Set(['#002b36', '#fdf6e3']);

async function readRootThemeVars(page: import('@playwright/test').Page) {
	return page.evaluate(() => {
		const cs = getComputedStyle(document.documentElement);
		const token = (name: string) => cs.getPropertyValue(name).trim();
		return { bg: token('--bg'), text: token('--text') };
	});
}

test('the dark scheme swaps the background token', async ({ page }) => {
	await page.goto('/');
	const light = await page.evaluate(() =>
		getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()
	);
	await page.emulateMedia({ colorScheme: 'dark' });
	await expect
		.poll(() => page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()))
		.not.toBe(light);
});

test('system dark mode uses analysis tokens on overview and settings', async ({ page }) => {
	await page.addInitScript(() => localStorage.removeItem('yakka-analytics-theme'));
	await page.emulateMedia({ colorScheme: 'dark' });
	for (const path of ['/', '/settings']) {
		await page.goto(path);
		await expect.poll(async () => (await readRootThemeVars(page)).bg).toBe(ANALYSIS_DARK.bg);
		const vars = await readRootThemeVars(page);
		expect(vars.text).toBe(ANALYSIS_DARK.text);
		expect(SOLARIZED_BG.has(vars.bg)).toBe(false);
	}
});

test('choosing Light updates analysis tokens without reload and survives reload', async ({ page }) => {
	await page.goto('/');
	await page.getByTestId('theme-light').click();
	await expect.poll(async () => (await readRootThemeVars(page)).bg).toBe(ANALYSIS_LIGHT.bg);
	expect((await readRootThemeVars(page)).text).toBe(ANALYSIS_LIGHT.text);
	await page.reload();
	expect((await readRootThemeVars(page)).bg).toBe(ANALYSIS_LIGHT.bg);
	expect((await readRootThemeVars(page)).text).toBe(ANALYSIS_LIGHT.text);
});

test('system mode follows a later OS colour-scheme change', async ({ page }) => {
	await page.addInitScript(() => localStorage.removeItem('yakka-analytics-theme'));
	await page.emulateMedia({ colorScheme: 'light' });
	await page.goto('/');
	expect((await readRootThemeVars(page)).bg).toBe(ANALYSIS_LIGHT.bg);
	await page.getByTestId('theme-system').click();
	await page.emulateMedia({ colorScheme: 'dark' });
	await expect.poll(async () => (await readRootThemeVars(page)).bg).toBe(ANALYSIS_DARK.bg);
});

test('a burst of preset clicks reaches the facets endpoint at most twice', async ({ page }) => {
	const facets = trackRequests(page, '/v1/analytics/facets');
	await page.goto('/?ask=trend&measure=hook_events&bucket=day');
	await expect(page.getByTestId('preset-7d')).toBeVisible();
	await page.waitForTimeout(400);
	facets.reset();

	await page.evaluate(() => {
		for (const id of ['today', '24h', '7d', '30d', '90d']) {
			(document.querySelector(`[data-testid="preset-${id}"]`) as HTMLButtonElement).click();
		}
	});
	await expect(page.getByTestId('preset-90d')).toHaveAttribute('aria-pressed', 'true');
	await page.waitForTimeout(600);
	expect(facets.count()).toBeLessThanOrEqual(2);
});

test('the header has no report nav links and save view is absent on overview', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByRole('link', { name: 'Trends' })).toHaveCount(0);
	await expect(page.getByRole('link', { name: 'Dashboards' })).toHaveCount(0);
	await expect(page.getByRole('link', { name: 'Builder' })).toHaveCount(0);
	await expect(page.getByTestId('saveview-save')).toHaveCount(0);
});

test('legacy report URLs show the retirement stub, not the old chart chrome', async ({ page }) => {
	for (const path of ['/trends', '/builder', '/dashboards']) {
		await page.goto(path);
		await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
		await expect(page.getByTestId('trends-chart')).toHaveCount(0);
		await expect(page.getByTestId('builder-chart')).toHaveCount(0);
		await expect(page.getByTestId('dash-tile')).toHaveCount(0);
		await expect(page.getByTestId('saveview-save')).toHaveCount(0);
	}
});
