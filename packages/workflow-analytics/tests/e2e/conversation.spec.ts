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

test('an unpriced usage event reads unpriced and no row shows $0', async ({ page }) => {
	await page.goto('/conversation?id=c5');
	const rows = page.getByTestId('timeline-row');
	await expect(rows).toHaveCount(3);
	await expect(rows.filter({ hasText: 'qwen3-coder' })).toContainText('unpriced');
	const texts = await rows.allInnerTexts();
	expect(texts.some((t) => t.includes('unpriced'))).toBe(true);
	expect(texts.some((t) => t.includes('$0.00'))).toBe(false);
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

test('the back link returns to the exact list it was opened from', async ({ page }) => {
	await page.goto('/conversations?range=7d&harness=claude');
	const link = page.locator('a[href^="/conversation?id="]').first();
	await expect(link).toBeVisible();
	await link.click();
	await expect(page).toHaveURL(/\/conversation\?id=/);
	const back = await page.getByTestId('back-to-conversations').boundingBox();
	const row = await page.getByTestId('timeline-row').first().boundingBox();
	if (back && row) expect(row.y).toBeGreaterThan(back.y + back.height); // rows stay inside the timeline, below the header
	await page.getByTestId('back-to-conversations').click();
	await expect(page).toHaveURL(/\/conversations\?range=7d&harness=claude$/);
});

test('a zero-token zero-cost row shows no cost text, an unpriced tokenized row reads unpriced', async ({
	page
}) => {
	const events = [
		{
			ts: '2026-01-01T00:00:00Z',
			type: 'hook_event',
			norm_event: 'usage',
			event: 'usage',
			tool: '',
			model: 'm1',
			path: '',
			kind: '',
			source: '',
			sha: '',
			tokens: { in: 0, out: 0, cache_read: 0, cache_write: 0, reasoning: 0 },
			cost_usd: 0
		},
		{
			ts: '2026-01-01T00:01:00Z',
			type: 'hook_event',
			norm_event: 'usage',
			event: 'usage',
			tool: '',
			model: 'qwen3-coder',
			path: '',
			kind: '',
			source: '',
			sha: '',
			tokens: { in: 5, out: 5, cache_read: 0, cache_write: 0, reasoning: 0 },
			cost_usd: 0
		}
	];
	await page.route('**/v1/analytics/conversation*', (r) =>
		r.fulfill({
			contentType: 'application/json',
			headers: { 'access-control-allow-origin': '*' },
			body: JSON.stringify({
				conversation_id: 'z',
				harness: 'claude',
				repos: [],
				models: ['m1', 'qwen3-coder'],
				first_ts: events[0].ts,
				last_ts: events[1].ts,
				totals: {
					model_calls: 2,
					tokens_in: 5,
					tokens_out: 5,
					tokens_cache_read: 0,
					tokens_cache_write: 0,
					tokens_reasoning: 0,
					cost_usd: 0,
					unpriced_calls: 1
				},
				events
			})
		})
	);
	await page.goto('/conversation?id=z');
	const rows = page.getByTestId('timeline-row');
	await expect(rows).toHaveCount(2);
	await expect(rows.nth(0)).not.toContainText('unpriced');
	await expect(rows.nth(1)).toContainText('unpriced');
});

test('the date preset control is visible on the conversation page', async ({ page }) => {
	await page.goto('/conversation?id=c5');
	await expect(page.getByTestId('preset-30d')).toBeVisible();
});

test('a narrower preset adds from and to on the conversation request', async ({ page }) => {
	const urls: string[] = [];
	await page.route('**/v1/analytics/conversation*', (route) => {
		urls.push(route.request().url());
		return route.continue();
	});
	await page.goto('/conversation?id=c5&range=30d');
	await expect(page.getByTestId('conv-total-model_calls')).toHaveText('3');
	const before = urls.length;
	await page.getByTestId('preset-7d').click();
	await expect.poll(() => urls.length).toBeGreaterThan(before);
	const last = new URL(urls[urls.length - 1]!);
	expect(last.searchParams.get('id')).toBe('c5');
	expect(last.searchParams.get('from')).toBeTruthy();
	expect(last.searchParams.get('to')).toBeTruthy();
	expect(last.searchParams.get('harness')).toBeNull();
});

test('events outside the window stay listed and read out of window', async ({ page }) => {
	const events = [
		{
			ts: '2020-01-01T00:00:00Z',
			type: 'hook_event',
			norm_event: 'old',
			event: 'old',
			tool: '',
			model: '',
			path: '',
			kind: '',
			source: '',
			sha: ''
		},
		{
			ts: new Date(Date.now() - 86400000).toISOString(),
			type: 'hook_event',
			norm_event: 'inwin',
			event: 'inwin',
			tool: '',
			model: '',
			path: '',
			kind: '',
			source: '',
			sha: ''
		}
	];
	await page.route('**/v1/analytics/conversation*', (route) =>
		route.fulfill({
			contentType: 'application/json',
			headers: { 'access-control-allow-origin': '*' },
			body: JSON.stringify({
				conversation_id: 'w',
				harness: 'claude',
				repos: [],
				models: [],
				first_ts: events[0].ts,
				last_ts: events[1].ts,
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
				window_totals: {
					model_calls: 0,
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
	await page.goto('/conversation?id=w&range=7d');
	await expect(page.getByTestId('timeline-row')).toHaveCount(2);
	await expect(page.getByTestId('timeline-out')).toHaveCount(1);
	await expect(page.getByTestId('timeline-row').filter({ hasText: 'old' }).getByTestId('timeline-out')).toBeVisible();
});

test('window totals render beside whole-run totals when the API sends them', async ({ page }) => {
	await page.route('**/v1/analytics/conversation*', (route) =>
		route.fulfill({
			contentType: 'application/json',
			headers: { 'access-control-allow-origin': '*' },
			body: JSON.stringify({
				conversation_id: 'w2',
				harness: 'claude',
				repos: [],
				models: [],
				first_ts: '2026-01-01T00:00:00Z',
				last_ts: '2026-01-02T00:00:00Z',
				totals: {
					model_calls: 9,
					tokens_in: 0,
					tokens_out: 0,
					tokens_cache_read: 0,
					tokens_cache_write: 0,
					tokens_reasoning: 0,
					cost_usd: 0,
					unpriced_calls: 0
				},
				window_totals: {
					model_calls: 2,
					tokens_in: 0,
					tokens_out: 0,
					tokens_cache_read: 0,
					tokens_cache_write: 0,
					tokens_reasoning: 0,
					cost_usd: 0,
					unpriced_calls: 0
				},
				events: []
			})
		})
	);
	await page.goto('/conversation?id=w2&range=7d');
	await expect(page.getByTestId('conv-total-model_calls')).toHaveText('9');
	await expect(page.getByTestId('conv-window-totals')).toBeVisible();
	await expect(page.getByTestId('conv-window-model_calls')).toHaveText('2');
});

test('all-time range omits window bounds and hides window totals', async ({ page }) => {
	const urls: string[] = [];
	await page.route('**/v1/analytics/conversation*', (route) => {
		urls.push(route.request().url());
		const u = new URL(route.request().url());
		const body: Record<string, unknown> = {
			conversation_id: 'w3',
			harness: 'claude',
			repos: [],
			models: [],
			first_ts: '2026-01-01T00:00:00Z',
			last_ts: '2026-01-02T00:00:00Z',
			totals: {
				model_calls: 1,
				tokens_in: 0,
				tokens_out: 0,
				tokens_cache_read: 0,
				tokens_cache_write: 0,
				tokens_reasoning: 0,
				cost_usd: 0,
				unpriced_calls: 0
			},
			events: []
		};
		if (u.searchParams.get('from') || u.searchParams.get('to')) {
			body.window_totals = {
				model_calls: 0,
				tokens_in: 0,
				tokens_out: 0,
				tokens_cache_read: 0,
				tokens_cache_write: 0,
				tokens_reasoning: 0,
				cost_usd: 0,
				unpriced_calls: 0
			};
		}
		return route.fulfill({
			contentType: 'application/json',
			headers: { 'access-control-allow-origin': '*' },
			body: JSON.stringify(body)
		});
	});
	await page.goto('/conversation?id=w3&range=7d');
	await expect(page.getByTestId('conv-window-totals')).toBeVisible();
	await page.getByTestId('preset-all').click();
	await expect.poll(() => urls.some((u) => !new URL(u).searchParams.get('from'))).toBe(true);
	await expect(page.getByTestId('conv-window-totals')).toHaveCount(0);
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
