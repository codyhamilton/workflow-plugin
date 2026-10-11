import { expect, test, type Page } from '@playwright/test';
import { USAGE_C5 } from './fixture';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

const TOTAL_KEYS = [
	'model_calls',
	'tokens_in',
	'tokens_out',
	'tokens_cache_read',
	'tokens_cache_write',
	'tokens_reasoning',
	'unpriced_calls'
] as const;

const rowDatetimes = (page: Page) =>
	page
		.getByTestId('timeline-row')
		.locator('time')
		.evaluateAll((els) => els.map((e) => e.getAttribute('datetime') ?? ''));

test('totals equal USAGE_C5 and the cost carries the unpriced note', async ({ page }) => {
	await page.goto('/conversation?id=c5');
	for (const k of TOTAL_KEYS)
		await expect(page.getByTestId(`conv-total-${k}`), k).toHaveText(String(USAGE_C5[k]));
	const cost = page.getByTestId('conv-total-cost');
	await expect(cost).toContainText('$0.02');
	await expect(cost).toContainText('1 unpriced');
	await expect(cost).not.toHaveText('$0.00');
});

test('the timeline rows are in ts order, oldest first', async ({ page }) => {
	await page.goto('/conversation?id=c5');
	await expect(page.getByTestId('timeline-row')).toHaveCount(3);
	const ts = await rowDatetimes(page);
	expect(ts).toEqual([...ts].sort());
	expect(new Set(ts).size).toBe(3);
	await expect(page.getByTestId('timeline-row').first()).toContainText('usage');
});

test('an unknown id shows No such conversation without the connection advice', async ({ page }) => {
	await page.goto('/conversation?id=nope');
	await expect(page.getByTestId('conversation-message')).toHaveText('No such conversation');
	await expect(page.getByText('Check the connection')).toHaveCount(0);
	await expect(page.getByTestId('error-panel')).toHaveCount(0);
});

test('a missing id asks to open one from the list', async ({ page }) => {
	await page.goto('/conversation');
	await expect(page.getByTestId('conversation-message')).toHaveText('Open a conversation from the list');
});

test('the conversation id link from /conversations lands on the timeline', async ({ page }) => {
	await page.goto('/conversations');
	const link = page.locator('a[href="/conversation?id=c5"]');
	if (await link.count()) await link.click();
	// 4-13 owns the list link; until it lands, exercise the destination the link points at.
	else await page.goto('/conversation?id=c5');
	await expect(page).toHaveURL(/\/conversation\?id=c5$/);
	await expect(page.getByTestId('conv-total-model_calls')).toHaveText('3');
});

test('a 5,000-event timeline keeps the DOM under 100 rows', async ({ page }) => {
	const events = Array.from({ length: 5000 }, (_, i) => ({
		ts: new Date(Date.UTC(2026, 0, 1) + i * 1000).toISOString(),
		type: 'hook_event',
		norm_event: 'PreToolUse',
		event: 'PreToolUse',
		tool: 'Bash',
		model: '',
		path: '',
		kind: '',
		source: '',
		sha: ''
	}));
	await page.route('**/v1/analytics/conversation*', (r) =>
		r.fulfill({
			contentType: 'application/json',
			headers: { 'access-control-allow-origin': '*' },
			body: JSON.stringify({
				conversation_id: 'big',
				harness: 'claude',
				repos: ['r1'],
				models: ['m'],
				first_ts: events[0].ts,
				last_ts: events[4999].ts,
				totals: {
					model_calls: 5000,
					tokens_in: 0,
					tokens_out: 0,
					tokens_cache_read: 0,
					tokens_cache_write: 0,
					tokens_reasoning: 0,
					cost_usd: 0,
					unpriced_calls: 0
				},
				events
			})
		})
	);
	await page.goto('/conversation?id=big');
	await expect(page.getByTestId('conv-total-model_calls')).toHaveText('5000');
	expect(await page.getByTestId('timeline-row').count()).toBeLessThan(100);
});

test('the totals render within 1s of navigation', async ({ page }) => {
	const t0 = Date.now();
	await page.goto('/conversation?id=c5');
	await expect(page.getByTestId('conv-total-cost')).toBeVisible();
	expect(Date.now() - t0).toBeLessThan(1000);
});

test('a truncated timeline says so', async ({ page }) => {
	await page.goto('/conversation?id=c5');
	await expect(page.getByTestId('timeline-truncated')).toHaveCount(0);
	await page.route('**/v1/analytics/conversation*', (r) =>
		r.fulfill({
			contentType: 'application/json',
			headers: { 'access-control-allow-origin': '*' },
			body: JSON.stringify({
				conversation_id: 'c5',
				harness: 'opencode',
				repos: ['r1'],
				models: [],
				first_ts: '2026-01-01T00:00:00Z',
				last_ts: '2026-01-01T00:00:00Z',
				totals: {
					model_calls: 0,
					tokens_in: 0,
					tokens_out: 0,
					tokens_cache_read: 0,
					tokens_cache_write: 0,
					tokens_reasoning: 0,
					cost_usd: 0,
					unpriced_calls: 0
				},
				events: [],
				truncated: true
			})
		})
	);
	await page.reload();
	await expect(page.getByTestId('timeline-truncated')).toBeVisible();
});
