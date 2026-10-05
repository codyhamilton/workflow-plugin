import { expect, test, type Page } from '@playwright/test';
import { DAYS, FILTER_REPO, HOOK_EVENTS_BY_DAY } from './fixture';
import { useServe } from './helpers';

// Hand-counted from the fixture facts: hook events per harness per day (whole window, then repo r1).
const BY_HARNESS = {
	claude: { [DAYS.d5]: 2, [DAYS.d4]: 1, [DAYS.d1]: 1 },
	cursor: { [DAYS.d2]: 1, [DAYS.d1]: 1 }
};
const BY_HARNESS_R1 = {
	claude: { [DAYS.d5]: 2, [DAYS.d4]: 1, [DAYS.d1]: 1 },
	cursor: { [DAYS.d1]: 1 }
};

async function expectCells(page: Page, key: string, want: Record<string, number>) {
	for (const [t, n] of Object.entries(want)) {
		await expect(page.getByTestId(`series-${key}-${t}`), `${key} ${t}`).toHaveText(String(n));
	}
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('trends shows the per-day hook_events counts', async ({ page }) => {
	await page.goto('/trends');
	await expectCells(page, 'all', HOOK_EVENTS_BY_DAY);
});

test('group=harness shows one series per harness; repo_id filters and survives a reload', async ({ page }) => {
	await page.goto('/trends?metric=hook_events&group=harness');
	await expectCells(page, 'claude', BY_HARNESS.claude);
	await expectCells(page, 'cursor', BY_HARNESS.cursor);
	await page.goto(`/trends?metric=hook_events&group=harness&repo_id=${FILTER_REPO}`);
	await expectCells(page, 'cursor', BY_HARNESS_R1.cursor);
	await expect(page.getByTestId(`series-cursor-${DAYS.d2}`)).toHaveCount(0); // r2's day has no r1 point
	await page.reload();
	expect(new URL(page.url()).searchParams.getAll('repo_id')).toEqual([FILTER_REPO]);
	await expectCells(page, 'claude', BY_HARNESS_R1.claude);
	await expect(page.getByTestId(`series-cursor-${DAYS.d2}`)).toHaveCount(0); // r2's day has no r1 point
});

test('metric=conversations leaves only none and harness selectable for group', async ({ page }) => {
	await page.goto('/trends?group=repo_id');
	await expectCells(page, 'r1', { [DAYS.d5]: 2 });
	await page.getByTestId('trends-metric').selectOption('conversations');
	await expect(page).toHaveURL(/metric=conversations/);
	const opts = await page
		.getByTestId('trends-group')
		.locator('option')
		.evaluateAll((os) => os.map((o) => (o as HTMLOptionElement).value));
	expect(opts.sort()).toEqual(['harness', 'none']);
	await expect(page.getByTestId('trends-group')).toHaveValue('none');
	await expect(page.getByTestId('series-all-' + DAYS.d1)).toBeVisible();
	await expect(page.getByTestId('error-panel')).toHaveCount(0);
});
