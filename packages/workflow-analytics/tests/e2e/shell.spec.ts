import { expect, test } from '@playwright/test';
import { FILTER_REPO } from './fixture';
import { trackRequests, useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('a preset survives navigating to another route and a reload', async ({ page }) => {
	await page.goto('/');
	await page.getByTestId('preset-7d').click();
	await expect(page).toHaveURL(/range=7d/);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');

	await page.getByRole('link', { name: 'Hooks' }).click();
	await expect(page).toHaveURL(/\/hooks\?.*range=7d/);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');

	await page.reload();
	await expect(page).toHaveURL(/\/hooks\?.*range=7d/);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');
});

test('the custom range inputs set from and to', async ({ page }) => {
	await page.goto('/');
	const from = page.getByTestId('filter-from');
	const to = page.getByTestId('filter-to');

	await from.fill('2026-01-01');
	await from.dispatchEvent('change');
	await expect(page).toHaveURL(/from=2026-01-01/);

	await to.fill('2026-01-31');
	await to.dispatchEvent('change');
	await expect(page).toHaveURL(/to=2026-01-31/);
	await expect(page.getByTestId('preset-30d')).toHaveAttribute('aria-pressed', 'false');
});

test('removing a chip drops it from the URL', async ({ page }) => {
	await page.goto(`/?repo_id=${FILTER_REPO}`);
	await expect(page.getByTestId(`chip-repo_id-${FILTER_REPO}`)).toBeVisible();
	await page.getByTestId(`chip-remove-repo_id-${FILTER_REPO}`).click();
	await expect(page.getByTestId(`chip-repo_id-${FILTER_REPO}`)).toHaveCount(0);
	await expect(page).not.toHaveURL(/repo_id/);
});

test('the layout fits 1024x768 without a horizontal scrollbar', async ({ page }) => {
	await page.setViewportSize({ width: 1024, height: 768 });
	await page.goto('/?range=7d');
	await expect(page.getByTestId('preset-7d')).toBeVisible();
	const { scroll, inner } = await page.evaluate(() => ({
		scroll: document.documentElement.scrollWidth,
		inner: window.innerWidth
	}));
	expect(scroll).toBeLessThanOrEqual(inner);
});

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

test('a burst of preset clicks reaches the facets endpoint at most twice', async ({ page }) => {
	const facets = trackRequests(page, '/v1/analytics/facets');
	await page.goto('/');
	await expect(page.getByTestId('preset-7d')).toBeVisible();
	await page.waitForTimeout(400); // let the initial facets request settle
	facets.reset();

	// Five clicks in one task: the client debounces the burst into at most a couple of requests.
	await page.evaluate(() => {
		for (const id of ['today', '24h', '7d', '30d', '90d']) {
			(document.querySelector(`[data-testid="preset-${id}"]`) as HTMLButtonElement).click();
		}
	});
	await expect(page.getByTestId('preset-90d')).toHaveAttribute('aria-pressed', 'true');
	await page.waitForTimeout(600);
	expect(facets.count()).toBeLessThanOrEqual(2);
});
