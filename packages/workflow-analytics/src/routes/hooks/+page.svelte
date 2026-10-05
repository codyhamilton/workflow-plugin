<script lang="ts">
	import { page } from '$app/state';
	import { apiGet } from '$lib/api';
	import Bars from '$lib/charts/Bars.svelte';
	import { filterParams, parseFilter } from '$lib/filters';
	import { label } from '$lib/format';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Series } from '$lib/types';

	const GROUPS = ['event', 'tool', 'harness'] as const;
	type Row = { key: string; n: number };

	let data = $state<Record<(typeof GROUPS)[number], Row[]> | null>(null);

	$effect(() => {
		const base = filterParams(parseFilter(page.url.searchParams));
		let live = true;
		Promise.all(
			GROUPS.map(async (g) => {
				const q = new URLSearchParams(base);
				q.set('metric', 'hook_events');
				q.set('bucket', 'day');
				q.set('group', g);
				const s = await apiGet<Series>('analytics/series', q);
				const rows = s.series.map((x) => ({ key: x.key, n: x.points.reduce((a, p) => a + p.n, 0) }));
				return [g, rows.sort((a, b) => b.n - a.n || a.key.localeCompare(b.key))] as const;
			})
		).then(
			(r) => {
				if (!live) return;
				clearError();
				data = Object.fromEntries(r) as typeof data;
			},
			(e) => {
				if (!live) return;
				data = null;
				setError(e);
			}
		);
		return () => (live = false);
	});
</script>

<h1>Hooks</h1>
{#if data}
	{#each GROUPS as g (g)}
		<h2>{g}</h2>
		<Bars rows={data[g].map((r) => ({ name: label(r.key), n: r.n }))} keys={['n']} horizontal />
		<table>
			<tbody>
				{#each data[g] as r (r.key)}
					{@const k = r.key === '' ? 'none' : r.key}
					<tr data-testid="hooks-{g}-row-{k}">
						<th>{label(r.key)}</th>
						<td data-testid="hooks-{g}-{k}">{r.n}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/each}
{/if}

<style>
	table {
		margin-top: 0.5rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		border-bottom: 1px solid #eee;
		font-variant-numeric: tabular-nums;
	}
	th {
		text-align: left;
	}
	td {
		text-align: right;
	}
</style>
