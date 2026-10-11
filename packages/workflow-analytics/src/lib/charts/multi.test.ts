import { describe, expect, it } from 'vitest';
import { render } from 'svelte/server';
import SmallMultiples from './SmallMultiples.svelte';
import {
	groupedBarOption,
	groupedBarProps,
	multiplesLayout,
	orderKeys,
	panelOption
} from './multi';
import { DEFAULT_TOKENS } from './theme';
import type { QueryResponse } from '../types';

const TOKENS = DEFAULT_TOKENS;

function resp(partial: Partial<QueryResponse>): QueryResponse {
	return { measure: 'm', bucket: 'none', dims: [], rows: [], ...partial };
}

describe('groupedBarOption', () => {
	const props = {
		categories: [{ key: 'a', label: 'A', clickable: true }],
		series: [{ name: 's', values: [1] }]
	};

	it('renders grouped bars with no stack', () => {
		const option = groupedBarOption(props, TOKENS);
		expect(option.series[0].type).toBe('bar');
		expect(option.series[0].stack).toBeUndefined();
	});

	it('renders stacked bars on one total stack', () => {
		const option = groupedBarOption({ ...props, stacked: true }, TOKENS);
		expect(option.series[0].stack).toBe('total');
	});
});

describe('multiplesLayout', () => {
	it('sets the panel count to the distinct second-dimension keys', () => {
		const r = resp({
			dims: ['model', 'repo'],
			bucket: 'day',
			rows: [
				{ t: '2024-01-01', k: ['a', 'r1'], v: 1 },
				{ t: '2024-01-01', k: ['a', 'r2'], v: 2 },
				{ t: '2024-01-02', k: ['b', 'r1'], v: 3 }
			]
		});
		expect(multiplesLayout(r).panels).toHaveLength(2);
	});

	it('shares one y max across panels', () => {
		const r = resp({
			dims: ['model', 'repo'],
			bucket: 'day',
			rows: [
				{ t: '2024-01-01', k: ['a', 'r1'], v: 1 },
				{ t: '2024-01-01', k: ['a', 'r2'], v: 7 }
			]
		});
		const layout = multiplesLayout(r);
		expect(layout.yMax).toBe(7);
		const option = panelOption(layout.panels[0], layout.yMax, 'day', TOKENS);
		expect((option.yAxis as { max?: number }).max).toBe(7);
	});

	it('yields no panels for an empty response', () => {
		const layout = multiplesLayout(resp({ dims: ['model', 'repo'], bucket: 'day' }));
		expect(layout.panels).toEqual([]);
		expect(layout.yMax).toBe(0);
	});
});

describe('groupedBarProps', () => {
	it('orders weekday keys 0..6 and labels them Sun..Sat', () => {
		const r = resp({
			dims: ['weekday'],
			rows: ['3', '1', '0', '6', '5', '4', '2'].map((k) => ({ k: [k], v: 1 }))
		});
		const p = groupedBarProps(r);
		expect(p.categories.map((c) => c.key)).toEqual(['0', '1', '2', '3', '4', '5', '6']);
		expect(p.categories.map((c) => c.label)).toEqual([
			'Sun',
			'Mon',
			'Tue',
			'Wed',
			'Thu',
			'Fri',
			'Sat'
		]);
	});

	it('keeps the __other__ category last and unclickable', () => {
		const r = resp({
			dims: ['model'],
			rows: [{ k: ['__other__'], v: 1 }, { k: ['zeta'], v: 2 }, { k: ['alpha'], v: 3 }]
		});
		const p = groupedBarProps(r);
		expect(p.categories.map((c) => c.key)).toEqual(['alpha', 'zeta', '__other__']);
		expect(p.categories[2].clickable).toBe(false);
		expect(orderKeys('model', ['__other__', 'b', 'a'])).toEqual(['a', 'b', '__other__']);
	});
});

describe('SmallMultiples data-ready', () => {
	it('is ready on the root when there are zero panels', () => {
		const { body } = render(SmallMultiples, {
			props: { testid: 'x', panels: [], yMax: 0, bucket: 'day' }
		});
		expect(body).toContain('data-ready="true"');
	});

	it('is not ready before its child charts mount', () => {
		const panels = [
			{
				key: 'a',
				title: 'A',
				series: [{ name: 's', points: [{ t: '2024-01-01', v: 1 }] }]
			}
		];
		const { body } = render(SmallMultiples, {
			props: { testid: 'x', panels, yMax: 1, bucket: 'day' }
		});
		expect(body).toContain('data-ready="false"');
	});
});
