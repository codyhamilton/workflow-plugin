import { expect, test, type Page } from '@playwright/test';
import { FILTER_REPO, SUMMARY_ALL, SUMMARY_R1 } from './fixture';
import { useServe } from './helpers';

const FIELDS = [
	'conversations',
	'hook_events',
	'artifact_versions',
	'commits',
	'by_kind-design',
	'by_kind-brief',
	'by_kind-report'
] as const;
const R1 = SUMMARY_R1;
// r2 is the window total minus r1 (every fixture fact belongs to r1 or r2).
const R2 = Object.fromEntries(FIELDS.map((f) => [f, SUMMARY_ALL[f] - R1[f]]));

async function expectRepo(page: Page, repo: string, want: Record<string, number>) {
	for (const f of FIELDS)
		await expect(page.getByTestId(`repo-${repo}-${f}`), `${repo} ${f}`).toHaveText(String(want[f]));
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('both fixture repos appear with their own counts', async ({ page }) => {
	await page.goto('/repos');
	await expectRepo(page, 'r1', R1);
	await expectRepo(page, 'r2', R2);
});

test('repo_id in the URL shows only that repo', async ({ page }) => {
	await page.goto(`/repos?repo_id=${FILTER_REPO}`);
	await expectRepo(page, FILTER_REPO, R1);
	await expect(page.getByTestId('repo-r2-conversations')).toHaveCount(0);
	await page.reload();
	await expectRepo(page, FILTER_REPO, R1);
	await expect(page.getByTestId('repo-r2-conversations')).toHaveCount(0);
});
