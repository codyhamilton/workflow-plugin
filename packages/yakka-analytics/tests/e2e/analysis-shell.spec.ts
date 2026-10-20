import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

const SOLARIZED_BG = new Set(['#002b36', '#fdf6e3']);

async function readRootTokens(page: import('@playwright/test').Page) {
	return page.evaluate(() => {
		const cs = getComputedStyle(document.documentElement);
		const token = (name: string) => cs.getPropertyValue(name).trim();
		return { bg: token('--bg'), text: token('--text') };
	});
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('logged-in / and /login share analysis --bg and --text', async ({ page }) => {
	await page.goto('/');
	const home = await readRootTokens(page);
	expect(SOLARIZED_BG.has(home.bg)).toBe(false);

	await page.goto('/login');
	const login = await readRootTokens(page);
	expect(login.bg).toBe(home.bg);
	expect(login.text).toBe(home.text);
	expect(SOLARIZED_BG.has(login.bg)).toBe(false);
});

test('/profile uses the same --bg as /', async ({ page }) => {
	await page.goto('/');
	const homeBg = (await readRootTokens(page)).bg;
	await page.goto('/profile');
	expect((await readRootTokens(page)).bg).toBe(homeBg);
});
