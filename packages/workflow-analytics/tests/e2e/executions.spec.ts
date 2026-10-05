import { expect, test, type Page } from '@playwright/test';
import { EXECUTION_COUNTS, EXECUTION_ROWS, FILTER_REPO } from './fixture';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

const rowTexts = (page: Page) => page.getByTestId('exec-row').allInnerTexts();

async function expectCounts(page: Page, want: Record<string, number>) {
	for (const s of ['complete', 'unreported', 'started'])
		await expect(page.getByTestId(`exec-count-${s}`), s).toHaveText(String(want[s]));
}

async function expectRows(page: Page, want: typeof EXECUTION_ROWS) {
	await expect(page.getByTestId('exec-row')).toHaveCount(want.length);
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
	const rows = EXECUTION_ROWS.filter((r) => r.repo_id === FILTER_REPO);
	const want = { complete: 0, unreported: 0, started: 0 } as Record<string, number>;
	for (const r of rows) want[r.shape]++;
	await page.goto(`/executions?repo_id=${FILTER_REPO}`);
	await expectCounts(page, want);
	await expectRows(page, rows);
	await page.reload();
	await expectCounts(page, want);
	await expectRows(page, rows);
});

test('limit=1 paging walk equals the unpaged rows', async ({ page }) => {
	await page.goto('/executions');
	await expect(page.getByTestId('exec-row')).toHaveCount(EXECUTION_ROWS.length);
	const all = await rowTexts(page);
	await page.goto('/executions?limit=1');
	await expect(page.getByTestId('exec-row')).toHaveCount(1);
	const more = page.getByRole('button', { name: 'Load more' });
	for (let i = 2; i <= all.length; i++) {
		await more.click();
		await expect(page.getByTestId('exec-row')).toHaveCount(i);
	}
	await expect(more).toHaveCount(0);
	expect(await rowTexts(page)).toEqual(all);
});
