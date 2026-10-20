import { readFileSync } from 'node:fs';
import { expect, type Page } from '@playwright/test';

export interface ServeState {
	local: string; // base URL of the local-mode serve (no auth)
	keyed: string; // base URL of the keyed serve (cross-origin from the preview, bearer required)
	key: string;
}

export function serveState(): ServeState {
	return JSON.parse(readFileSync(process.env.E2E_STATE!, 'utf8'));
}

/** Point the site at one of the e2e serves before any page script runs. */
export async function useServe(page: Page, which: 'local' | 'keyed') {
	const s = serveState();
	const base = which === 'local' ? s.local : s.keyed;
	const key = which === 'keyed' ? s.key : null;
	await page.addInitScript(
		([b, k, localStay]) => {
			localStorage.setItem('yakka-analytics-base', b as string);
			if (k) localStorage.setItem('yakka-analytics-key', k as string);
			if (localStay) localStorage.setItem('yakka-analytics-key', localStay as string);
		},
		which === 'local' ? [base, key, 'e2e-local-stay'] : [base, key, null]
	);
}

/** Counts requests whose URL contains the string pattern or matches the RegExp. */
export function trackRequests(page: Page, pattern: string | RegExp): { count(): number; urls(): string[]; reset(): void } {
	const seen: string[] = [];
	page.on('request', (r) => {
		const u = r.url();
		const hit = typeof pattern === 'string' ? u.includes(pattern) : pattern.test(u);
		if (hit) seen.push(u);
	});
	return {
		count: () => seen.length,
		urls: () => seen.slice(),
		reset: () => {
			seen.length = 0;
		}
	};
}

/** Waits until every chart reports `data-ready="true"` and none report `"false"`. */
export async function expectSettled(page: Page): Promise<void> {
	await expect(page.locator('[data-ready="false"]')).toHaveCount(0);
	await expect(page.locator('[data-ready="true"]').first()).toBeVisible();
}

/** BarChart geometry (4-04): fixed px grid, categories top to bottom in data order. */
const BAR_GRID = { left: 120, right: 24, top: 8, bottom: 24 };

/**
 * Clicks the centre of bar `index` of a horizontal `BarChart` (4-04's geometry). N comes from the
 * number of rows in `<testid>-table`. `BarChart` renders the chart and its table as alternatives,
 * so read the count from the table, restore the chart, then click the real ECharts bar.
 */
export async function clickBar(page: Page, testid: string, index: number, opts: { shift?: boolean } = {}): Promise<void> {
	const table = page.getByTestId(`${testid}-table`);
	if ((await table.count()) === 0) {
		await page.getByTestId(`${testid}-table-toggle`).click();
		await expect(table).toBeVisible();
	}
	const n = await table.locator('tbody tr').count();
	await page.getByTestId(`${testid}-table-toggle`).click(); // back to the chart
	await expect(page.getByTestId(testid).locator('.echart svg')).toBeVisible();
	const box = await page.getByTestId(testid).boundingBox();
	if (!box || n === 0) throw new Error(`clickBar: no chart box or table rows for ${testid}`);
	const { left, right, top, bottom } = BAR_GRID;
	const x = box.x + left + (box.width - left - right) / 2;
	const y = box.y + top + ((index + 0.5) * (box.height - top - bottom)) / n;
	if (opts.shift) await page.keyboard.down('Shift');
	await page.mouse.click(x, y);
	if (opts.shift) await page.keyboard.up('Shift');
}

/**
 * Drags a horizontal brush across a `TimeChart` from `fromFrac` to `toFrac` of its box width at mid
 * height. Written against 4-04's contract; unexercised until it lands.
 */
export async function brush(page: Page, testid: string, fromFrac: number, toFrac: number): Promise<void> {
	const box = await page.getByTestId(testid).boundingBox();
	if (!box) throw new Error(`brush: no chart box for ${testid}`);
	const y = box.y + box.height / 2;
	await page.mouse.move(box.x + box.width * fromFrac, y);
	await page.mouse.down();
	await page.mouse.move(box.x + box.width * toFrac, y, { steps: 5 });
	await page.mouse.up();
}
