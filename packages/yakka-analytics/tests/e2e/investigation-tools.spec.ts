import { expect, test, type Page } from '@playwright/test';
import { SAVED_ANALYSIS_KEY } from '../../src/lib/saved-analysis';
import { expectSettled, useServe } from './helpers';

const QWEN = 'ollama-maxctx/qwen3-coder:30b-a3b-q4_K_M';

test.use({ timezoneId: 'UTC' });

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
	const { local } = (await import('./helpers')).serveState();
	await page.addInitScript((base) => {
		localStorage.setItem('yakka-analytics-base', base);
		localStorage.setItem('yakka-analytics-key', 'e2e-local-stay');
	}, local);
});

async function openUsageTool(page: Page) {
	await page.goto('/?ask=trend&measure=cost_usd&bucket=day&dim=model');
	await expectSettled(page);
	await expect(page.getByTestId('investigation-usage-tool')).toBeVisible();
}

test('usage tool shows unpriced model cost, not $0.00', async ({ page }) => {
	await openUsageTool(page);
	await expect(page.getByTestId('investigation-usage-table').locator('tr', { hasText: QWEN })).toBeVisible();
	await expect(page.getByTestId(`investigation-usage-${QWEN}-cost`)).toHaveText('unpriced');
	await expect(page.getByTestId(`investigation-usage-${QWEN}-cost`)).not.toHaveText('$0.00');
});

test('quality tool shows window scores beside baseline for design', async ({ page }) => {
	const cors = { 'access-control-allow-origin': '*' };
	const scores = {
		kind: 'design',
		checks: [{ name: 'd.alpha', n: 2, min: 0.1, p25: 0.2, median: 0.3, p75: 0.4, max: 0.5 }]
	};
	const base = { kind: 'design', checks: { 'd.alpha': { n: 10, p25: 0.15, median: 0.35, p75: 0.55 } } };
	await page.route('**/v1/analytics/scores*', (r) => r.fulfill({ json: scores, headers: cors }));
	await page.route('**/v1/baselines*', (r) => r.fulfill({ json: base, headers: cors }));
	await page.route('**/v1/analytics/score-series*', (r) =>
		r.fulfill({ json: { kind: 'design', bucket: 'day', checks: [] }, headers: cors })
	);
	await page.goto('/?ask=quality&kind=design&bucket=day&range=7d');
	await expect(page.getByTestId('investigation-quality-d.alpha-w-median')).toHaveText('0.3');
	await expect(page.getByTestId('investigation-quality-d.alpha-b-median')).toHaveText('0.35');
});

test('conversations list opens detail with in-window marker when window overlaps', async ({ page }) => {
	await page.goto('/?ask=conversations&range=7d');
	await expect(page.getByTestId('investigation-conv-c5-id')).toBeVisible();
	await page.getByTestId('investigation-conv-c5-id').click();
	await expect(page.getByTestId('investigation-timeline-row').first()).toBeVisible();
	await expect(page.getByTestId('investigation-timeline-row')).toHaveCount(3);
	await expect(page.getByTestId('investigation-timeline-in').first()).toBeVisible();
});

test('saved analysis round-trip restores ask and window', async ({ page }) => {
	await page.goto('/?ask=trend&measure=hook_events&bucket=day&range=7d');
	await expectSettled(page);
	await page.getByTestId('investigation-tool-saved').click();
	await page.getByTestId('investigation-saved-name').fill('E2E saved');
	await page.getByTestId('investigation-saved-save').click();
	await page.reload();
	await page.getByTestId('investigation-tool-saved').click();
	await page.getByTestId('investigation-saved-open-E2E saved').click();
	await expectSettled(page);
	const u = new URL(page.url());
	expect(u.searchParams.get('ask')).toBe('trend');
	expect(u.searchParams.get('measure')).toBe('hook_events');
	expect(u.searchParams.get('range')).toBe('7d');
	await page.evaluate((key) => localStorage.removeItem(key), SAVED_ANALYSIS_KEY);
});
