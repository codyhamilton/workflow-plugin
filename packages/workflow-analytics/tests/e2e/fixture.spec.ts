import { expect, test } from '@playwright/test';
import { CONVERSATION_ROWS, EXECUTION_COUNTS, EXECUTION_ROWS, HOOK_EVENTS_BY_DAY } from './fixture';
import { serveState } from './helpers';

test('fixture expectations match the serve numbers', async () => {
	const b = serveState().local + '/v1/analytics/';
	const j = async (p: string) => (await fetch(b + p)).json() as Promise<any>;
	const ex = await j('executions');
	expect(ex.counts).toEqual(EXECUTION_COUNTS);
	expect(ex.rows.map((r: any) => ({ ...r, ts: Date.parse(r.ts) / 1000 }))).toEqual(EXECUTION_ROWS);
	const cv = await j('conversations');
	expect(cv.rows.map((r: any) => ({ ...r, first_ts: Date.parse(r.first_ts) / 1000, last_ts: Date.parse(r.last_ts) / 1000 }))).toEqual(CONVERSATION_ROWS);
	const s = await j('series?metric=hook_events&bucket=day');
	expect(Object.fromEntries(s.series[0].points.map((p: any) => [p.t, p.n]))).toEqual(HOOK_EVENTS_BY_DAY);
	for (const [g, want] of [['repo_id', { r1: 5, r2: 1 }], ['harness', { claude: 4, cursor: 2 }], ['event', { PreToolUse: 3, Stop: 2, PostToolUse: 1 }], ['tool', { Bash: 3, Read: 1, '': 2 }]] as const) {
		const r = await j(`series?metric=hook_events&bucket=day&group=${g}`);
		const got = Object.fromEntries(r.series.map((x: any) => [x.key, x.points.reduce((a: number, p: any) => a + p.n, 0)]));
		expect(got, g).toEqual(want);
	}
});
