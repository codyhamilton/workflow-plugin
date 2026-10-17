import { expect, test } from '@playwright/test';
import { expectSettled, useServe } from './helpers';

const DIM_KEYS = [
	'repo_id',
	'harness',
	'kind',
	'plan',
	'norm_event',
	'event',
	'tool',
	'model',
	'source',
	'conversation_id'
] as const;

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('the filter bar exposes all ten shared dimensions', async ({ page }) => {
	await page.goto('/');
	await expectSettled(page);
	for (const key of DIM_KEYS) {
		await expect(page.getByTestId(`filter-${key}`)).toBeVisible();
	}
});

test('selecting a facet-backed harness updates the URL', async ({ page }) => {
	await page.goto('/');
	await expectSettled(page);
	await page.getByTestId('filter-harness').selectOption('claude');
	await expect(page).toHaveURL(/[?&]harness=claude/);
});

test('the conversation_id control labels exclude as unsupported', async ({ page }) => {
	await page.goto('/');
	await expectSettled(page);
	await expect(page.getByTestId('filter-conversation_id-exclude-hint')).toHaveText('Exclude not applied');
});
