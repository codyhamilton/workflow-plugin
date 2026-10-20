<script lang="ts">
	import type { AggregateRequest, QualityResult } from '$lib/aggregate';
	import { QualityChart, type QualityFrameData } from '$lib/analysis/chart-frame';
	import { bucketCount, pickBucket, type Bucket } from '$lib/buckets';

	const KINDS = ['design', 'brief', 'report'] as const;
	const ORDER: Bucket[] = ['day', 'week', 'month'];
	const CAP = 400;
	const W = ['n', 'min', 'p25', 'median', 'p75', 'max'] as const;
	const B = ['n', 'p25', 'median', 'p75'] as const;

	let {
		request,
		primary,
		commit,
		tz,
		onBrushEnd
	}: {
		request: AggregateRequest;
		primary: QualityResult | null;
		commit: (next: AggregateRequest, replace?: boolean) => void;
		tz: string;
		onBrushEnd: (detail: { from?: string; to?: string }) => void;
	} = $props();

	const ask = $derived(request.ask.ask === 'quality' ? request.ask : null);
	const scores = $derived(primary?.scores ?? null);
	const baselines = $derived(primary?.baseline ?? null);
	const scoreSeries = $derived(primary?.scoreSeries ?? null);

	const chartWindow = $derived.by(() => {
		const w = primary?.window;
		if (!w || !('from' in w) || !w.from || !w.to) return null;
		const from = new Date(w.from);
		const to = new Date(w.to);
		if (Number.isNaN(from.getTime()) || Number.isNaN(to.getTime())) return null;
		return { from, to };
	});

	const offered = $derived.by(() =>
		chartWindow
			? ORDER.filter((b) => bucketCount(b, chartWindow.from, chartWindow.to, tz) <= CAP)
			: ORDER
	);

	const bucket = $derived.by(() => {
		if (!ask) return 'day' as Bucket;
		if (chartWindow) {
			const want = ask.bucket;
			if (offered.includes(want)) return want;
			return pickBucket(chartWindow.from, chartWindow.to, tz, ORDER) ?? offered[0] ?? 'month';
		}
		return ask.bucket;
	});

	const bandChecks = $derived((scoreSeries?.checks ?? []).filter((c) => c.points.length > 0));
	const selectedCheck = $derived(bandChecks[0]?.name ?? scores?.checks[0]?.name ?? '');

	const qualityFrame = $derived.by((): QualityFrameData | null => {
		if (!ask || !chartWindow || !selectedCheck) return null;
		const check = scoreSeries?.checks.find((c) => c.name === selectedCheck);
		if (!check) return null;
		return {
			kind: ask.kind,
			bucket: ask.bucket,
			points: check.points.map((p) => ({
				t: p.t,
				n: p.n,
				p25: p.p25,
				median: p.median,
				p75: p.p75
			})),
			baselineMedian: baselines?.checks?.[selectedCheck]?.median,
			from: chartWindow.from,
			to: chartWindow.to,
			tz
		};
	});

	function setKind(kind: (typeof KINDS)[number]) {
		if (!ask) return;
		commit({ ...request, ask: { ...ask, kind } });
	}

	function setBucket(b: Bucket) {
		if (!ask) return;
		commit({ ...request, ask: { ...ask, bucket: b } });
	}
</script>

<div class="quality-tool" data-testid="investigation-quality-tool">
	<p class="kinds">
		Kind:
		{#each KINDS as k (k)}
			<button
				type="button"
				aria-pressed={ask?.kind === k}
				data-testid="investigation-quality-kind-{k}"
				onclick={() => setKind(k)}>{k}</button
			>
		{/each}
	</p>

	{#if chartWindow && bandChecks.length > 0}
		<label class="bucket">
			bucket
			<select
				data-testid="investigation-quality-bucket"
				value={bucket}
				onchange={(e) => setBucket((e.currentTarget as HTMLSelectElement).value as Bucket)}
			>
				{#each offered as b (b)}<option value={b}>{b}</option>{/each}
			</select>
		</label>
	{/if}

	{#if scores}
		<table data-testid="investigation-quality-table">
			<thead>
				<tr>
					<th rowspan="2">check</th>
					<th colspan={W.length}>window</th>
					<th colspan={B.length}>all-time baseline</th>
				</tr>
				<tr>
					{#each W as f (f)}<th>{f}</th>{/each}
					{#each B as f (f)}<th class="b">{f}</th>{/each}
				</tr>
			</thead>
			<tbody>
				{#each scores.checks as c (c.name)}
					{@const b = baselines?.checks?.[c.name]}
					<tr data-testid="investigation-quality-row">
						<th>{c.name}</th>
						{#each W as f (f)}<td data-testid="investigation-quality-{c.name}-w-{f}">{c[f]}</td>{/each}
						{#each B as f (f)}<td class="b" data-testid="investigation-quality-{c.name}-b-{f}">{b ? b[f] : ''}</td>{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}

	{#if qualityFrame}
		<section class="chart">
			<QualityChart
				data={qualityFrame}
				testid="investigation-quality-series"
				onbrushend={onBrushEnd}
			/>
		</section>
	{/if}
</div>

<style>
	button[aria-pressed='true'] {
		font-weight: bold;
	}
	.kinds {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
	}
	.bucket {
		display: block;
		margin: 0.5rem 0;
	}
	table {
		margin-top: 0.75rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		text-align: right;
		border-bottom: 1px solid var(--border);
		font-variant-numeric: tabular-nums;
	}
	th:first-child {
		text-align: left;
	}
	.b {
		background: var(--surface);
	}
	.chart {
		margin-top: 1rem;
	}
</style>
