import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

test('a dashboard is built, persists, reorders, exports and imports', async ({ page, browser }) => {
	await useServe(page, 'local');

	// Two saved views, made with the 5-06 save control on the Hooks route.
	await page.goto('/hooks?range=7d');
	await page.getByTestId('saveview-name').fill('hooks-7d');
	await page.getByTestId('saveview-save').click();
	await page.goto('/hooks?range=30d');
	await page.getByTestId('saveview-name').fill('hooks-30d');
	await page.getByTestId('saveview-save').click();

	// Create a dashboard and make sure it is the selected one.
	await page.goto('/dashboards');
	await page.getByTestId('dash-name').fill('daily');
	await page.getByTestId('dash-create').click();
	await expect(page).toHaveURL(/\/dashboards\?d=/);
	await expect(page.getByTestId('dash-item').filter({ hasText: 'daily' })).toBeVisible();

	// Add both views as tiles.
	await page.getByTestId('dash-add-select').selectOption({ label: 'hooks-7d' });
	await page.getByTestId('dash-add').click();
	await page.getByTestId('dash-add-select').selectOption({ label: 'hooks-30d' });
	await page.getByTestId('dash-add').click();
	await expect(page.getByTestId('dash-tile')).toHaveCount(2);

	// The first tile frames the saved view and its chart mounts in the iframe's own document.
	const frame = page.frameLocator('[data-testid="dash-tile"] iframe').first();
	await expect(frame.getByTestId('hooks-harness')).toHaveAttribute('data-ready', 'true', {
		timeout: 15000
	});

	// A reload keeps the dashboard (through the store) and the selected id (through the URL).
	await page.reload();
	await expect(page.getByTestId('dash-item')).toHaveCount(1);
	await expect(page.getByTestId('dash-tile')).toHaveCount(2);

	// Reorder: move the first tile down; the iframe titles swap.
	const titles = () =>
		page
			.getByTestId('dash-tile')
			.locator('iframe')
			.evaluateAll((frames) => frames.map((f) => f.getAttribute('title')));
	const before = await titles();
	await page.getByTestId('dash-tile-down').first().click();
	await expect.poll(titles).not.toEqual(before);
	expect(await titles()).toEqual([before[1], before[0]]);

	// Remove the first tile.
	await page.getByTestId('dash-tile-remove').first().click();
	await expect(page.getByTestId('dash-tile')).toHaveCount(1);

	// Export: the download is `<name>.json` with the version, name and the remaining view's name/url.
	const [download] = await Promise.all([
		page.waitForEvent('download'),
		page.getByTestId('dash-export').click()
	]);
	expect(download.suggestedFilename()).toBe('daily.json');
	const json = JSON.parse(readFileSync((await download.path())!, 'utf8'));
	expect(json).toMatchObject({ version: 1, name: 'daily' });
	expect(json.views).toHaveLength(1);
	expect(json.views[0]).toMatchObject({ name: 'hooks-7d', url: '/hooks?range=7d' });

	// Import that JSON into a fresh browser profile and see the same dashboard and tile.
	const ctx = await browser.newContext();
	const fresh = await ctx.newPage();
	await useServe(fresh, 'local');
	await fresh.goto('/dashboards');
	await fresh.getByTestId('dash-import-text').fill(JSON.stringify(json));
	await fresh.getByTestId('dash-import').click();
	await expect(fresh).toHaveURL(/\/dashboards\?d=/);
	await expect(fresh.getByTestId('dash-item').filter({ hasText: 'daily' })).toBeVisible();
	await expect(fresh.getByTestId('dash-tile')).toHaveCount(1);
	await ctx.close();
});

test('a malformed import shows the error and creates nothing', async ({ page }) => {
	await useServe(page, 'local');
	await page.goto('/dashboards');
	await page.getByTestId('dash-import-text').fill('{"version":1');
	await page.getByTestId('dash-import').click();
	await expect(page.getByTestId('dash-import-error')).toBeVisible();
	await expect(page.getByTestId('dash-item')).toHaveCount(0);
});
