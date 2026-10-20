import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('/conversation does not render the legacy run timeline', async ({ page }) => {
	await page.goto('/conversation?id=c5');
	await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
	await expect(page.getByTestId('timeline-out')).toHaveCount(0);
});
