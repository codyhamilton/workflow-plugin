import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('/repos does not render the legacy repo comparison report', async ({ page }) => {
	await page.goto('/repos');
	await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
	await expect(page.getByTestId('repos-table')).toHaveCount(0);
});
