import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('/quality does not render the legacy score distribution report', async ({ page }) => {
	await page.goto('/quality?kind=design');
	await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
	await expect(page.getByTestId('quality-chart')).toHaveCount(0);
});
