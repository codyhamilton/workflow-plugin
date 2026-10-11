import { expect, test } from '@playwright/test';
import { USAGE_ALL, USAGE_BY_MODEL } from './fixture';
import { clickBar, expectSettled, trackRequests, useServe } from './helpers';

const SONNET = 'anthropic/claude-sonnet-5-5';
const QWEN = 'ollama-maxctx/qwen3-coder:30b-a3b-q4_K_M';
const OPUS = 'claude-opus-5-5';

// `clickBar` reads bar N''s geometry from the chart box after showing the table. Open the table
// first and wait so its own toggle (which counts rows before Svelte flushes) does not race.
async function openTable(page: import('@playwright/test').Page, testid: string) {
	await page.getByTestId(`${testid}-table-toggle`).click();
	await expect(page.getByTestId(`${testid}-table`).locator('tbody tr').first()).toBeVisible();
}

// The priced Sonnet bar is first in `usage-cost-by-model` (clickBar's index is the bar band, 0-based).
const SONNET_BAR = 0;

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('usage table shows per-model calls, tokens and cost, and the unpriced banner', async ({ page }) => {
	await page.goto('/usage');
	const sonnet = USAGE_BY_MODEL[SONNET];
	await expect(page.getByTestId(`usage-${SONNET}-calls`)).toHaveText(String(sonnet.calls));
	await expect(page.getByTestId(`usage-${SONNET}-unpriced`)).toHaveText('0');
	await expect(page.getByTestId(`usage-${SONNET}-cost`)).toHaveText('$0.02');
	await expect(page.getByTestId(`usage-${QWEN}-cost`)).toHaveText('unpriced');
	await expect(page.getByTestId(`usage-${OPUS}-cost`)).toHaveText('unpriced');
	await expect(page.getByTestId('usage-unpriced-banner')).toHaveText(
		`${USAGE_ALL.unpriced_calls} of ${USAGE_ALL.model_calls} calls are unpriced`
	);
});

test('a window with only unpriced calls never shows $0', async ({ page }) => {
	await page.goto('/usage?harness=claude');
	await expect(page.getByTestId(`usage-${OPUS}-cost`)).toHaveText('unpriced');
	await expect(page.getByTestId('usage-unpriced-banner')).toHaveText('1 of 1 calls are unpriced');
	await expect(page.locator('body')).not.toContainText('$0');
});

test('?model= narrows the table to that model', async ({ page }) => {
	await page.goto(`/usage?model=${encodeURIComponent(SONNET)}`);
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await expect(page.getByTestId(`usage-row-${QWEN}`)).toHaveCount(0);
	await expect(page.getByTestId('usage-unpriced-banner')).toHaveCount(0);
});

test('clicking a cost bar filters by model; shift-click excludes', async ({ page }) => {
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await openTable(page, 'usage-cost-by-model');
	await clickBar(page, 'usage-cost-by-model', SONNET_BAR);
	await expect(page.getByTestId(`chip-model-${SONNET}`)).toBeVisible();
	await clickBar(page, 'usage-cost-by-model', SONNET_BAR, { shift: true });
	await expect(page.getByTestId(`chip-model-${SONNET}`)).toHaveAttribute('data-mode', 'exclude');
});

test('__other__ is inert', async ({ page }) => {
	await page.route('**/v1/analytics/query*', (route) => {
		const url = new URL(route.request().url());
		const dims = url.searchParams.getAll('dim');
		const rows = dims.includes('model')
			? [
					{ k: [SONNET], v: 0.02 },
					{ k: ['__other__'], v: 0.5 }
				]
			: [];
		return route.fulfill({
			json: { measure: url.searchParams.get('measure') ?? 'cost_usd', bucket: 'none', dims, rows },
			headers: { 'access-control-allow-origin': '*' }
		});
	});
	await page.goto('/usage');
	await expect(page.getByTestId('usage-row-__other__')).toBeVisible();
	await openTable(page, 'usage-cost-by-model');
	await clickBar(page, 'usage-cost-by-model', 2);
	await expect(page.locator('[data-testid^="chip-"]')).toHaveCount(0);
});

test('one load issues seven /analytics/query requests, none per model', async ({ page }) => {
	const reqs = trackRequests(page, /analytics\/query/);
	await page.goto('/usage');
	await expect(page.getByTestId(`usage-row-${SONNET}`)).toBeVisible();
	await expectSettled(page);
	expect(reqs.count()).toBe(7);
});

test('a preset change settles within 1 s', async ({ page }) => {
	await page.goto('/usage');
	await expectSettled(page);
	const t0 = Date.now();
	await page.getByTestId('preset-7d').click();
	await expectSettled(page);
	expect(Date.now() - t0).toBeLessThan(1000);
});
