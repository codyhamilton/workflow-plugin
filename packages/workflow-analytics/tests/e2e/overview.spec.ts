import { expect, test } from '@playwright/test';
import { FILTER_REPO, SUMMARY_ALL, SUMMARY_R1, USAGE_ALL } from './fixture';
import { expectSettled, trackRequests, useServe } from './helpers';

type P = import('@playwright/test').Page;
async function expectNumbers(page: P, want: Record<string, number>) {
	for (const [k, v] of Object.entries(want)) await expect(page.getByTestId(`summary-${k}`), k).toHaveText(String(v));
}
const TILES_ALL = {
	conversations: SUMMARY_ALL.conversations,
	hook_events: SUMMARY_ALL.hook_events,
	artifact_versions: SUMMARY_ALL.artifact_versions,
	distinct_content: SUMMARY_ALL.distinct_content,
	commits: SUMMARY_ALL.commits,
	model_calls: USAGE_ALL.model_calls,
	unpriced_calls: USAGE_ALL.unpriced_calls
};
const TILES_R1 = {
	conversations: SUMMARY_R1.conversations,
	hook_events: SUMMARY_R1.hook_events,
	artifact_versions: SUMMARY_R1.artifact_versions,
	distinct_content: SUMMARY_R1.distinct_content,
	commits: SUMMARY_R1.commits
};

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('overview shows the fixture numbers for the whole window', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, TILES_ALL);
	await expect(page.getByTestId('summary-tokens')).toHaveText(String(USAGE_ALL.tokens_in + USAGE_ALL.tokens_out));
	await expect(page.getByTestId('summary-tokens_cache_read')).toHaveText(String(USAGE_ALL.tokens_cache_read));
	await expect(page.getByTestId('summary-cost_usd')).toHaveText('$0.02, 2 unpriced');
});

test('repo_id in the URL filters, and survives a reload', async ({ page }) => {
	await page.goto(`/?repo_id=${FILTER_REPO}`);
	await expectNumbers(page, TILES_R1);
	await page.reload();
	expect(new URL(page.url()).searchParams.getAll('repo_id')).toEqual([FILTER_REPO]);
	await expectNumbers(page, TILES_R1);
});

test('choosing a repo in the filter bar changes the URL and the numbers', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, TILES_ALL);
	await page.getByTestId('filter-repo_id').selectOption(FILTER_REPO);
	await expect(page).toHaveURL(new RegExp(`repo_id=${FILTER_REPO}`));
	await expectNumbers(page, TILES_R1);
	await page.goBack();
	await expectNumbers(page, TILES_ALL);
});

test('no filter control offers an empty option', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, TILES_ALL);
	for (const name of ['repo_id', 'harness', 'kind', 'plan']) {
		const opts = await page.getByTestId(`filter-${name}`).locator('option').evaluateAll((os) =>
			os.map((o) => ({ value: (o as HTMLOptionElement).value, text: (o.textContent ?? '').trim() }))
		);
		expect(opts.length, name).toBeGreaterThan(0);
		for (const o of opts) {
			expect(o.value, name).not.toBe('');
			expect(o.text, name).not.toBe('');
		}
	}
});

test('cost tile never shows $0.00 while calls are unpriced', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByTestId('summary-cost_usd')).toHaveText('$0.02, 2 unpriced');
	await expect(page.getByTestId('summary-unpriced_calls')).toHaveText('2');
	await page.route('**/analytics/summary*', (route) =>
		route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ ...SUMMARY_ALL, ...USAGE_ALL, cost_usd: 0, model_calls: 3, unpriced_calls: 3 })
		})
	);
	await page.reload();
	await expect(page.getByTestId('summary-cost_usd')).toHaveText('unpriced');
	await expect(page.getByTestId('summary-unpriced_calls')).toHaveText('3');
});

test('heatmap reports ready', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByTestId('overview-heatmap')).toHaveAttribute('data-ready', 'true');
});

test('preset click settles within 1s', async ({ page }) => {
	await page.goto('/');
	await expectSettled(page);
	const start = Date.now();
	await page.getByTestId('preset-7d').click();
	await expectSettled(page);
	expect(Date.now() - start).toBeLessThan(1000);
});

test('one summary and at most ten query requests per load', async ({ page }) => {
	const summary = trackRequests(page, /analytics\/summary/);
	const query = trackRequests(page, /analytics\/query/);
	await page.goto('/');
	await expectNumbers(page, TILES_ALL);
	await expectSettled(page);
	await page.waitForTimeout(500);
	expect(summary.count()).toBeLessThanOrEqual(1);
	expect(query.count()).toBeLessThanOrEqual(10);
});
