import { expect, test, type Page } from '@playwright/test';
import { HOOKS_BY_EVENT, HOOKS_BY_HARNESS, HOOKS_BY_REPO, HOOKS_BY_TOOL } from './fixture';
import { expectSettled, trackRequests, useServe } from './helpers';

// Hand-counted per dimension, whole window. `hooks-tool` carries the empty tool key as "(none)".
const WANT: Record<string, Record<string, number>> = {
	'hooks-harness': HOOKS_BY_HARNESS,
	'hooks-repo_id': HOOKS_BY_REPO,
	'hooks-event': HOOKS_BY_EVENT,
	'hooks-tool': Object.fromEntries(
		Object.entries(HOOKS_BY_TOOL).map(([k, v]) => [k === '' ? '(none)' : k, v])
	)
};

/** Reveals the data table behind a chart and returns it. */
async function showTable(page: Page, testid: string) {
	const table = page.getByTestId(`${testid}-table`);
	if ((await table.count()) === 0) {
		await page.getByTestId(`${testid}-table-toggle`).click();
		await expect(table).toBeVisible();
	}
	return table;
}

/** The table view of a chart as a label → number map (order independent). */
async function counts(page: Page, testid: string): Promise<Record<string, number>> {
	const table = await showTable(page, testid);
	const rows = table.locator('tbody tr');
	const out: Record<string, number> = {};
	const n = await rows.count();
	for (let i = 0; i < n; i++) {
		const cells = await rows.nth(i).locator('td').allTextContents();
		out[cells[0].trim()] = Number(cells[1].trim());
	}
	return out;
}

// `clickBar` in helpers.ts toggles a BarChart to its table view to count rows, then clicks bar
// geometry over the table it just revealed — no chart, so nothing selects. This local version reads
// the row count from the table, restores the chart, then clicks the real ECharts bar.
const BAR_GRID = { left: 120, right: 24, top: 8, bottom: 24 };

async function clickHarnessBar(page: Page, index: number, opts: { shift?: boolean; frac?: number } = {}) {
	const testid = 'hooks-harness';
	const table = page.getByTestId(`${testid}-table`);
	if ((await table.count()) === 0) {
		await page.getByTestId(`${testid}-table-toggle`).click();
		await expect(table).toBeVisible();
	}
	const n = await table.locator('tbody tr').count();
	await page.getByTestId(`${testid}-table-toggle`).click(); // back to the chart
	await expect(page.getByTestId(testid).locator('.echart svg')).toBeVisible();
	const box = await page.getByTestId(testid).boundingBox();
	if (!box) throw new Error(`clickHarnessBar: no chart box for ${testid}`);
	const { left, right, top, bottom } = BAR_GRID;
	const frac = opts.frac ?? 0.5;
	const x = box.x + left + (box.width - left - right) * frac;
	const y = box.y + top + ((index + 0.5) * (box.height - top - bottom)) / n;
	if (opts.shift) await page.keyboard.down('Shift');
	await page.mouse.click(x, y);
	if (opts.shift) await page.keyboard.up('Shift');
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('every bar table equals the fixture count', async ({ page }) => {
	await page.goto('/hooks');
	await expectSettled(page);
	for (const [testid, want] of Object.entries(WANT)) {
		expect(await counts(page, testid), testid).toEqual(want);
	}
});

test('one load issues six /query requests', async ({ page }) => {
	const requests = trackRequests(page, /analytics\/query/);
	await page.goto('/hooks');
	await expectSettled(page);
	expect(requests.count()).toBe(6);
});

test('clicking a harness bar adds an include chip and narrows the other bars', async ({ page }) => {
	await page.goto('/hooks');
	await expectSettled(page);
	await clickHarnessBar(page, 0); // rows are key-ascending: claude, cursor, opencode
	await expect(page.getByTestId('chip-harness-claude')).toHaveAttribute('data-mode', 'include');
	await expect(page).toHaveURL(/harness=claude/);
	await expectSettled(page);
	expect(await counts(page, 'hooks-repo_id')).toEqual({ r1: 5 });
});

test('clicking the empty track of a short bar drills that row', async ({ page }) => {
	await page.goto('/hooks');
	await expectSettled(page);
	await clickHarnessBar(page, 1, { frac: 0.9 }); // cursor: 2 of a max 5, empty track to its right
	await expect(page.getByTestId('chip-harness-cursor')).toHaveAttribute('data-mode', 'include');
	await expect(page).toHaveURL(/harness=cursor/);
	await expectSettled(page);
});

test('shift-clicking a harness bar adds an exclude chip the bar then omits', async ({ page }) => {
	await page.goto('/hooks');
	await expectSettled(page);
	await clickHarnessBar(page, 2, { shift: true }); // opencode
	await expect(page.getByTestId('chip-harness-opencode')).toHaveAttribute('data-mode', 'exclude');
	await expect(page).toHaveURL(/x\.harness=opencode/);
	await expectSettled(page);
	const after = await counts(page, 'hooks-harness');
	expect(after).not.toHaveProperty('opencode');
	expect(after).toEqual({ claude: 5, cursor: 2 });
});

test('a bar click settles within one second', async ({ page }) => {
	await page.goto('/hooks');
	await expectSettled(page);
	const started = Date.now();
	await clickHarnessBar(page, 0);
	await expectSettled(page);
	expect(Date.now() - started).toBeLessThan(1000);
});

test('a treemap A leaf click adds a chip for each level of its path', async ({ page }) => {
	await page.goto('/hooks');
	await expectSettled(page);
	const table = await showTable(page, 'hooks-treemap-a');
	await table.locator('tbody tr').filter({ hasText: 'opencode / usage' }).click();
	await expect(page.getByTestId('chip-harness-opencode')).toHaveAttribute('data-mode', 'include');
	await expect(page.getByTestId('chip-norm_event-usage')).toHaveAttribute('data-mode', 'include');
});

test('a treemap __other__ leaf is inert', async ({ page }) => {
	await page.route('**/v1/analytics/query**', async (route) => {
		const dims = new URL(route.request().url()).searchParams.getAll('dim');
		if (dims[0] === 'harness' && dims[1] === 'norm_event') {
			await route.fulfill({
				json: {
					measure: 'hook_events',
					bucket: 'none',
					dims,
					rows: [
						{ k: ['claude', 'tool_pre'], v: 2 },
						{ k: ['__other__', 'other'], v: 1 }
					]
				}
			});
			return;
		}
		await route.continue();
	});
	await page.goto('/hooks');
	await expectSettled(page);
	const table = await showTable(page, 'hooks-treemap-a');
	await table.locator('tbody tr').filter({ hasText: '__other__' }).click();
	await expect(page.locator('[data-testid^="chip-"]')).toHaveCount(0);
	expect(new URL(page.url()).searchParams.getAll('harness')).toEqual([]);
	expect(new URL(page.url()).searchParams.getAll('norm_event')).toEqual([]);
});

test('the 7d preset chosen on Overview persists when navigating to Hooks', async ({ page }) => {
	await page.goto('/?range=7d');
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');
	await page.getByRole('link', { name: 'Hooks' }).click();
	await expect(page).toHaveURL(/\/hooks\?.*range=7d/);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');
});
