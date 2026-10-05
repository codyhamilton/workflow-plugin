import { expect, test, type Page } from '@playwright/test';
import { CONVERSATION_ROWS, FILTER_REPO } from './fixture';
import { useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

const rowTexts = (page: Page) => page.getByTestId('conv-row').allInnerTexts();

async function expectRows(page: Page, want: typeof CONVERSATION_ROWS) {
	await expect(page.getByTestId('conv-row')).toHaveCount(want.length);
	const t = await rowTexts(page);
	want.forEach((w, i) => {
		expect(t[i]).toContain(w.conversation_id);
		expect(t[i]).toContain(w.harness);
	});
	for (const w of want)
		for (const f of ['hook_events', 'artifact_versions', 'commits'] as const)
			await expect(page.getByTestId(`conv-${w.conversation_id}-${f}`), `${w.conversation_id} ${f}`).toHaveText(String(w[f]));
}

test('one row per fixture conversation, last_ts descending, with counts', async ({ page }) => {
	await page.goto('/conversations');
	await expectRows(page, CONVERSATION_ROWS);
});

test('repo_id filters', async ({ page }) => {
	await page.goto(`/conversations?repo_id=${FILTER_REPO}`);
	const want = CONVERSATION_ROWS.filter((r) => r.repos.includes(FILTER_REPO));
	await expect(page.getByTestId('conv-row')).toHaveCount(want.length);
	for (const w of want) await expect(page.getByTestId(`conv-${w.conversation_id}-commits`)).toBeVisible();
	await expect(page.getByTestId('conv-c2-commits')).toHaveCount(0);
});

test('limit=1 paging walk equals the unpaged rows', async ({ page }) => {
	await page.goto('/conversations');
	await expect(page.getByTestId('conv-row')).toHaveCount(CONVERSATION_ROWS.length);
	const all = await rowTexts(page);
	await page.goto('/conversations?limit=1');
	await expect(page.getByTestId('conv-row')).toHaveCount(1);
	const more = page.getByRole('button', { name: 'Load more' });
	for (let i = 2; i <= all.length; i++) {
		await more.click();
		await expect(page.getByTestId('conv-row')).toHaveCount(i);
	}
	await expect(more).toHaveCount(0);
	expect(await rowTexts(page)).toEqual(all);
});
