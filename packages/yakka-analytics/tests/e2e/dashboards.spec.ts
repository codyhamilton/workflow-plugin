import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('/dashboards does not render the legacy dashboard grid', async ({ page }) => {
	await page.goto('/dashboards');
	await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
	await expect(page.getByTestId('dash-tile')).toHaveCount(0);
	await expect(page.getByTestId('saveview-save')).toHaveCount(0);
});
