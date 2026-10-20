import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('/trends does not render the legacy time-series report', async ({ page }) => {
	await page.goto('/trends?range=7d&metric=commits&group=harness&bucket=day');
	await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
	await expect(page.getByTestId('trends-chart')).toHaveCount(0);
});
