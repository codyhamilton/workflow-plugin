import { describe, expect, it } from 'vitest';
import { barOption, heatmapOption, timeOption, treemapOption } from './options';
import { DEFAULT_TOKENS } from './theme';

const TOKENS = DEFAULT_TOKENS;

describe('barOption', () => {
	it('orders categories first row first and sets the fixed grid', () => {
		const option = barOption(
			{
				rows: [
					{ key: 'a', label: 'A', value: 1 },
					{ key: 'b', value: 2 }
				]
			},
			TOKENS
		);
		expect(option.grid).toMatchObject({ left: 120, right: 24, top: 8, bottom: 24 });
		expect(option.yAxis.inverse).toBe(true);
		expect(option.yAxis.data).toEqual(['A', 'b']);
		expect(option.series[0].type).toBe('bar');
		expect(option.series[0].data).toHaveLength(2);
	});

	it('marks the __other__ row unclickable and leaves the rest clickable', () => {
		const option = barOption(
			{
				rows: [
					{ key: 'a', value: 1 },
					{ key: '__other__', value: 9 }
				]
			},
			TOKENS
		);
		const data = option.series[0].data;
		expect(data[0].clickable).toBe(true);
		expect(data[1].clickable).toBe(false);
	});

	it('marks nothing clickable when selectable is false', () => {
		const option = barOption({ rows: [{ key: 'a', value: 1 }], selectable: false }, TOKENS);
		expect(option.series[0].data[0].clickable).toBe(false);
	});
});

describe('timeOption', () => {
	it('registers the brush with lineX and activates it on the x axis', () => {
		const option = timeOption(
			{ series: [{ name: 'x', points: [{ t: '2024-01-01', v: 1 }] }], bucket: 'day' },
			TOKENS
		);
		expect(option.brush.brushType).toBe('lineX');
		expect(option.xAxis.type).toBe('time');
		expect(option.series[0].type).toBe('line');
	});

	it('uses stacked bars when stacked', () => {
		const option = timeOption(
			{ series: [{ name: 'x', points: [{ t: '2024-01-01', v: 1 }] }], bucket: 'day', stacked: true },
			TOKENS
		);
		expect(option.series[0].type).toBe('bar');
		expect(option.series[0].stack).toBeTruthy();
	});
});

describe('heatmapOption', () => {
	it('builds a 24 x 7 grid with a visualMap range from the data', () => {
		const xLabels = Array.from({ length: 24 }, (_, i) => String(i));
		const yLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
		const option = heatmapOption(
			{ cells: [{ x: 0, y: 0, v: 5 }, { x: 23, y: 6, v: 9 }], xLabels, yLabels },
			TOKENS
		);
		expect(option.xAxis.data).toHaveLength(24);
		expect(option.yAxis.data).toHaveLength(7);
		expect(option.series[0].type).toBe('heatmap');
		expect(option.series[0].data).toEqual([[0, 0, 5], [23, 6, 9]]);
		expect(option.visualMap.min).toBe(5);
		expect(option.visualMap.max).toBe(9);
	});

	it('does not throw on empty data', () => {
		const option = heatmapOption({ cells: [], xLabels: [], yLabels: [] }, TOKENS);
		expect(option.series[0].data).toEqual([]);
	});
});

describe('treemapOption', () => {
	it('maps the root to a treemap series', () => {
		const option = treemapOption(
			{ root: [{ name: 'a', value: 1, children: [{ name: 'b', value: 1 }] }] },
			TOKENS
		);
		expect(option.series[0].type).toBe('treemap');
		expect(option.series[0].data[0].name).toBe('a');
		expect(option.series[0].data[0].children[0].name).toBe('b');
	});
});
