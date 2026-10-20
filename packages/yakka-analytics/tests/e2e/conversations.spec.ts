import { expect, test } from '@playwright/test';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('/conversations does not render the legacy runs table', async ({ page }) => {
	await page.goto('/conversations');
	await expect(page.getByTestId('legacy-route-stub')).toBeVisible();
	await expect(page.getByTestId('conv-row')).toHaveCount(0);
});
