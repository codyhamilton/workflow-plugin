import { expect, test, type Page } from '@playwright/test';
import { EXECUTION_COUNTS, EXECUTION_ROWS, FILTER_REPO } from './fixture';
import { useServe } from './helpers';

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
