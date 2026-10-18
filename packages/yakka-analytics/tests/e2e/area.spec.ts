import { expect, test, type Page } from '@playwright/test';
import { expectSettled, serveState, useServe } from './helpers';

// The fixture days are UTC days; pin the browser zone so the /query buckets land on them.
test.use({ timezoneId: 'UTC' });

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('area chart renders a filled area path and its line stroke', async ({ page }) => {
	await page.goto('/builder?m=cost_usd&d=model&b=day&c=area');
	await expect(page.getByTestId('builder-chart')).toHaveAttribute('data-kind', 'area');
	await expect(page.getByTestId('builder-chart-chart')).toBeVisible();
	await expectSettled(page);
	await expect(
		page.getByTestId('builder-chart-chart').locator('svg path[fill="#268bd2"]').first()
	).toBeVisible();
	await expect(
		page.getByTestId('builder-chart-chart').locator('svg path[stroke="#268bd2"][fill="none"]').first()
	).toBeVisible();
});

test('multiples chart settles in the browser', async ({ page }) => {
	await page.goto('/builder?m=cost_usd&d=model&d=harness&b=day&c=multiples');
	await expect(page.getByTestId('builder-chart')).toHaveAttribute('data-kind', 'multiples');
	await expect(page.getByTestId('builder-chart-panel').first()).toBeVisible();
	await expectSettled(page);
});
