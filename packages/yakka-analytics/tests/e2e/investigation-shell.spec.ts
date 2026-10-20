import { expect, test, type Page } from '@playwright/test';
import { expectSettled, trackRequests, useServe } from './helpers';

const BAR_GRID = { left: 120, right: 24, top: 8, bottom: 24 };

async function clickInvestigationBar(page: Page, index: number, opts: { shift?: boolean } = {}) {
	const n = await page.getByTestId('investigation-chart-keys').locator('li').count();
	const box = await page.getByTestId('investigation-chart').boundingBox();
	if (!box || n === 0) throw new Error('clickInvestigationBar: missing chart or keys');
	const { left, right, top, bottom } = BAR_GRID;
	const x = box.x + left + (box.width - left - right) / 2;
	const y = box.y + top + ((index + 0.5) * (box.height - top - bottom)) / n;
	if (opts.shift) await page.keyboard.down('Shift');
	await page.mouse.click(x, y);
	if (opts.shift) await page.keyboard.up('Shift');
}

test.use({ timezoneId: 'UTC' });

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
	const { local } = (await import('./helpers')).serveState();
	await page.addInitScript((base) => {
		localStorage.setItem('yakka-analytics-base', base);
		localStorage.setItem('yakka-analytics-key', 'e2e-local-stay');
	}, local);
});

test('landing control opens investigation with both measures visible', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByTestId('landing-trend-hook_events')).toBeVisible();
	await page.getByTestId('landing-open-investigation').click();
	await expect(page).toHaveURL(/\?.*ask=trend/);
	const u = new URL(page.url());
	expect(u.searchParams.get('measure')).toBe('hook_events');
	expect(u.searchParams.get('bucket')).toBe('day');
	await expectSettled(page);
	await expect(page.getByTestId('investigation-trend-hook_events')).toBeVisible();
	await expect(page.getByTestId('investigation-trend-cost_usd')).toBeVisible();
});

test('preset change refetches and updates the URL window', async ({ page }) => {
	const query = trackRequests(page, /analytics\/query/);
	await page.goto('/?ask=trend&measure=hook_events&bucket=day');
	await expectSettled(page);
	const beforeUrl = page.url();
	query.reset();
	const resp = page.waitForResponse((r) => r.url().includes('/v1/analytics/query'));
	await page.getByTestId('investigation-shell').getByTestId('preset-7d').click();
	await resp;
	await expect(page).not.toHaveURL(beforeUrl);
	const u = new URL(page.url());
	expect(u.searchParams.get('range') === '7d' || u.searchParams.has('from')).toBe(true);
	expect(query.count()).toBeGreaterThan(0);
});

test('drill on harness adds a filter; __other__ does not', async ({ page }) => {
	await page.goto('/?ask=breakdown&measure=hook_events&dim=harness');
	await expectSettled(page);
	await clickInvestigationBar(page, 0);
	await expect(page).toHaveURL(/harness=/);
	const u = new URL(page.url());
	expect(u.searchParams.getAll('harness').length).toBeGreaterThan(0);
});

test('shift-click exclude adds x.<dim> and conversation_id shows ignored notice', async ({ page }) => {
	await page.goto('/?ask=breakdown&measure=hook_events&dim=harness');
	await expectSettled(page);
	await clickInvestigationBar(page, 0, { shift: true });
	const u = new URL(page.url());
	expect(u.searchParams.getAll('x.harness').length).toBeGreaterThan(0);

	await page.goto('/?ask=breakdown&measure=hook_events&dim=conversation_id');
	await expectSettled(page);
	await clickInvestigationBar(page, 0, { shift: true });
	await expect(page.getByTestId('notice-ignored')).toBeVisible();
	await expect(page.getByTestId('notice-ignored')).toContainText('conversation_id');
});

test('pasted URL reproduces ask and filters', async ({ browser }) => {
	const ctx = await browser.newContext({ timezoneId: 'UTC' });
	const page = await ctx.newPage();
	await useServe(page, 'local');
	const { local } = (await import('./helpers')).serveState();
	await page.addInitScript((base) => {
		localStorage.setItem('yakka-analytics-base', base);
		localStorage.setItem('yakka-analytics-key', 'e2e-local-stay');
	}, local);

	const url =
		'/?ask=breakdown&measure=hook_events&dim=harness&range=7d&harness=cursor';
	await page.goto(url);
	await expectSettled(page);
	const copy = page.url();

	const page2 = await ctx.newPage();
	await useServe(page2, 'local');
	await page2.addInitScript((base) => {
		localStorage.setItem('yakka-analytics-base', base);
		localStorage.setItem('yakka-analytics-key', 'e2e-local-stay');
	}, local);
	await page2.goto(copy);
	await expectSettled(page2);
	const a = new URL(copy);
	const b = new URL(page2.url());
	expect(b.searchParams.get('ask')).toBe(a.searchParams.get('ask'));
	expect(b.searchParams.get('measure')).toBe(a.searchParams.get('measure'));
	expect(b.searchParams.get('dim')).toBe(a.searchParams.get('dim'));
	expect(b.searchParams.get('range')).toBe(a.searchParams.get('range'));
	expect(b.searchParams.getAll('harness').sort()).toEqual(a.searchParams.getAll('harness').sort());
	await ctx.close();
});
