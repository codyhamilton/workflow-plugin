import { expect, test, type Page } from '@playwright/test';
import { FILTER_REPO, HOOKS_BY_EVENT, HOOKS_BY_HARNESS, HOOKS_BY_TOOL } from './fixture';
import { useServe } from './helpers';

// repo r1 only: c1 (2 Bash PreToolUse, Stop), c3 (Stop), c4 (1 Bash PreToolUse; the secret one is rejected).
const R1 = {
	event: { PreToolUse: 3, Stop: 2 },
	tool: { Bash: 3, '': 2 },
	harness: { claude: 4, cursor: 1 }
};

async function expectGroups(page: Page, want: Record<string, Record<string, number>>) {
	for (const [g, rows] of Object.entries(want))
		for (const [k, n] of Object.entries(rows))
			await expect(page.getByTestId(`hooks-${g}-${k === '' ? 'none' : k}`), `${g} ${k}`).toHaveText(String(n));
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('event, tool (with the (none) row) and harness counts equal the fixture', async ({ page }) => {
	await page.goto('/hooks');
	await expectGroups(page, { event: HOOKS_BY_EVENT, tool: HOOKS_BY_TOOL, harness: HOOKS_BY_HARNESS });
	await expect(page.getByTestId('hooks-tool-row-none')).toContainText('(none)');
});

test('repo_id changes the counts and survives a reload', async ({ page }) => {
	await page.goto(`/hooks?repo_id=${FILTER_REPO}`);
	await expectGroups(page, R1);
	await expect(page.getByTestId('hooks-event-PostToolUse')).toHaveCount(0);
	await page.reload();
	await expectGroups(page, R1);
	await expect(page.getByTestId('hooks-tool-Read')).toHaveCount(0);
});
