import { expect, test, type Page } from '@playwright/test';
import { EXECUTION_COUNTS, EXECUTION_ROWS, FILTER_REPO } from './fixture';
import { expectSettled, trackRequests, useServe } from './helpers';

test.use({ timezoneId: 'UTC' });

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

const rows = (page: Page) => page.getByTestId('exec-row');
const rowTexts = (page: Page) => rows(page).allInnerTexts();

async function expectCounts(page: Page, want: Record<string, number>) {
	for (const s of ['complete', 'unreported', 'started'])
		await expect(page.getByTestId(`exec-count-${s}`), s).toHaveText(String(want[s]));
}

async function expectRows(page: Page, want: typeof EXECUTION_ROWS) {
	await expect(rows(page)).toHaveCount(want.length);
	const t = await rowTexts(page);
	want.forEach((w, i) => {
		for (const v of [w.repo_id, w.plan, w.conversation_id, w.brief_path, w.harness, w.shape]) expect(t[i]).toContain(v);
	});
}

test('counts and per-brief shapes equal the fixture', async ({ page }) => {
	await page.goto('/executions');
	await expectCounts(page, EXECUTION_COUNTS);
	await expectRows(page, EXECUTION_ROWS);
});

test('repo_id filters and survives reload', async ({ page }) => {
	const want = EXECUTION_ROWS.filter((r) => r.repo_id === FILTER_REPO);
	const counts = { complete: 0, unreported: 0, started: 0 } as Record<string, number>;
	for (const r of want) counts[r.shape]++;
	await page.goto(`/executions?repo_id=${FILTER_REPO}`);
	await expectCounts(page, counts);
	await expectRows(page, want);
	await page.reload();
	await expectCounts(page, counts);
	await expectRows(page, want);
});

test('a repo cell click adds a repo_id chip and narrows the rows', async ({ page }) => {
	await page.goto('/executions');
	await expectRows(page, EXECUTION_ROWS);
	// The r2 row (c2) is the second row; clicking its repo cell filters to r2.
	await rows(page).nth(1).getByTestId('exec-repo').click();
	await expect(page).toHaveURL(/repo_id=r2/);
	await expect(page.getByTestId('chip-repo_id-r2')).toHaveAttribute('data-mode', 'include');
	await expectRows(page, EXECUTION_ROWS.filter((r) => r.repo_id === 'r2'));
});

test('shift-clicking a repo cell adds an exclude chip', async ({ page }) => {
	await page.goto('/executions');
	await expectRows(page, EXECUTION_ROWS);
	await rows(page).nth(1).getByTestId('exec-repo').click({ modifiers: ['Shift'] });
	await expect(page).toHaveURL(/x\.repo_id=r2/);
	await expect(page.getByTestId('chip-repo_id-r2')).toHaveAttribute('data-mode', 'exclude');
	await expectRows(page, EXECUTION_ROWS.filter((r) => r.repo_id !== 'r2'));
});

test('the conversation link navigates to its timeline without filters', async ({ page }) => {
	await page.goto(`/executions?repo_id=${FILTER_REPO}`);
	const link = rows(page).first().getByTestId('exec-conversation');
	await expect(link).toHaveAttribute('href', '/conversation?id=c3');
	await link.click();
	await expect(page).toHaveURL(/\/conversation\?id=c3$/);
});

test('limit=1 paging walk equals the unpaged rows', async ({ page }) => {
	await page.goto('/executions');
	await expect(rows(page)).toHaveCount(EXECUTION_ROWS.length);
	const all = await rowTexts(page);
	await page.goto('/executions?limit=1');
	await expect(rows(page)).toHaveCount(1);
	const more = page.getByRole('button', { name: 'Load more' });
	for (let i = 2; i <= all.length; i++) {
		await more.click();
		await expect(rows(page)).toHaveCount(i);
	}
	await expect(more).toHaveCount(0);
	expect(await rowTexts(page)).toEqual(all);
});

test('a drill interaction renders within 1 s', async ({ page }) => {
	await page.goto('/executions');
	await expectRows(page, EXECUTION_ROWS);
	const start = Date.now();
	await rows(page).nth(1).getByTestId('exec-repo').click();
	await expect(page.getByTestId('chip-repo_id-r2')).toBeVisible();
	await expectRows(page, EXECUTION_ROWS.filter((r) => r.repo_id === 'r2'));
	expect(Date.now() - start).toBeLessThan(1000);
});

test('shows the execution sankey and its link controls', async ({ page }) => {
	await page.goto('/executions');
	await expect(page.getByTestId('exec-sankey')).toBeVisible();
	for (const id of ['exec-link-design-brief', 'exec-link-brief-commit', 'exec-link-brief-nocommit', 'exec-link-commit-report', 'exec-link-commit-noreport']) {
		await expect(page.getByTestId(id)).toBeVisible();
	}
});

test('clicking a sankey link filters the table and toggles off', async ({ page }) => {
	await page.goto('/executions');
	await expectRows(page, EXECUTION_ROWS);
	await page.getByTestId('exec-link-commit-report').click();
	await expect(page).toHaveURL(/shape=complete/);
	await expect(page.getByTestId('exec-link-commit-report')).toHaveAttribute('aria-pressed', 'true');
	await expectRows(page, EXECUTION_ROWS.filter((r) => r.shape === 'complete'));
	await page.reload();
	await expect(page).toHaveURL(/shape=complete/);
	await expectRows(page, EXECUTION_ROWS.filter((r) => r.shape === 'complete'));
	await page.getByTestId('exec-link-commit-report').click();
	await expect(page).not.toHaveURL(/shape=complete/);
	await expectRows(page, EXECUTION_ROWS);
});

test('shape=complete is sent to the API, counts stay window totals, rows match', async ({ page }) => {
	const seen = trackRequests(page, '/v1/analytics/executions');
	await page.goto('/executions?shape=complete');
	await expectCounts(page, EXECUTION_COUNTS);
	await expectRows(page, EXECUTION_ROWS.filter((r) => r.shape === 'complete'));
	const first = seen.urls().find((u) => !u.includes('cursor='));
	expect(first).toBeTruthy();
	expect(first!).toMatch(/shape=complete/);
});

test('shape=complete survives reload and limit=1 paging walk', async ({ page }) => {
	const want = EXECUTION_ROWS.filter((r) => r.shape === 'complete');
	await page.goto('/executions?shape=complete');
	await expectRows(page, want);
	const all = await rowTexts(page);
	await page.goto('/executions?shape=complete&limit=1');
	await expectCounts(page, EXECUTION_COUNTS);
	await expect(rows(page)).toHaveCount(1);
	await expect(page.getByRole('button', { name: 'Load more' })).toHaveCount(0);
	expect(await rowTexts(page)).toEqual(all);
	await page.reload();
	await expectRows(page, want);
});

test('stacked shape series chart is visible', async ({ page }) => {
	await page.goto('/executions');
	await expect(page.getByTestId('exec-shape-series')).toBeVisible();
	await expectSettled(page);
});

test('brushing the shape series narrows the window and refetches executions', async ({ page }) => {
	await page.goto('/executions');
	await expectSettled(page);
	const seen = trackRequests(page, '/v1/analytics/executions');
	seen.reset();
	const chart = page.getByTestId('exec-shape-series').locator('.echart');
	await chart.scrollIntoViewIfNeeded();
	const box = await chart.boundingBox();
	if (!box) throw new Error('no exec-shape-series chart box');
	const y = box.y + box.height * 0.75;
	await page.mouse.move(box.x + box.width * 0.2, y);
	await page.mouse.down();
	await page.mouse.move(box.x + box.width * 0.8, y, { steps: 8 });
	await page.mouse.up();
	await expect(page).toHaveURL(/[?&]from=/);
	const u = new URL(page.url());
	expect(u.searchParams.get('from')).toBeTruthy();
	expect(u.searchParams.get('to')).toBeTruthy();
	expect(u.searchParams.get('range')).toBeNull();
	await expect
		.poll(() => seen.urls().some((url) => new URL(url).searchParams.has('from')))
		.toBe(true);
});
