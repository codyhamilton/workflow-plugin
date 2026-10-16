import { describe, expect, it } from 'vitest';
import { binLabel, distributionOption } from './distribution';
import { DEFAULT_TOKENS } from './theme';
import type { DistributionBin } from '$lib/types';

const TOKENS = DEFAULT_TOKENS;

describe('binLabel', () => {
	it('labels cost zero and sub-cent buckets', () => {
		expect(binLabel('cost_usd', 0)).toBe('0');
		expect(binLabel('cost_usd', 0, 0.0001)).toBe('<$0.0001');
		expect(binLabel('cost_usd', 0.0001, 0.001)).toBe('$0.0001–$0.001');
		expect(binLabel('cost_usd', 100)).toBe('≥$100');
	});

	it('labels token power-of-two edges', () => {
		expect(binLabel('tokens_out', 0)).toBe('0');
		expect(binLabel('tokens_out', 1, 2)).toBe('1–2');
		expect(binLabel('tokens_out', 1024, 2048)).toBe('1024–2048');
		expect(binLabel('tokens_out', 1048576)).toBe('≥1048576');
	});
});

describe('distributionOption', () => {
	const costBins: DistributionBin[] = [
		{ lo: 0, n: 3 },
		{ lo: 0, hi: 0.0001, n: 1 },
		{ lo: 0.0001, hi: 0.001, n: 2 },
		{ lo: 100, n: 0 }
	];
	const tokenBins: DistributionBin[] = [
		{ lo: 0, n: 5 },
		{ lo: 1, hi: 2, n: 2 },
		{ lo: 1048576, n: 0 }
	];

	it('maps cost bins to category labels and bar counts', () => {
		const option = distributionOption({ measure: 'cost_usd', bins: costBins }, TOKENS);
		expect(option.xAxis.data).toEqual(['0', '<$0.0001', '$0.0001–$0.001', '≥$100']);
		expect(option.series[0].data).toEqual([3, 1, 2, 0]);
	});

	it('maps token bins to power-of-two edge labels', () => {
		const option = distributionOption({ measure: 'tokens_in', bins: tokenBins }, TOKENS);
		expect(option.xAxis.data).toEqual(['0', '1–2', '≥1048576']);
		expect(option.series[0].data).toEqual([5, 2, 0]);
	});
});
