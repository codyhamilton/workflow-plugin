<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { apiGet } from '$lib/api';
	import LineSeries from '$lib/charts/LineSeries.svelte';
	import { filterParams, parseFilter } from '$lib/filters';
	import { label } from '$lib/format';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Metric, Series } from '$lib/types';

	// DESIGN.md series contract: the only (metric, group) pairings the API accepts.
	const GROUPS: Record<Metric, string[]> = {
		hook_events: ['harness', 'repo_id', 'event', 'tool'],
		artifact_versions: ['harness', 'repo_id', 'kind', 'plan', 'source'],
		commits: ['harness', 'repo_id'],
		conversations: ['harness'],
		rejections: ['stage']
	};
	const METRICS = Object.keys(GROUPS) as Metric[];

	const metric = $derived.by(() => {
		const m = page.url.searchParams.get('metric') as Metric;
		return METRICS.includes(m) ? m : 'hook_events';
	});
	const bucket = $derived(page.url.searchParams.get('bucket') === 'week' ? 'week' : 'day');
	const groups = $derived(['none', ...GROUPS[metric]]);
	const group = $derived.by(() => {
		const g = page.url.searchParams.get('group') ?? 'none';
		return groups.includes(g) ? g : 'none';
	});

	let data = $state<Series | null>(null);

	$effect(() => {
		const q = filterParams(parseFilter(page.url.searchParams));
		q.set('metric', metric);
		q.set('bucket', bucket);
		if (group !== 'none') q.set('group', group);
		let live = true;
		apiGet<Series>('analytics/series', q).then(
			(s) => {
				if (!live) return;
				clearError();
				data = s;
			},
			(e) => {
				if (!live) return;
				data = null;
				setError(e);
			}
		);
		return () => (live = false);
	});

	function setParam(name: string, value: string) {
		const q = new URLSearchParams(page.url.searchParams);
		q.set(name, value);
		if (name === 'metric' && !['none', ...GROUPS[value as Metric]].includes(q.get('group') ?? 'none')) {
			q.set('group', 'none');
		}
		goto(`?${q}`, { keepFocus: true, noScroll: true });
	}

	const times = $derived([...new Set((data?.series ?? []).flatMap((s) => s.points.map((p) => p.t)))].sort());
	const cell = (s: Series['series'][number], t: string) => s.points.find((p) => p.t === t)?.n ?? 0;
	const id = (k: string) => (k === '' ? 'none' : k);
</script>

<h1>Trends</h1>
<div class="controls">
	<label>metric
		<select data-testid="trends-metric" value={metric} onchange={(e) => setParam('metric', e.currentTarget.value)}>
			{#each METRICS as m (m)}<option value={m}>{m}</option>{/each}
		</select>
	</label>
	<label>bucket
		<select data-testid="trends-bucket" value={bucket} onchange={(e) => setParam('bucket', e.currentTarget.value)}>
			<option value="day">day</option>
			<option value="week">week</option>
		</select>
	</label>
	<label>group
		<select data-testid="trends-group" value={group} onchange={(e) => setParam('group', e.currentTarget.value)}>
			{#each groups as g (g)}<option value={g}>{g}</option>{/each}
		</select>
	</label>
</div>

{#if data}
	<LineSeries series={data.series} bucket={data.bucket} />
	<table>
		<thead>
			<tr><th>{data.bucket}</th>{#each data.series as s (s.key)}<th>{label(s.key)}</th>{/each}</tr>
		</thead>
		<tbody>
			{#each times as t (t)}
				<tr>
					<th>{t}</th>
					{#each data.series as s (s.key)}
						<td data-testid="series-{id(s.key)}-{t}">{cell(s, t)}</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
{/if}

<style>
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
		border-bottom: 1px solid #eee;
		font-variant-numeric: tabular-nums;
	}
</style>
