import { expect, test } from '@playwright/test';
import { serveState, useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('/explore does not mount Perspective or the old explore UI', async ({ page }) => {
	await page.goto('/explore');
	await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
	await expect(page.locator('perspective-viewer')).toHaveCount(0);
	await expect(page.getByTestId('explore-count')).toHaveCount(0);
});

test('the overview does not load Perspective', async ({ page }) => {
	const { local } = serveState();
	await page.addInitScript((base) => {
		localStorage.setItem('yakka-analytics-base', base);
		localStorage.setItem('yakka-analytics-key', 'e2e-local-stay');
	}, local);
	const urls: string[] = [];
	page.on('request', (r) => urls.push(r.url()));
	await page.goto('/');
	await expect(page.getByTestId('landing-trend-hook_events')).toBeVisible();
	expect(urls.filter((u) => u.includes('perspective') || u.split('?')[0].endsWith('.wasm'))).toEqual([]);
});
