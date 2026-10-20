import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('/usage does not render the legacy usage report', async ({ page }) => {
	await page.goto('/usage?range=7d');
	await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
	await expect(page.getByTestId('usage-model-table')).toHaveCount(0);
});
