<script lang="ts">
	import { page } from '$app/state';
	import BoxChart from '$lib/charts/BoxChart.svelte';
	import ScoreBandChart from '$lib/charts/ScoreBandChart.svelte';
	import type { BoxRow } from '$lib/charts/box';
	import { bucketCount, pickBucket, type Bucket } from '$lib/buckets';
	import { KINDS, type Kind } from '$lib/filters';
	import { resolveWindow, scoreSeriesParams, scoresParams } from '$lib/params';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Baselines, ScoreSeries, Scores } from '$lib/types';
	import { view } from '$lib/view.svelte';

	const W = ['n', 'min', 'p25', 'median', 'p75', 'max'] as const;
	const B = ['n', 'p25', 'median', 'p75'] as const;
	const ORDER: Bucket[] = ['day', 'week', 'month'];
	const CAP = 400;

	let scores = $state<Scores | null>(null);
	let baselines = $state<Baselines | null>(null);
	let scoreSeries = $state<ScoreSeries | null>(null);

	const include = $derived(view.state.include);
	const kind = $derived<Kind>((include.kind?.[0] as Kind | undefined) ?? 'design');

	const window = $derived.by(() => {
		const now = new Date();
		const w = resolveWindow(view.state, now, view.tz, 'rest');
		return w.from && w.to ? { from: w.from, to: w.to } : null;
	});

	const offered = $derived.by(() =>
		window ? ORDER.filter((b) => bucketCount(b, window.from, window.to, view.tz) <= CAP) : ORDER
	);

	const bucket = $derived.by(() => {
		if (!window) return 'day' as Bucket;
		const want = page.url.searchParams.get('bucket') as Bucket | null;
		if (want && offered.includes(want)) return want;
		return pickBucket(window.from, window.to, view.tz, ORDER) ?? offered[0] ?? 'month';
	});

	const distRows = $derived<BoxRow[]>(
		(scores?.checks ?? [])
			.filter((c) => c.n > 0)
			.map((c) => ({
				name: c.name,
				min: c.min,
				p25: c.p25,
				median: c.median,
				p75: c.p75,
				max: c.max,
				marker: baselines?.checks?.[c.name]?.median
			}))
	);

	const bandChecks = $derived(
		(scoreSeries?.checks ?? []).filter((c) => c.points.length > 0)
	);

	function setBucket(v: string) {
		view.setParam('bucket', v);
	}

	$effect(() => {
		void view.state;
		const base = view.paramsFor('rest');
		const k = kind;
		const b = bucket;
		if (!base) {
			scores = null;
			baselines = null;
			scoreSeries = null;
			return;
		}
		let live = true;
		Promise.all([
			getJSON<Scores>('quality-scores', 'analytics/scores', scoresParams(base, k)),
			getJSON<Baselines>('quality-baselines', 'baselines', new URLSearchParams({ kind: k })),
			getJSON<ScoreSeries>(
				'quality-score-series',
				'analytics/score-series',
				scoreSeriesParams(base, k, b)
			)
		]).then(
			([s, bl, ss]) => {
				if (!live) return;
				clearError();
				scores = s;
				baselines = bl;
				scoreSeries = ss;
			},
			(e) => {
				if (!live || e instanceof Superseded) return;
				scores = null;
				baselines = null;
				scoreSeries = null;
				setError(e);
			}
		);
		return () => {
			live = false;
		};
	});
</script>

<h1>Quality</h1>
<p class="kinds">
	Kind:
	{#each KINDS as k (k)}
		<button type="button" aria-pressed={k === kind} data-testid="quality-kind-{k}" onclick={() => view.setInclude('kind', [k])}
			>{k}</button
		>
	{/each}
</p>
{#if (include.kind?.length ?? 0) > 1}
	<p data-testid="quality-kind-note">The URL names several kinds; showing {kind}.</p>
{/if}
{#if window && bandChecks.length > 0}
	<div class="controls">
		<label
			>bucket
			<select data-testid="quality-bucket" value={bucket} onchange={(e) => setBucket(e.currentTarget.value)}>
				{#each offered as b (b)}<option value={b}>{b}</option>{/each}
			</select>
		</label>
	</div>
	{#each bandChecks as check (check.name)}
		<ScoreBandChart
			testid="quality-band-{check.name}"
			title={check.name}
			points={check.points}
			{bucket}
			from={window.from}
			to={window.to}
			tz={view.tz}
			baselineMedian={baselines?.checks?.[check.name]?.median}
			onbrush={({ from, to }) => view.setWindow(from, to)}
		/>
	{/each}
{:else if window}
	<div class="controls">
		<label
			>bucket
			<select data-testid="quality-bucket" value={bucket} onchange={(e) => setBucket(e.currentTarget.value)}>
				{#each offered as b (b)}<option value={b}>{b}</option>{/each}
			</select>
		</label>
	</div>
{/if}
{#if scores}
	<BoxChart testid="quality-dist" rows={distRows} />
	<table>
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
				<tr data-testid="q-row">
					<th>{c.name}</th>
					{#each W as f (f)}<td data-testid="q-{c.name}-w-{f}">{c[f]}</td>{/each}
					{#each B as f (f)}<td class="b" data-testid="q-{c.name}-b-{f}">{b ? b[f] : ''}</td>{/each}
				</tr>
			{/each}
		</tbody>
	</table>
{/if}

<style>
	button[aria-pressed='true'] {
		font-weight: bold;
	}
	.controls {
		display: flex;
		gap: 1rem;
		margin-bottom: 1rem;
	}
	table {
		margin-top: 1rem;
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
</style>
